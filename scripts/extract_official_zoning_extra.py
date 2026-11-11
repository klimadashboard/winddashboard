#!/usr/bin/env python3
"""
Add Steiermark + Salzburg zoning polygons to geodata/official_zoning.geojson.

geodata/official_zoning.geojson historically only contained Niederösterreich's
official Windkraft-Eignungszonen (richly attributed: zoning_id, name, legal_basis,
effective_from, communities, source_url — vectorized from the NÖ Sektorales
Raumordnungsprogramm directly, not from this repo's raster pipeline).

The source raster (abschichtung.tif) additionally embeds Steiermark (SAPRO
Windenergie) and Salzburg zoning in its "official_wind_zoning" reference band —
see methodik page. This script extracts ONLY the Steiermark/Salzburg polygons
from that band (NÖ is left untouched, since the existing curated NÖ dataset is
more precise and richly attributed than a raster-derived re-extraction would be;
Kärnten and Burgenland come from their own shapefiles via
add_ktn_bgld_zoning.py).

Das Skript ist **wiederholbar**: es wirft vorhandene STMK-/SBG-Features aus
`official_zoning.geojson` heraus, bevor es die neuen anhängt. Bis zur Lieferung
clean-44-ohne-lsg (Okt. 2026) hängte es nur an — ein zweiter Lauf verdoppelte
damit stillschweigend alle steirischen und Salzburger Zonen.

Die Bandnummer steht bewusst nirgends: sie hat sich zwischen den Lieferungen
schon zweimal verschoben (30 → 37 → 36). Gesucht wird über den Bandnamen.

Usage:
  python scripts/extract_official_zoning_extra.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import shapes
from rasterio.warp import transform_geom
from shapely.geometry import shape, mapping

SRC = "scripts/raster/abschichtung.tif"
STATES = "geodata/austria_states.geojson"
OUT = "geodata/official_zoning.geojson"

BAND_NAME = "official_wind_zoning"
MIN_HA = 1.0
SIMPLIFY_TOL = 0.00005  # degrees (~5 m), matches extract_band_geojson.py

# Bundesländer to add from the raster (Niederösterreich is intentionally excluded —
# the existing curated dataset for NÖ stays authoritative).
#
# Steiermark: seit der Lieferung clean-44-ohne-lsg (Okt. 2026) liegt dem Band
# das amtliche SAPRO Windenergie 2026 zugrunde (LGBl. 87/2026, in Kraft seit
# 13.10.2026) statt der zuvor handdigitalisierten `luca_zonen/Stmk.shp`.
# Salzburg ist weiterhin handdigitalisiert, ohne bekannten Stand.
ADD_STATES = {
    "Steiermark": "SAPRO Windenergie 2026, Stmk. LGBl. Nr. 87/2026",
    "Salzburg": "Zonierung Salzburg (digitale Zonengeometrien)",
}
# Nur gesetzt, wo wir ein belastbares Inkrafttreten kennen.
EFFECTIVE_FROM = {"Steiermark": "2026-10-13"}
ID_PREFIX = {"Steiermark": "STMK", "Salzburg": "SBG"}


def main():
    with rasterio.open(SRC) as src:
        descriptions = list(src.descriptions)
        if BAND_NAME not in descriptions:
            sys.exit(f"Band '{BAND_NAME}' not found in {SRC}")
        band_idx = descriptions.index(BAND_NAME) + 1
        data = src.read(band_idx)
        transform = src.transform
        src_crs = src.crs

    states = json.load(open(STATES))
    state_polys = [
        (f["properties"]["NAME_1"], shape(f["geometry"])) for f in states["features"]
    ]

    mask = (data == 1).astype(np.uint8)
    new_features = []
    counters = {name: 0 for name in ADD_STATES}

    for geom_native, val in shapes(mask, mask=(mask == 1), transform=transform):
        if val != 1:
            continue
        poly_native = shape(geom_native)
        area_ha = round(poly_native.area / 10_000, 2)
        if area_ha < MIN_HA:
            continue

        geom_wgs = transform_geom(src_crs, "EPSG:4326", geom_native)
        geom = shape(geom_wgs)
        if not geom.is_valid:
            geom = geom.buffer(0)
        geom = geom.simplify(SIMPLIFY_TOL, preserve_topology=True)
        if geom.is_empty:
            continue

        # Centroid in WGS84 (post-reprojection) — state polygons are WGS84 too.
        centroid = geom.centroid
        bundesland = ""
        for name, sp in state_polys:
            if sp.contains(centroid):
                bundesland = name
                break
        if bundesland not in ADD_STATES:
            continue  # skip Niederösterreich (already curated) and everything else

        counters[bundesland] += 1
        prefix = ID_PREFIX[bundesland]
        props = {
            "zoning_id": f"{prefix}-{counters[bundesland]:02d}",
            "bundesland": bundesland,
            "area_ha": area_ha,
            "legal_basis": ADD_STATES[bundesland],
            "source": f"raster-derived ({Path(SRC).name}, Band {band_idx} {BAND_NAME})",
        }
        if bundesland in EFFECTIVE_FROM:
            props["effective_from"] = EFFECTIVE_FROM[bundesland]
        new_features.append({
            "type": "Feature",
            "geometry": mapping(geom),
            "properties": props,
        })

    print(f"Extracted {len(new_features)} polygons ({sum(counters.values())} total): "
          f"{ {k: v for k, v in counters.items()} }")

    # Wiederholbar: die zuvor aus dem Raster abgeleiteten STMK-/SBG-Features
    # fliegen raus, bevor die neuen angehängt werden. Erkannt werden sie am
    # `bundesland` — die kuratierten NÖ-Zonen und die aus Shapefiles ergänzten
    # Kärntner und burgenländischen Zonen bleiben unangetastet.
    existing = json.load(open(OUT))
    before = len(existing["features"])
    existing["features"] = [
        f for f in existing["features"]
        if f["properties"].get("bundesland") not in ADD_STATES
    ]
    dropped = before - len(existing["features"])
    if dropped:
        print(f"Removed {dropped} previously raster-derived "
              f"{'/'.join(ADD_STATES)} polygons before re-adding")
    existing["features"].extend(new_features)

    with open(OUT, "w") as f:
        json.dump(existing, f, separators=(",", ":"))
    print(f"→ {OUT} now has {len(existing['features'])} features "
          f"({Path(OUT).stat().st_size // 1024} KB)")


if __name__ == "__main__":
    import os
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    main()
