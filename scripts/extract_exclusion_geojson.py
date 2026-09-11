"""
Extract exclusion zone GeoJSONs from classification.tif for scrollytelling.

Gruppen (Klassencodes siehe create_classification_from_simplified.py):
  schutzgebiete   → code 1
  siedlungen      → code 2
  sonstige        → codes 3–8, 12, 13, 15, 16 (Infrastruktur, Gelände, Gewässer)
  wind            → code 11 (Wind zu gering)

Die Codes 9 und 10 sind mit widmung_v2 stillgelegt, 15 und 16 kamen hinzu; der
Bereichsausdruck 3–10 hätte die neuen stillschweigend übergangen, deshalb steht
"sonstige" jetzt als ausdrückliche Liste.
"""

import json, numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.features import shapes
from rasterio.warp import transform_geom
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
import shapely

SRC = "scripts/raster/classification.tif"
OUT_DIR = "geodata"

# Downsample factor — 20× gives ~500 m pixels, fast + small output
FACTOR = 20

# Alles, was weder Schutzgebiet (1), Siedlungsabstand (2), Wind (11),
# geeignete Fläche (14) noch außerhalb (0) ist.
SONSTIGE_CODES = [3, 4, 5, 6, 7, 8, 12, 13, 15, 16]

GROUPS = {
    "exclusion_schutz":    lambda c: c == 1,
    "exclusion_siedlung":  lambda c: c == 2,
    "exclusion_sonstige":  lambda c: np.isin(c, SONSTIGE_CODES),
    "exclusion_wind":      lambda c: c == 11,
}

def extract(arr, mask_fn, transform, src_crs):
    mask = mask_fn(arr).astype(np.uint8)
    polys = []
    for geom, val in shapes(mask, mask=(mask == 1), transform=transform):
        if val != 1:
            continue
        # reproject from EPSG:31287 → WGS84
        wgs = transform_geom(src_crs, "EPSG:4326", geom)
        polys.append(shape(wgs))

    if not polys:
        return None

    print(f"  merging {len(polys)} polygons …")
    merged = unary_union(polys)
    # simplify ~ 0.005° ≈ 500 m at Austrian latitudes
    simplified = merged.simplify(0.005, preserve_topology=True)
    return simplified

def write_geojson(geom, path):
    if geom is None:
        print(f"  [skip] no geometry")
        return
    fc = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": mapping(geom),
            "properties": {}
        }]
    }
    with open(path, "w") as f:
        json.dump(fc, f, separators=(",", ":"))
    import os
    size_kb = os.path.getsize(path) / 1024
    print(f"  → {path}  ({size_kb:.0f} KB)")

with rasterio.open(SRC) as ds:
    src_crs = ds.crs
    new_h = ds.height // FACTOR
    new_w = ds.width  // FACTOR

    print(f"Downsampling {ds.shape} → ({new_h}, {new_w}) …")
    arr = ds.read(
        1,
        out_shape=(new_h, new_w),
        resampling=Resampling.mode,
    )

    # Build new transform for downsampled raster
    from rasterio.transform import from_bounds
    t = from_bounds(*ds.bounds, new_w, new_h)

for name, fn in GROUPS.items():
    print(f"\n{name}")
    geom = extract(arr, fn, t, src_crs)
    write_geojson(geom, f"{OUT_DIR}/{name}.geojson")

print("\nDone.")
