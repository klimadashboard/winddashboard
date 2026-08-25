"""
Extract individual band GeoJSONs from osm_wka_distance_zones_widmung.tif.

Each of the 18 "default" exclusion bands is polygonized and written to
geodata/band_NN_<slug>.geojson. Features have a single property: {"band_id": N}.

The settlement-distance band (band_01_human_settlement) additionally gets 5 more
variants extracted (800/1000/1200/1500/2000 m) from the source file's settlement-
distance-variant bands, since that is the only band that differs between the 6
settlement-distance scenarios (see PIPELINE.md / README §3.6) — everything else
(power lines, roads, rail, cableways, military, airports, nature, terrain, wind)
is identical across all variants, so only this one band needs extra copies.

Uses Resampling.max so thin buffers (roads, power lines) don't disappear at 20×.
"""

import json
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.features import rasterize, shapes
from rasterio.warp import transform_geom
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
import shapely

SRC = "scripts/raster/osm_wka_distance_zones_widmung.tif"
AUSTRIA_OUTLINE = "geodata/austria_outline.geojson"
OUT_DIR = "geodata"

# (source band index, output band_id, slug) for the 18 "default" exclusion bands.
# output band_id (1-18) is the STABLE identifier used throughout the app
# (src/lib/config/bands.ts BAND_DEFS[].band) — it must NOT be confused with the
# source band index, which only says where to read the pixels from.
BAND_SLUGS = [
    (2,  1,  "band_01_human_settlement"),
    (4,  2,  "band_02_human_important_objects"),
    (6,  3,  "band_03_human_cableway_buildings"),
    (8,  4,  "band_04_human_haeuser_im_gruenen"),
    (10, 5,  "band_05_human_general_buildings"),
    (11, 6,  "band_06_human_power_380kv"),
    (12, 7,  "band_07_human_road_motorway"),
    (13, 8,  "band_08_human_road_federal"),
    (14, 9,  "band_09_human_rail"),
    (15, 10, "band_10_human_cableway_people"),
    (16, 11, "band_11_human_military"),
    (17, 12, "band_12_human_airport"),
    (18, 13, "band_13_human_airport_lateral"),
    (19, 14, "band_14_nature_protection"),
    (20, 15, "band_15_nature_osm"),
    (21, 16, "band_16_geo_slope"),
    (22, 17, "band_17_geo_elevation"),
    (23, 18, "band_18_geo_wind"),
]

# Extra settlement-distance variants for band_01 (band 2 above = "default").
# Resolved by band *description*, not a hardcoded index — robust to re-ordering.
SETTLEMENT_VARIANT_DESCRIPTIONS = {
    "800":  "settlement_widmung_buffer_800m",
    "1000": "settlement_widmung_buffer_1000m",
    "1200": "settlement_widmung_buffer_1200m",
    "1500": "settlement_widmung_buffer_1500m",
    "2000": "settlement_widmung_buffer_2000m",
}

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

        for band_idx, band_id, slug in BAND_SLUGS:
            if band_idx > src.count:
                print(f"  Band {band_idx}: not in file (only {src.count} bands), skipping")
                continue
            extract_band(src, band_idx, slug, band_id, austria_mask_arr)

        print("\nSettlement-distance variants (band_01 alternates) …")
        descriptions = list(src.descriptions)
        for variant, band_name in SETTLEMENT_VARIANT_DESCRIPTIONS.items():
            if band_name not in descriptions:
                print(f"  {band_name}: not found in file, skipping")
                continue
            band_idx = descriptions.index(band_name) + 1  # rasterio band index is 1-based
            slug = f"band_01_human_settlement_{variant}"
            extract_band(src, band_idx, slug, band_id=1, austria_mask_arr=austria_mask_arr)

    print("Done.")


if __name__ == "__main__":
    import os
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    main()
