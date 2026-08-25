#!/usr/bin/env python3
"""
Fetch Austrian water-surface polygons (lakes from GGN + rivers from OSM) and write
scripts/raster/water_bodies.geojson (gitignored, like the other large external
pipeline inputs).

The source raster (osm_wka_distance_zones_widmung.tif) has no water exclusion band
at all, so without this, lakes large enough to exceed the possible-zones 10 ha
threshold (most obviously the Austrian shore of the Bodensee, but also e.g.
Neusiedler See, Attersee, Wolfgangsee, ...) get vectorized as potential wind zones
by extract_possible_zones.py. That script rasterizes this file the same way it
already rasterizes geodata/austria_outline.geojson (load_water_mask()), and ANDs
it out of the "available" mask before vectorizing.

Source: "Stehende Gewässer des Gesamtgewässernetz Österreich (GGN)", published by
Umweltbundesamt, CC BY 4.0 — 34,789 lake polygons nationwide, already in EPSG:31287
(the raster's native CRS, so no reprojection distortion at rasterize time).
  https://www.data.gv.at/katalog/dataset/ce50ffa6-5032-4771-90a2-1c48d6a0ac85
  (dataset page lists a new "Distribution" per version bump — resolve the current
  download URL from there if this one 404s; it's a per-version Nextcloud share link,
  not a stable URL)

Second source — OSM water-area polygons, for RIVERS:
GGN's "Stehende Gewässer" covers only standing water (lakes/reservoirs). River
surfaces are missing, and that is not cosmetic: measured in the Danube corridor
alone, zone 583 (17.9 ha) sat 100 % in the Danube, 552 (122.6 ha) 67 %, 560
(365 ha) 23 %. GGN cannot close this itself — its Fließgewässer distribution is
LineString geometry (89,577 centerlines; attributes carry only LAENGE_KM/GEW_KAT,
no width), so there is no river-*area* polygon to rasterize, and buffering by an
invented width would over/under-exclude on a 25 m grid.

So this script unions two sources, each used for what it actually models well:
  1. GGN "Stehende Gewässer" — authoritative lake/reservoir polygons, and it also
     covers lake deltas that OSM tags inconsistently (the Rheindelta at the
     Bodensee is inside GGN's lake polygon but tagged wetland/reedbed/shoal in OSM)
  2. OSM natural=water + waterway=riverbank — actual river/canal surface polygons
Overlap between the two is harmless (the masks are unioned, then rasterized).

An earlier version of this script assembled water polygons from OSM tags
(natural=water, then also natural=wetland/shoal/shingle). OSM is still used here,
but only for rivers — lakes come from GGN, because OSM tags lake deltas
inconsistently and GGN gets them right.

The public Overpass API times out (504) or rate-limits (429) individual tiles
unpredictably, so the OSM half fetches a grid of tiles with long-backoff retries.
If the log shows a tile ending at 0 elements, re-run — completed tiles are cheap
to refetch and the merge dedupes by OSM id.

Usage:
  python scripts/fetch_water_bodies.py
"""

import json
import subprocess
import time
import zipfile
from pathlib import Path

import fiona
from pyproj import Transformer
from shapely.geometry import shape, mapping, Polygon
from shapely.ops import transform as shapely_transform, unary_union
from shapely.validation import make_valid

OUT = "scripts/raster/water_bodies.geojson"
# degrees, ~5 m at Austrian latitudes. MUST stay well under the raster's 25 m pixel:
# an earlier value of 0.0005 (~50 m) was fine for blobby lakes but silently gutted
# rivers, which are often only 50–100 m wide — the Danube stretch at zone 549 came
# out covering 3.5 % of the zone instead of the 42 % it actually covers.
SIMPLIFY_TOL = 0.00005

# ── Source 1: GGN standing waters (lakes/reservoirs) ────────────────────────
GGN_ZIP_URL = "https://docs.umweltbundesamt.at/s/K5HSHMCrJTBwjLt/download"
EXTRACT_DIR = Path("scripts/raster/ggn_stehende_gewaesser")
SHP_NAME = "stehendeGewaesser.shp"

# ── Source 2: OSM water-surface polygons (rivers/canals) ───────────────────
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OSM_RAW_CACHE = Path("scripts/raster/osm_water_raw.json")
# Austria's bbox plus a border buffer (border rivers: Danube, Rhein, Inn, March).
SOUTH, WEST, NORTH, EAST = 46.2, 9.2, 49.1, 17.3
LON_STEPS, LAT_STEPS = 4, 3
# natural=water covers rivers/canals as areas; waterway=riverbank is the older
# tagging for the same thing and is still present on plenty of Austrian rivers.
OSM_QUERY = """[out:json][timeout:120];
(
  way["natural"="water"]({s},{w},{n},{e});
  relation["natural"="water"]({s},{w},{n},{e});
  way["waterway"="riverbank"]({s},{w},{n},{e});
  relation["waterway"="riverbank"]({s},{w},{n},{e});
);
out geom;"""


def load_ggn_lakes() -> list[dict]:
    import urllib.request

    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = EXTRACT_DIR / "ggn.zip"
    if not (EXTRACT_DIR / SHP_NAME).exists():
        print(f"Downloading {GGN_ZIP_URL} ...")
        urllib.request.urlretrieve(GGN_ZIP_URL, zip_path)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(EXTRACT_DIR)
        zip_path.unlink()

    transformer = Transformer.from_crs("EPSG:31287", "EPSG:4326", always_xy=True)
    features = []
    with fiona.open(EXTRACT_DIR / SHP_NAME) as src:
        print(f"GGN: {len(src)} lake polygons ({src.crs})")
        for f in src:
            geom = shape(f["geometry"])
            if not geom.is_valid:
                geom = make_valid(geom)
            geom_wgs = shapely_transform(lambda x, y: transformer.transform(x, y), geom)
            if geom_wgs.is_empty:
                continue
            features.append({
                "type": "Feature",
                "geometry": mapping(geom_wgs),
                "properties": {
                    "name": f["properties"].get("NAME"),
                    "area_km2": f["properties"].get("FLAECHEKM2"),
                    "src": "ggn",
                },
            })
    return features


def fetch_osm_tile(s, w, n, e, tmp_path, max_attempts=5, backoff=25) -> list[dict]:
    query = OSM_QUERY.format(s=s, w=w, n=n, e=e)
    for attempt in range(max_attempts):
        result = subprocess.run(
            ["curl", "-s", "--max-time", "130", "-X", "POST", "--data-binary", query,
             OVERPASS_URL, "-o", str(tmp_path), "-w", "%{http_code}"],
            capture_output=True, text=True,
        )
        if result.stdout.strip() == "200":
            try:
                return json.loads(tmp_path.read_text()).get("elements", [])
            except Exception as ex:
                print(f"    parse error: {ex}")
                return []
        print(f"    HTTP {result.stdout.strip()!r}, waiting {backoff:.0f}s...")
        time.sleep(backoff)
    print(f"    FAILED after {max_attempts} attempts")
    return []


def way_to_geometry(el: dict) -> dict | None:
    coords = [[pt["lon"], pt["lat"]] for pt in el.get("geometry") or []]
    if len(coords) < 4 or coords[0] != coords[-1]:
        return None
    return {"type": "Polygon", "coordinates": [coords]}


def _stitch_rings(fragments: list[list[list[float]]]) -> list[list[list[float]]]:
    """Assemble OSM multipolygon member fragments into closed rings.

    Large OSM multipolygons (all big rivers) split each ring across several member
    ways, so a member's own geometry is usually an OPEN linestring — only a
    fragment of the ring. Closing each fragment on its own (an earlier bug here)
    yields slivers instead of the actual polygon: relation 2731237 (Danube near
    Mauthausen) has 3 outer fragments that form ONE ring, and the zone sitting in
    that stretch of river was consequently never masked. Fragments are joined
    end-to-end, in either direction, until each ring closes.
    """
    rings: list[list[list[float]]] = []
    pending = [list(f) for f in fragments if len(f) >= 2]
    while pending:
        cur = pending.pop(0)
        if cur[0] == cur[-1]:
            if len(cur) >= 4:
                rings.append(cur)
            continue
        joined = True
        while joined and cur[0] != cur[-1]:
            joined = False
            for i, frag in enumerate(pending):
                if frag[0] == cur[-1]:
                    cur = cur + frag[1:]
                elif frag[-1] == cur[-1]:
                    cur = cur + frag[-2::-1]
                elif frag[-1] == cur[0]:
                    cur = frag[:-1] + cur
                elif frag[0] == cur[0]:
                    cur = frag[::-1][:-1] + cur
                else:
                    continue
                pending.pop(i)
                joined = True
                break
        # Unclosed leftovers happen with data errors / clipped-at-bbox members;
        # close them so a partially-tagged river still contributes some mask.
        if cur[0] != cur[-1]:
            cur = cur + [cur[0]]
        if len(cur) >= 4:
            rings.append(cur)
    return rings


def relation_to_geometry(el: dict) -> dict | None:
    outer_frags, inner_frags = [], []
    for member in el.get("members", []):
        geom = member.get("geometry")
        if not geom:
            continue
        coords = [[pt["lon"], pt["lat"]] for pt in geom]
        if len(coords) < 2:
            continue
        # Blank role is common on simple multipolygons and means "outer".
        (inner_frags if member.get("role") == "inner" else outer_frags).append(coords)

    outer_rings = _stitch_rings(outer_frags)
    inner_rings = _stitch_rings(inner_frags)
    if not outer_rings:
        return None

    outer_polys = []
    for ring in outer_rings:
        try:
            p = Polygon(ring)
        except Exception:
            continue
        if not p.is_valid:
            p = make_valid(p)
        if not p.is_empty:
            outer_polys.append(p)
    if not outer_polys:
        return None

    merged = unary_union(outer_polys)
    if inner_rings:
        holes = []
        for ring in inner_rings:
            try:
                h = Polygon(ring)
            except Exception:
                continue
            if not h.is_valid:
                h = make_valid(h)
            if not h.is_empty:
                holes.append(h)
        if holes:
            merged = merged.difference(unary_union(holes))
    if merged.is_empty:
        return None
    # difference()/make_valid() can yield a GeometryCollection with stray lines;
    # keep only the areal parts so rasterize() downstream gets clean polygons.
    if merged.geom_type == "GeometryCollection":
        polys = [g for g in merged.geoms if g.geom_type in ("Polygon", "MultiPolygon")]
        if not polys:
            return None
        merged = unary_union(polys)
    return mapping(merged)


def load_osm_water() -> list[dict]:
    # Raw Overpass elements are cached so that a bug in the geometry-building code
    # below costs a re-run of the cheap part only — the fetch itself takes ~10 min
    # thanks to Overpass's 429/504 backoffs. Delete the cache to force a refetch.
    if OSM_RAW_CACHE.exists():
        seen_list = json.loads(OSM_RAW_CACHE.read_text())
        print(f"\nOSM: reusing cached raw elements from {OSM_RAW_CACHE} "
              f"({len(seen_list)} elements) — delete it to refetch")
        seen = {(el["type"], el["id"]): el for el in seen_list}
    else:
        lon_edges = [WEST + i * (EAST - WEST) / LON_STEPS for i in range(LON_STEPS + 1)]
        lat_edges = [SOUTH + j * (NORTH - SOUTH) / LAT_STEPS for j in range(LAT_STEPS + 1)]
        tiles = [
            (lat_edges[j], lon_edges[i], lat_edges[j + 1], lon_edges[i + 1])
            for i in range(LON_STEPS) for j in range(LAT_STEPS)
        ]
        print(f"\nOSM: fetching {len(tiles)} tiles from {OVERPASS_URL} ...")

        tmp_path = Path("/tmp/_fetch_water_tile.json")
        seen: dict[tuple[str, int], dict] = {}
        for idx, (s, w, n, e) in enumerate(tiles):
            elements = fetch_osm_tile(s, w, n, e, tmp_path)
            new = 0
            for el in elements:
                key = (el["type"], el["id"])
                if key not in seen:
                    seen[key] = el
                    new += 1
            print(f"  tile {idx + 1}/{len(tiles)} ({s:.2f},{w:.2f})-({n:.2f},{e:.2f}): "
                  f"{len(elements)} elements, {new} new")
        OSM_RAW_CACHE.parent.mkdir(parents=True, exist_ok=True)
        OSM_RAW_CACHE.write_text(json.dumps(list(seen.values())))
        print(f"OSM: cached raw elements → {OSM_RAW_CACHE}")

    features, skipped = [], 0
    for el in seen.values():
        raw = way_to_geometry(el) if el["type"] == "way" else relation_to_geometry(el)
        if raw is None:
            skipped += 1
            continue
        geom = shape(raw)
        if not geom.is_valid:
            geom = make_valid(geom)
        geom = geom.simplify(SIMPLIFY_TOL, preserve_topology=True)
        if geom.is_empty:
            skipped += 1
            continue
        tags = el.get("tags", {})
        features.append({
            "type": "Feature",
            "geometry": mapping(geom),
            "properties": {
                "name": tags.get("name"),
                "water": tags.get("water") or tags.get("waterway"),
                "src": "osm",
            },
        })
    print(f"OSM: {len(features)} polygons ({skipped} skipped as invalid/empty)")
    return features


def main():
    features = load_ggn_lakes() + load_osm_water()
    print(f"\n→ {len(features)} features total")
    with open(OUT, "w") as fh:
        json.dump({"type": "FeatureCollection", "features": features}, fh, separators=(",", ":"))
    print(f"→ {OUT} ({Path(OUT).stat().st_size // 1024} KB)")


if __name__ == "__main__":
    import os
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    main()
