#!/usr/bin/env python3
"""
Add Kärnten + Burgenland official zoning polygons to geodata/official_zoning.geojson.

Both are downloaded directly from the Land's own GIS portal (curated vector data,
not raster-derived like the Steiermark/Salzburg addition in
extract_official_zoning_extra.py):

  Kärnten (RED III Windkraftbeschleunigungsgebiete, EPSG:31258):
    https://www.data.gv.at/datasets/93a7b404-c30d-474e-864f-98859529a7d7
    https://gis.ktn.gv.at/OGD/Geographie_Planung/RED_III_Windkraftbeschleunigungszone.zip
    → scripts/raster/ktn_windkraftbeschleunigungszone/ (gitignored, re-download if missing)
    4 Beschleunigungsgebiete, all "positive" zones (no separate exclusion layer
    published) — matches the officialZoneType 'positive' case already handled by
    introKärnten() in src/lib/data/regionIntro.ts.

  Burgenland (WK_Eignungszonen, EPSG:31259):
    https://geodaten.bgld.gv.at (Kategorie "Raumplanung" → WK_Eignungszonen.zip)
    → scripts/raster/bgld_wk_eignungszonen/ (gitignored, re-download if missing)
    71 features total: 40 Eignungszonen + 31 Ausschlusszonen. Only the Eignungszonen
    are added here — official-zones-fill on the map is styled as a single purple
    "positive zone" fill (Map.svelte), so mixing in Ausschlusszonen there would
    visually mislabel them as buildable. The Ausschlusszonen need their own map
    layer/styling before they can be added; skipped for now (31 features dropped).

Usage:
  python scripts/add_ktn_bgld_zoning.py
"""

import json
from pathlib import Path

import fiona
from pyproj import Transformer
from shapely.geometry import shape, mapping
from shapely.ops import transform as shapely_transform

OUT = "geodata/official_zoning.geojson"

KTN_SHP = "scripts/raster/ktn_windkraftbeschleunigungszone/RED_III_Windkraftbeschleunigungszone.shp"
KTN_SOURCE_URL = "https://www.data.gv.at/datasets/93a7b404-c30d-474e-864f-98859529a7d7"

BGLD_SHP = "scripts/raster/bgld_wk_eignungszonen/WK_Eignungszonen.shp"
BGLD_SOURCE_URL = "https://geodaten.bgld.gv.at/de/downloads/geodaten.html"


def reproject(geom_native, src_crs):
    transformer = Transformer.from_crs(src_crs, "EPSG:4326", always_xy=True)
    return shapely_transform(lambda x, y: transformer.transform(x, y), shape(geom_native))


def load_ktn():
    features = []
    with fiona.open(KTN_SHP) as src:
        for i, f in enumerate(src, 1):
            geom_native = f["geometry"]
            poly_native = shape(geom_native)
            area_ha = round(poly_native.area / 10_000, 2)
            geom_wgs = reproject(geom_native, src.crs)
            features.append({
                "type": "Feature",
                "geometry": mapping(geom_wgs),
                "properties": {
                    "zoning_id": f"KTN-{i:02d}",
                    "bundesland": "Kärnten",
                    "name": f["properties"].get("ZONENBEZ"),
                    "area_ha": area_ha,
                    "zone_type": "positive",
                    "legal_basis": "RED III Windkraftbeschleunigungsgebiete Kärnten "
                                   "(Anlage zu § 7c Abs. 2 K-ROG 2021)",
                    "source_url": KTN_SOURCE_URL,
                },
            })
    return features


def load_bgld():
    features = []
    i = 0
    with fiona.open(BGLD_SHP) as src:
        for f in src:
            props = f["properties"]
            if props.get("Status") != "Eignungszone gem. Verordnung":
                continue  # Ausschlusszonen — see module docstring
            i += 1
            geom_native = f["geometry"]
            poly_native = shape(geom_native)
            area_ha = round(poly_native.area / 10_000, 2)
            geom_wgs = reproject(geom_native, src.crs)
            in_kraft = props.get("in_Kraft")  # "20230210" → "2023-02-10"
            effective_from = (
                f"{in_kraft[:4]}-{in_kraft[4:6]}-{in_kraft[6:8]}" if in_kraft else None
            )
            lgbl = props.get("LGBl")
            features.append({
                "type": "Feature",
                "geometry": mapping(geom_wgs),
                "properties": {
                    "zoning_id": f"BGLD-{i:02d}",
                    "bundesland": "Burgenland",
                    "area_ha": area_ha,
                    "zone_type": "eignung",
                    "legal_basis": f"Bgld. LGBl. Nr. {lgbl}" if lgbl else None,
                    "effective_from": effective_from,
                    "communities": props.get("Gemeinde"),
                    "source_url": BGLD_SOURCE_URL,
                },
            })
    return features


def main():
    ktn_features = load_ktn()
    bgld_features = load_bgld()
    print(f"Kärnten: {len(ktn_features)} Beschleunigungsgebiete")
    print(f"Burgenland: {len(bgld_features)} Eignungszonen (Ausschlusszonen skipped)")

    existing = json.load(open(OUT))
    existing["features"].extend(ktn_features)
    existing["features"].extend(bgld_features)

    with open(OUT, "w") as f:
        json.dump(existing, f, separators=(",", ":"))
    print(f"→ {OUT} now has {len(existing['features'])} features "
          f"({Path(OUT).stat().st_size // 1024} KB)")


if __name__ == "__main__":
    import os
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    main()
