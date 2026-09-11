"""
Extract individual band GeoJSONs from the Abschichtung raster.

Welche Bänder Layer werden, entscheidet das Bandmanifest — dieselbe Auswahl wie
in scripts/generate_bands_config.py, damit Kacheln und `bands.ts` nicht
auseinanderlaufen können. Jedes Band wird polygonisiert nach
geodata/<bandname>.geojson geschrieben, mit einer Eigenschaft: {"band_id": N},
wobei N der Bandindex aus dem Manifest ist.

Der Dateiname ist der Bandname aus dem Manifest und zugleich der Layername in
den Vektorkacheln (`tippecanoe -L <name>:…`) und das `source-layer` in MapLibre.

Uses Resampling.max so thin buffers (roads) don't disappear at 20×.
"""

import json
import os
import sys

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.features import rasterize, shapes
from rasterio.warp import transform_geom
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
import shapely

SRC_CANDIDATES = [
    "scripts/raster/abschichtung.tif",
    "scripts/raster/osm_wka_distance_zones_widmung.tif",
]
SRC = next((p for p in SRC_CANDIDATES if os.path.exists(p)), SRC_CANDIDATES[-1])
AUSTRIA_OUTLINE = "geodata/austria_outline.geojson"
OUT_DIR = "geodata"

# Die Layerauswahl kommt aus dem Manifest — siehe generate_bands_config.py.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_bands_config import MANIFEST, select_bands  # noqa: E402

# Simplification tolerance — keep fine; Tippecanoe will handle LOD simplification
SIMPLIFY_TOL = 0.00005  # degrees (~5 m at Austrian latitudes) — fine since source is 25 m

DOWNSAMPLE = 1  # factor → 1 × 25 m = full native resolution, matches possible_zones.geojson


def max_pool_2d(arr: np.ndarray, factor: int) -> np.ndarray:
    """Downsample a 2-D boolean/uint8 array by taking the max in each (factor×factor) block."""
    h, w = arr.shape
    # Trim so dimensions are divisible by factor
    h2 = (h // factor) * factor
    w2 = (w // factor) * factor
    trimmed = arr[:h2, :w2]
    return trimmed.reshape(h // factor, factor, w // factor, factor).max(axis=(1, 3))


def load_austria_mask(src_ds) -> np.ndarray:
    """Rasterize geodata/austria_outline.geojson to the source grid.

    Several source bands (esp. geography_wind_too_low) are not clipped to
    Austria's real border — they cover the whole rectangular grid extent,
    which would otherwise bleed into neighbouring countries in the detail
    bands too (visible e.g. as a huge "wind too low" blob across all of
    Bavaria/Italy/Slovenia if left unmasked).
    """
    with open(AUSTRIA_OUTLINE) as f:
        feature = json.load(f)
    geom_native = transform_geom("EPSG:4326", src_ds.crs, feature["geometry"])
    return rasterize(
        [(geom_native, 1)],
        out_shape=(src_ds.height, src_ds.width),
        transform=src_ds.transform,
        fill=0,
        dtype=np.uint8,
    )


def extract_band(src_ds, band_idx: int, slug: str, band_id: int, austria_mask_arr: np.ndarray):
    # Read full-resolution band (nearest is fine — values are 0/1)
    full = src_ds.read(band_idx, resampling=Resampling.nearest)

    # Max-pool downsample: preserves thin 1-pixel buffers
    band = max_pool_2d(full, DOWNSAMPLE)
    austria_band = max_pool_2d(austria_mask_arr, DOWNSAMPLE)

    # Recompute transform for the downsampled grid
    ds_transform = src_ds.transform * src_ds.transform.scale(
        src_ds.width / band.shape[1],
        src_ds.height / band.shape[0],
    )

    # Mask: pixels where band == 1 (exclusion zone) AND inside Austria
    mask = ((band == 1) & (austria_band == 1)).astype(np.uint8)

    if mask.sum() == 0:
        print(f"  Band {band_idx} ({slug}): no pixels, skipping")
        return

    tol = SIMPLIFY_TOL

    features = []
    for geom_dict, val in shapes(mask, mask=mask, transform=ds_transform):
        if val == 0:
            continue
        # Reproject from source CRS to WGS-84
        geom_wgs = transform_geom(src_ds.crs, "EPSG:4326", geom_dict)
        geom = shape(geom_wgs)
        if not geom.is_valid:
            geom = geom.buffer(0)
        geom = geom.simplify(tol, preserve_topology=True)
        if geom.is_empty:
            continue
        features.append(geom)

    if not features:
        print(f"  Band {band_idx} ({slug}): no features after simplification")
        return

    # Merge overlapping polygons
    merged = unary_union(features)

    # Flatten to individual geometries
    if merged.geom_type == "Polygon":
        geoms = [merged]
    elif merged.geom_type == "MultiPolygon":
        geoms = list(merged.geoms)
    else:
        geoms = list(merged.geoms) if hasattr(merged, "geoms") else [merged]

    fc = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": mapping(g),
                "properties": {"band_id": band_id},
            }
            for g in geoms
            if not g.is_empty
        ],
    }

    out_path = f"{OUT_DIR}/{slug}.geojson"
    with open(out_path, "w") as f:
        json.dump(fc, f, separators=(",", ":"))

    print(f"  Band {band_idx} ({slug}): {len(fc['features'])} features → {out_path}")


def main():
    print(f"Opening {SRC} …")
    with rasterio.open(SRC) as src:
        print(f"  CRS: {src.crs}, size: {src.width}×{src.height}, bands: {src.count}")
        austria_mask_arr = load_austria_mask(src)

        with open(MANIFEST, encoding="utf-8") as fh:
            manifest = json.load(fh)
        names = list(src.descriptions)
        bands = select_bands(manifest)
        print(f"  {len(bands)} Layer laut Manifest")

        for b in bands:
            if b["name"] not in names:
                print(f"  {b['name']}: nicht im Raster, übersprungen")
                continue
            band_idx = names.index(b["name"]) + 1
            extract_band(src, band_idx, b["name"], b["index"], austria_mask_arr)

    print("Done.")


if __name__ == "__main__":
    import os
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    main()
