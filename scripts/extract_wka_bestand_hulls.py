#!/usr/bin/env python3
"""Extrahiert Band 38 (`wka_bestand_ausserhalb_zonen`) als GeoJSON.

Was das Band ist
----------------
Der Datenanbieter fasst die bestehenden Windräder zu "Park-Hüllen" zusammen:
Anlagen mit weniger als 750 m Abstand gelten als ein Park, um dessen konvexe
Hülle 200 m Rand gelegt werden. Das Band enthält nur die Hüllen, die
**außerhalb** der amtlichen Zonen liegen.

Warum ein eigenes Skript
------------------------
`extract_band_geojson.py` nimmt laut Manifest ausschließlich Bänder mit
`rolle: "bedingung"` — also die echten Ausschlussgründe. Band 38 hat
`rolle: "referenz"` und fiel deshalb bisher durch jedes Raster der Pipeline:
kein GeoJSON, keine Kachel, kein Layer. Dieselbe Sonderbehandlung hat schon
Band 37 (`extract_official_zoning_extra.py`).

Das Band ist keine Ausschlussfläche und darf in der Karte auch nicht so
aussehen — es beantwortet die Frage "wo stehen heute Windräder, ohne dass das
Land dafür eine Zone ausgewiesen hat". Im Burgenland ist das der Regelfall:
die Eignungszonen von 2023 decken die älteren Parks nicht ab.

Aufruf
------
    python scripts/extract_wka_bestand_hulls.py
"""

from __future__ import annotations

import json
import os
import sys

import numpy as np
import rasterio
from rasterio.features import shapes
from rasterio.warp import transform_geom
from shapely.geometry import shape, mapping, Point
from shapely.prepared import prep

SRC = "scripts/raster/abschichtung.tif"
STATES = "geodata/austria_states.geojson"
TURBINES = "geodata/existing_turbines.geojson"
OUT = "geodata/wka_bestand_ausserhalb_zonen.geojson"

BAND_NAME = "wka_bestand_ausserhalb_zonen"
MIN_HA = 1.0
SIMPLIFY_TOL = 0.00005  # ~5 m, wie in extract_band_geojson.py

PREFIX = {
    "Burgenland": "BGLD",
    "Kärnten": "KTN",
    "Niederösterreich": "NOE",
    "Oberösterreich": "OOE",
    "Salzburg": "SBG",
    "Steiermark": "STMK",
    "Tirol": "T",
    "Vorarlberg": "VBG",
    "Wien": "W",
}


def main() -> None:
    with rasterio.open(SRC) as src:
        names = list(src.descriptions)
        if BAND_NAME not in names:
            sys.exit(f"Band '{BAND_NAME}' fehlt in {SRC}")
        idx = names.index(BAND_NAME) + 1
        data = src.read(idx)
        transform = src.transform
        src_crs = src.crs

    states = json.load(open(STATES))
    state_polys = [(f["properties"]["NAME_1"], shape(f["geometry"])) for f in states["features"]]

    turbines = json.load(open(TURBINES))
    pts = [Point(f["geometry"]["coordinates"]) for f in turbines["features"]]

    mask = (data == 1).astype(np.uint8)
    features = []
    counters: dict[str, int] = {}
    skipped_small = 0

    for geom_native, val in shapes(mask, mask=(mask == 1), transform=transform):
        if val != 1:
            continue
        poly_native = shape(geom_native)
        area_ha = round(poly_native.area / 10_000, 2)
        if area_ha < MIN_HA:
            skipped_small += 1
            continue

        geom = shape(transform_geom(src_crs, "EPSG:4326", geom_native))
        if not geom.is_valid:
            geom = geom.buffer(0)
        geom = geom.simplify(SIMPLIFY_TOL, preserve_topology=True)
        if geom.is_empty:
            continue

        centroid = geom.centroid
        bundesland = next((n for n, sp in state_polys if sp.contains(centroid)), "")
        if not bundesland:
            # Hüllen ragen mit ihrem 200-m-Rand über die Staatsgrenze; dann
            # entscheidet die größte Überlappung statt des Schwerpunkts.
            best, best_area = "", 0.0
            for n, sp in state_polys:
                inter = geom.intersection(sp).area
                if inter > best_area:
                    best, best_area = n, inter
            bundesland = best

        prepared = prep(geom)
        turbine_count = sum(1 for p in pts if prepared.contains(p))

        counters[bundesland] = counters.get(bundesland, 0) + 1
        features.append({
            "type": "Feature",
            "geometry": mapping(geom),
            "properties": {
                "hull_id": f"{PREFIX.get(bundesland, 'XX')}-WKA-{counters[bundesland]:03d}",
                "bundesland": bundesland,
                "area_ha": area_ha,
                "turbines": turbine_count,
                "band_id": 38,
            },
        })

    total_ha = round(sum(f["properties"]["area_ha"] for f in features), 1)
    total_turbines = sum(f["properties"]["turbines"] for f in features)
    print(f"{len(features)} Hüllen, {total_ha} ha, {total_turbines} Anlagen darin "
          f"({skipped_small} Splitter < {MIN_HA} ha verworfen)")
    for name in sorted(counters, key=lambda n: -counters[n]):
        ha = round(sum(f["properties"]["area_ha"] for f in features
                       if f["properties"]["bundesland"] == name), 1)
        wka = sum(f["properties"]["turbines"] for f in features
                  if f["properties"]["bundesland"] == name)
        print(f"  {name:20s} {counters[name]:3d} Hüllen  {ha:9.1f} ha  {wka:4d} Anlagen")

    with open(OUT, "w") as fh:
        json.dump({"type": "FeatureCollection", "features": features}, fh, separators=(",", ":"))
    print(f"→ {OUT} ({os.path.getsize(OUT) // 1024} KB)")


if __name__ == "__main__":
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    main()
