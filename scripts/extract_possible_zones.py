#!/usr/bin/env python3
"""
Extract possible_zones / zone_centroids GeoJSONs from the Abschichtung raster.

Liest das Ergebnisband (verfügbare Flächen nach allen Ausschlüssen, ≥ 10 ha) und
vektorisiert es zu den Zonenpolygonen für Kartenlayer, Inspector und Heatmap.

Schreibt:
  geodata/possible_zones.geojson
  geodata/zone_centroids.geojson
  geodata/zone_stats.json   — {count, totalHa, perBundesland}, gelesen von
                              Inspector und Scrollytelling

Es gibt genau einen Datensatz. Bis 10.9.2026 wurden zusätzlich fünf uniforme
Siedlungsabstands-Szenarien (800/1000/1200/1500/2000 m) erzeugt; die Lieferung
widmung_v2 enthält sie nicht mehr (`SETTLEMENT_BUFFER_VARIANTS` ist leer) und sie
waren im UI nie erreichbar. Sie wurden deshalb ersatzlos entfernt.

Eigenschaften je Fläche in possible_zones.geojson:
  zone_id          — fortlaufende Ganzzahl
  area_ha          — Fläche in Hektar (in EPSG:31287 gerechnet)
  pd_mean_w_m2     — 0; das Raster liefert die Windleistungsdichte nur binär,
                     ein kontinuierliches Band ist beim Anbieter angefragt.
                     Alle Flächen liegen garantiert über der Windschwelle.
  n_existing_turbines — aus dem räumlichen Join mit existing_turbines.geojson
  bundesland       — Zentroid-in-Polygon gegen geodata/austria_states.geojson
  centroid_lat/lon — Zentroid in WGS84

zone_centroids.geojson:
  w — Heatmap-Gewicht (über den Logarithmus der Fläche normiert, damit große
      Flächen die Darstellung nicht dominieren)

Braucht geodata/austria_states.geojson (GADM Österreich Ebene 1, wird beim ersten
Lauf heruntergeladen).

Gewässer: widmung_v2 enthält das Band geography_water_bodies, die externe Maske
aus scripts/fetch_water_bodies.py wird dann übersprungen. Ältere Lieferungen ohne
dieses Band brauchen sie weiterhin, sonst tauchen große Seen als Eignungsflächen auf.

Aufruf:
  python scripts/extract_possible_zones.py [--src <raster.tif>]
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

# Default source. widmung_v2 ("abschichtung.tif", 44 Bänder) wird bevorzugt,
# sobald sie vorliegt; sonst die ältere widmung_v1-Lieferung mit 54 Bändern.
# Über --src überschreibbar.
SRC_CANDIDATES = [
    "scripts/raster/abschichtung.tif",
    "scripts/raster/osm_wka_distance_zones_widmung.tif",
]
SRC           = next((p for p in SRC_CANDIDATES if Path(p).exists()), SRC_CANDIDATES[-1])
TURBINES      = "geodata/existing_turbines.geojson"
STATES        = "geodata/austria_states.geojson"
AUSTRIA_OUTLINE = "geodata/austria_outline.geojson"
WATER_BODIES  = "scripts/raster/water_bodies.geojson"  # gitignored, see fetch_water_bodies.py
OUT_DIR       = "geodata"
STATS_OUT     = "geodata/zone_stats.json"

MIN_HA = 5.0  # cleaned bands guarantee ≥10 ha; 5 ha is a safety floor

# Ergebnisband der aktuellen Lieferung. widmung_v2 liefert genau ein Szenario:
# der gesetzliche, bundeslandspezifische Siedlungsabstand. Die fünf uniformen
# Vergleichsszenarien aus widmung_v1 (800/1000/1200/1500/2000 m) wurden am
# 10.9.2026 ersatzlos gestrichen — sie waren nie im UI erreichbar und kommen
# laut Datenanbieter nicht zurück.
RESULT_BANDS = ["available_cleaned_min_10ha", "available_cleaned_min_10ha_default"]


def result_band(src_path: str) -> str:
    """Findet das Ergebnisband, egal ob widmung_v1 oder v2."""
    with rasterio.open(src_path) as src:
        names = {d for d in src.descriptions if d}
    for candidate in RESULT_BANDS:
        if candidate in names:
            return candidate
    sys.exit(
        f"{src_path}: kein Ergebnisband gefunden. Erwartet eines von {RESULT_BANDS}, "
        f"vorhanden: {sorted(n for n in names if 'available' in n)}"
    )


def raster_has_water_band(src_path: str) -> bool:
    """widmung_v2 schließt Gewässer bereits im Raster aus (Band geography_water_bodies)."""
    with rasterio.open(src_path) as src:
        return "geography_water_bodies" in {d for d in src.descriptions if d}

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


def process(
    band_name: str, states: list[dict], turbines: list,
    austria_mask_arr: np.ndarray, water_mask_arr: np.ndarray,
) -> dict:
    print(f"\n=== Eignungsflächen (Band: {band_name}) ===")
    with rasterio.open(SRC) as src:
        band_idx = list(src.descriptions).index(band_name) + 1

    zones = extract_zones(SRC, band_idx, austria_mask_arr, water_mask_arr)
    if not zones:
        sys.exit("Keine Flächen extrahiert — das deutet auf ein leeres Ergebnisband hin.")

    assign_turbine_counts(zones, turbines)
    assign_bundesland(zones, states)

    total_ha = sum(z["area_ha"] for z in zones)
    with_turbines = sum(1 for z in zones if z["n_existing_turbines"] > 0)
    print(f"  Summary: {len(zones)} zones, {total_ha:,.0f} ha total, "
          f"{with_turbines} zones with existing turbines")

    write_zones(zones, f"{OUT_DIR}/possible_zones.geojson")
    write_centroids(zones, f"{OUT_DIR}/zone_centroids.geojson")

    return {
        "count": len(zones),
        "totalHa": round(total_ha),
        "perBundesland": bundesland_totals(zones),
    }


def main():
    band_name = result_band(SRC)
    print(f"Quelle: {SRC}")
    print(f"Ergebnisband: {band_name}")

    states = ensure_states(STATES)
    turbines = load_turbines(TURBINES)

    with rasterio.open(SRC) as src:
        austria_mask_arr = load_austria_mask(src.shape, src.transform, src.crs)
        if raster_has_water_band(SRC):
            # Gewässer stecken bereits in exclusion_geography und damit im
            # Ergebnisband — die externe Maske wäre nur eine zweite Ausführung
            # derselben Bedingung.
            print("  Gewässer: im Raster enthalten, externe Maske übersprungen")
            water_mask_arr = np.zeros(src.shape, dtype=np.uint8)
        else:
            water_mask_arr = load_water_mask(src.shape, src.transform, src.crs)

    stats = process(band_name, states, turbines, austria_mask_arr, water_mask_arr)

    with open(STATS_OUT, "w") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"\n→ {STATS_OUT} written")
    print(f"  {stats['count']} Flächen, {stats['totalHa']:,} ha")
    print("\nDone. Konstanten in Scrollytelling.svelte und Inspector.svelte prüfen.")


if __name__ == "__main__":
    import argparse
    import os

    os.chdir(Path(__file__).parent.parent)
    ap = argparse.ArgumentParser(description="Potenzialflächen aus dem Abschichtungsraster")
    ap.add_argument("--src", help=f"Quellraster (Default: {SRC})")
    args = ap.parse_args()
    if args.src:
        SRC = args.src
    if not Path(SRC).exists():
        sys.exit(f"Source not found: {SRC}")
    main()
