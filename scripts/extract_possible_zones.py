#!/usr/bin/env python3
"""
Extract possible_zones / zone_centroids GeoJSONs for all 6 settlement-distance
variants from osm_wka_distance_zones_widmung.tif.

Reads the available_cleaned_min_10ha_<variant> band for each of the 6 settlement-
distance scenarios (default / 800m / 1000m / 1200m / 1500m / 2000m) — the
authoritative set of available wind areas after all exclusions, ≥10 ha — and
vectorizes each to produce the zone polygons used by the app's map layers,
inspector, and the interactive settlement-distance slider.

For each non-default variant, writes:
  geodata/possible_zones_<variant>.geojson
  geodata/zone_centroids_<variant>.geojson

The "default" variant is written unsuffixed instead (possible_zones.geojson /
zone_centroids.geojson) — those two names are the same file, aliased in
src/routes/data/[name]/+server.ts, so there is exactly one copy of the default
scenario's data on disk (not a byte-identical duplicate under two filenames).

Also writes geodata/variant_stats.json — per-variant {count, totalHa, perBundesland}
— consumed by the frontend (Inspector zone count, Scrollytelling constants).

Properties written to each possible_zones_<variant>.geojson:
  zone_id          — sequential integer (per variant)
  area_ha          — polygon area in hectares (native EPSG:31287 projection)
  pd_mean_w_m2     — 0 (actual value not available in this raster;
                       all cleaned zones are guaranteed >= the variant's wind threshold)
  n_existing_turbines — count from spatial join with existing_turbines.geojson
  bundesland       — assigned via centroid-in-polygon against geodata/austria_states.geojson
  centroid_lat/lon — WGS84 centroid

zone_centroids_<variant>.geojson:
  w — heatmap weight (normalised by log-area so large zones don't dominate)

Requires geodata/austria_states.geojson (GADM Austria level-1, downloaded once by this script).

Also masks out scripts/raster/water_bodies.geojson (OSM natural=water lakes/reservoirs,
see scripts/fetch_water_bodies.py) — the source raster has no water exclusion at
all, so without this, lakes large enough to exceed the 10 ha threshold (e.g. parts
of the Bodensee) were showing up as potential wind zones.

Usage:
  python scripts/extract_possible_zones.py
"""

import json
import math
import sys
import urllib.request
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import rasterize, shapes
from rasterio.warp import transform_geom, transform as warp_transform
from rasterio.crs import CRS
from shapely.geometry import shape, mapping, Point
from shapely.strtree import STRtree

SRC           = "scripts/raster/osm_wka_distance_zones_widmung.tif"
TURBINES      = "geodata/existing_turbines.geojson"
STATES        = "geodata/austria_states.geojson"
AUSTRIA_OUTLINE = "geodata/austria_outline.geojson"
WATER_BODIES  = "scripts/raster/water_bodies.geojson"  # gitignored, see fetch_water_bodies.py
OUT_DIR       = "geodata"
STATS_OUT     = "geodata/variant_stats.json"

MIN_HA = 5.0  # cleaned bands guarantee ≥10 ha; 5 ha is a safety floor

# Variant id → source band description. "default" is written unsuffixed
# (possible_zones.geojson, not possible_zones_default.geojson) — see process_variant().
VARIANTS = {
    "default": "available_cleaned_min_10ha_default",
    "800":     "available_cleaned_min_10ha_800m",
    "1000":    "available_cleaned_min_10ha_1000m",
    "1200":    "available_cleaned_min_10ha_1200m",
    "1500":    "available_cleaned_min_10ha_1500m",
    "2000":    "available_cleaned_min_10ha_2000m",
}

STATES_URL = (
    "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_AUT_1.json"
)


def ensure_states(path: str) -> list[dict]:
    """Load (downloading once if needed) Austrian state polygons as list of {name, geom}."""
    if not Path(path).exists():
        print(f"Downloading state boundaries → {path} …")
        urllib.request.urlretrieve(STATES_URL, path)
    with open(path) as f:
        fc = json.load(f)
    return [
        {"name": feat["properties"]["NAME_1"], "geom": shape(feat["geometry"])}
        for feat in fc["features"]
    ]


def assign_bundesland(zones: list[dict], states: list[dict]) -> None:
    """Mutates zones in-place: adds bundesland via centroid-in-polygon."""
    unassigned = 0
    for z in zones:
        pt = Point(z["centroid_lon"], z["centroid_lat"])
        z["bundesland"] = ""
        for s in states:
            if s["geom"].contains(pt):
                z["bundesland"] = s["name"]
                break
        if not z["bundesland"]:
            unassigned += 1
    if unassigned:
        print(f"  {unassigned} zones unassigned (border edge cases)")


def load_turbines(path: str) -> list:
    with open(path) as f:
        gj = json.load(f)
    return [
        Point(feat["geometry"]["coordinates"][:2])
        for feat in gj.get("features", [])
        if feat.get("geometry", {}).get("type") == "Point"
    ]


def load_austria_mask(shape_hw: tuple[int, int], transform, crs) -> np.ndarray:
    """Rasterize geodata/austria_outline.geojson to the source grid.

    The source raster's own bands (esp. geography_wind_too_low, which flags
    missing Global Wind Atlas data as "excluded") are NOT clipped to Austria's
    real border — they cover the whole rectangular grid extent, which bleeds
    a few hundred hectares into neighbouring countries at the edges. Masking
    every band read with the real outline before vectorizing removes that
    leakage, instead of relying on the map's visual grey overlay (which sits
    below the zone-fill layer and doesn't actually clip it).
    """
    with open(AUSTRIA_OUTLINE) as f:
        feature = json.load(f)
    geom_native = transform_geom("EPSG:4326", crs, feature["geometry"])
    return rasterize(
        [(geom_native, 1)], out_shape=shape_hw, transform=transform, fill=0, dtype=np.uint8,
    )


def load_water_mask(shape_hw: tuple[int, int], transform, crs) -> np.ndarray:
    """Rasterize scripts/raster/water_bodies.geojson to the source grid.

    Same pattern as load_austria_mask() — the source raster's bands have no
    water exclusion at all, so lakes large enough to exceed MIN_HA (e.g. the
    Austrian shore of the Bodensee) would otherwise be vectorized as potential
    wind zones. Returns an all-zero mask (no-op) if the file doesn't exist yet,
    so this script still runs before scripts/fetch_water_bodies.py has been run.
    """
    if not Path(WATER_BODIES).exists():
        print(f"  [warn] {WATER_BODIES} not found — water bodies will NOT be excluded")
        return np.zeros(shape_hw, dtype=np.uint8)
    with open(WATER_BODIES) as f:
        fc = json.load(f)
    geoms_native = [
        (transform_geom("EPSG:4326", crs, feat["geometry"]), 1) for feat in fc["features"]
    ]
    return rasterize(
        geoms_native, out_shape=shape_hw, transform=transform, fill=0, dtype=np.uint8,
    )


def extract_zones(
    src_path: str, band_idx: int, austria_mask_arr: np.ndarray, water_mask_arr: np.ndarray,
) -> list[dict]:
    with rasterio.open(src_path) as src:
        data = src.read(band_idx)
        transform = src.transform
        src_crs = src.crs

    mask = ((data == 1) & (austria_mask_arr == 1) & (water_mask_arr == 0)).astype(np.uint8)
    pixel_area_ha = abs(transform.a * transform.e) / 10_000
    print(f"  {mask.sum():,} pixels = ~{mask.sum() * pixel_area_ha:,.0f} ha candidate area")

    zones = []
    for geom_native, val in shapes(mask, mask=(mask == 1), transform=transform, connectivity=8):
        if val != 1:
            continue
        poly_native = shape(geom_native)
        area_ha = round(poly_native.area / 10_000, 2)
        if area_ha < MIN_HA:
            continue

        geom_wgs84 = transform_geom(src_crs, "EPSG:4326", geom_native)
        c = poly_native.centroid
        xs, ys = warp_transform(src_crs, CRS.from_epsg(4326), [c.x], [c.y])
        zones.append({
            "geom": shape(geom_wgs84),
            "area_ha": area_ha,
            "centroid_lon": round(xs[0], 6),
            "centroid_lat": round(ys[0], 6),
        })

    print(f"  {len(zones)} zones ≥{MIN_HA} ha extracted")
    return zones


def assign_turbine_counts(zones: list[dict], turbines: list) -> None:
    for z in zones:
        z["n_existing_turbines"] = 0
    if not zones or not turbines:
        return
    tree = STRtree([z["geom"] for z in zones])
    for pt in turbines:
        # predicate="within" tests pt.within(tree_geometry) — i.e. "is this
        # turbine point inside this zone polygon" (STRtree.query evaluates
        # predicate(query_geometry, tree_geometry), not the reverse).
        for i in tree.query(pt, predicate="within"):
            zones[i]["n_existing_turbines"] += 1


def write_zones(zones: list[dict], path: str) -> None:
    features = [
        {
            "type": "Feature",
            "geometry": mapping(z["geom"]),
            "properties": {
                "zone_id": i,
                "area_ha": z["area_ha"],
                "pd_mean_w_m2": 0,
                "n_existing_turbines": z["n_existing_turbines"],
                "bundesland": z["bundesland"],
                "centroid_lat": z["centroid_lat"],
                "centroid_lon": z["centroid_lon"],
            },
        }
        for i, z in enumerate(zones, 1)
    ]
    with open(path, "w") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, separators=(",", ":"))
    print(f"  → {path}  ({len(features)} zones, {Path(path).stat().st_size // 1024} KB)")


def write_centroids(zones: list[dict], path: str) -> None:
    max_log = math.log(max(z["area_ha"] for z in zones) + 1)
    features = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [z["centroid_lon"], z["centroid_lat"]]},
            "properties": {"w": round(math.log(z["area_ha"] + 1) / max_log, 4)},
        }
        for z in zones
    ]
    with open(path, "w") as f:
        json.dump({"type": "FeatureCollection", "features": features}, f, separators=(",", ":"))
    print(f"  → {path}  ({len(features)} centroids, {Path(path).stat().st_size // 1024} KB)")


def bundesland_totals(zones: list[dict]) -> dict:
    totals: dict[str, float] = {}
    for z in zones:
        bl = z["bundesland"] or "(unassigned)"
        totals[bl] = totals.get(bl, 0) + z["area_ha"]
    return {bl: round(ha) for bl, ha in sorted(totals.items(), key=lambda x: -x[1])}


def process_variant(
    variant: str, band_name: str, states: list[dict], turbines: list,
    austria_mask_arr: np.ndarray, water_mask_arr: np.ndarray,
) -> dict:
    print(f"\n=== Variante '{variant}' (Band: {band_name}) ===")
    with rasterio.open(SRC) as src:
        descriptions = list(src.descriptions)
        if band_name not in descriptions:
            sys.exit(f"Band '{band_name}' not found in {SRC}")
        band_idx = descriptions.index(band_name) + 1

    zones = extract_zones(SRC, band_idx, austria_mask_arr, water_mask_arr)
    if not zones:
        print(f"  [warn] no zones extracted for variant '{variant}'")
        return {"count": 0, "totalHa": 0, "perBundesland": {}}

    assign_turbine_counts(zones, turbines)
    assign_bundesland(zones, states)

    total_ha = sum(z["area_ha"] for z in zones)
    with_turbines = sum(1 for z in zones if z["n_existing_turbines"] > 0)
    print(f"  Summary: {len(zones)} zones, {total_ha:,.0f} ha total, "
          f"{with_turbines} zones with existing turbines")

    # "default" is written unsuffixed only — possible_zones.geojson IS the
    # default variant, so a separate possible_zones_default.geojson would just
    # be a byte-identical ~15 MB duplicate (same for zone_centroids).
    if variant == "default":
        write_zones(zones, f"{OUT_DIR}/possible_zones.geojson")
        write_centroids(zones, f"{OUT_DIR}/zone_centroids.geojson")
    else:
        write_zones(zones, f"{OUT_DIR}/possible_zones_{variant}.geojson")
        write_centroids(zones, f"{OUT_DIR}/zone_centroids_{variant}.geojson")

    return {
        "count": len(zones),
        "totalHa": round(total_ha),
        "perBundesland": bundesland_totals(zones),
    }


def main():
    states = ensure_states(STATES)
    turbines = load_turbines(TURBINES)

    with rasterio.open(SRC) as src:
        austria_mask_arr = load_austria_mask(src.shape, src.transform, src.crs)
        water_mask_arr = load_water_mask(src.shape, src.transform, src.crs)

    stats = {}
    for variant, band_name in VARIANTS.items():
        stats[variant] = process_variant(
            variant, band_name, states, turbines, austria_mask_arr, water_mask_arr,
        )

    with open(STATS_OUT, "w") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"\n→ {STATS_OUT} written")

    print("\n=== Übersicht aller Varianten ===")
    for variant, s in stats.items():
        print(f"  {variant:8s}: {s['count']:5d} Zonen, {s['totalHa']:>10,.0f} ha")

    print("\nDone. Update Scrollytelling.svelte constants with the 'default' values above.")


if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent.parent)
    if not Path(SRC).exists():
        sys.exit(f"Source not found: {SRC}")
    main()
