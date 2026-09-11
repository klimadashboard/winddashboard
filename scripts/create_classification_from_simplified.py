#!/usr/bin/env python3
"""
Derive classification.tif (single-band) from the Abschichtung raster.

Die Zuordnung läuft über **Bandnamen**, nicht über Bandnummern: widmung_v1 hat
54 Bänder, widmung_v2 nur 44 und in anderer Reihenfolge. Namen, die im jeweiligen
Raster fehlen, werden übersprungen — dieselbe Tabelle bedient damit beide
Lieferungen.

Klassencodes (stabil, weil sie in Legende, Kacheln und Tooltip stecken):

   1 Schutzgebiet            7 Hangneigung >15°      12 Allgemeine Gebäude (25 m)
   2 Siedlungsabstand        8 Seehöhe >2.500 m      13 Gebäude an Seilbahnen (50 m)
   3 Haus im Grünen (750 m)  9 (stillgelegt)         14 Geeignet
   4 Sperrzone              10 (stillgelegt)         15 Nicht-Wohn-Hüllen (25 m)
   5 Verkehrsweg (150 m)    11 Wind zu gering        16 Größere Gewässer
   6 Eisenbahn (150 m)

Mit widmung_v2 stillgelegt: **9** (Wichtige Objekte) und **10** (Freileitung
380/400 kV). Beide Kriterien gibt es in der Lieferung nicht mehr — `POWER_LINES`
steht im Manifest ausdrücklich auf "kein Ausschlusskriterium". Die Nummern werden
nicht neu vergeben, damit alte Kacheln und Screenshots interpretierbar bleiben.
Neu hinzugekommen: **15** und **16**.

Priorität: letzter Treffer gewinnt (weiter unten in RULES = höhere Priorität).
  0 = außerhalb Österreichs / kein Datum

Ausgabe:
  scripts/raster/classification.tif — einbandig uint8, CRS und Auflösung wie die Quelle
"""

import json
import os
import sys
import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.warp import transform_geom

SRC_CANDIDATES = [
    "scripts/raster/abschichtung.tif",
    "scripts/raster/osm_wka_distance_zones_widmung.tif",
]
SRC = next((p for p in SRC_CANDIDATES if os.path.exists(p)), SRC_CANDIDATES[-1])
OUT = "scripts/raster/classification.tif"
AUSTRIA_OUTLINE = "geodata/austria_outline.geojson"

# Bandname → Klassencode, aufsteigend nach Priorität. Namen aus beiden
# Lieferungen stehen nebeneinander; was im Raster fehlt, wird übersprungen.
RULES = [
    ("geography_wind_too_low",            11),
    ("geography_elevation_too_high",       8),
    ("geography_slope_too_steep",          7),
    ("geography_water_bodies",            16),   # nur widmung_v2
    ("general_buildings_buffer",          12),
    ("nonresidential_hulls_buffer",       15),   # nur widmung_v2
    ("cableway_buildings_buffer",         13),
    ("power_380_400kv",                   10),   # nur widmung_v1
    ("rail_main",                          6),
    ("road_motorway_trunk",                5),
    ("road_federal_state",                 5),
    ("cableway_people_150m",               5),
    ("important_objects_buffer",           9),   # nur widmung_v1
    ("military_restricted_area",           4),
    ("airport_area",                       4),   # widmung_v1
    ("airport_area_major",                 4),   # widmung_v2
    ("airport_lateral_check_6km",          4),   # widmung_v1
    ("airport_runway_corridor_5km",        4),   # widmung_v2
    ("osm_nature_protection_areas",        1),
    ("nature_protection_areas",            1),
    ("haeuser_im_gruenen_buffer",          3),   # widmung_v1
    ("haeuser_im_gruenen",                 3),   # widmung_v2 (Zone, nicht _source)
    ("settlement_widmung_buffer",          2),   # widmung_v1
    ("settlement_buffer",                  2),   # widmung_v2
    ("available_cleaned_min_10ha_default", 14),  # widmung_v1
    ("available_cleaned_min_10ha",        14),
]


def main():
    print(f"Reading {SRC} …")
    with rasterio.open(SRC) as src:
        profile = src.profile.copy()
        height, width = src.height, src.width

        classification = np.zeros((height, width), dtype=np.uint8)

        names = list(src.descriptions)
        missing = []
        for band_name, code in RULES:
            if band_name not in names:
                missing.append(band_name)
                continue
            band_idx = names.index(band_name) + 1
            print(f"  Band {band_idx:02d} ({band_name}) → code {code}")
            data = src.read(band_idx)
            classification[data == 1] = code
        if missing:
            print(f"\n  Nicht in dieser Lieferung: {', '.join(missing)}")

        # Mask to Austria's real border. The source's wind-too-low band is not
        # clipped to the country outline (it flags "missing data" wherever the
        # Global Wind Atlas grid has none, which is most of the surrounding
        # rectangular padding) — without this, ~193M padding pixels would be
        # painted as "wind too low, excluded" instead of staying code 0.
        print(f"\nMasking to {AUSTRIA_OUTLINE} …")
        with open(AUSTRIA_OUTLINE) as f:
            outline_feature = json.load(f)
        outline_native = transform_geom("EPSG:4326", src.crs, outline_feature["geometry"])
        austria_mask = rasterize(
            [(outline_native, 1)],
            out_shape=(height, width),
            transform=src.transform,
            fill=0,
            dtype=np.uint8,
        )
        classification[austria_mask == 0] = 0

    profile.update(
        count=1,
        dtype=np.uint8,
        compress="deflate",
        predictor=2,
        nodata=None,
    )

    print(f"\nWriting {OUT} …")
    with rasterio.open(OUT, "w", **profile) as dst:
        dst.write(classification, 1)

    # Summary
    codes, counts = np.unique(classification, return_counts=True)
    total = classification.size
    print("\nBand 1 code distribution:")
    for c, n in zip(codes, counts):
        print(f"  code {c:2d}: {n:>12,d} px  ({100*n/total:5.1f}%)")
    print(f"\n✓ {OUT} written")


if __name__ == "__main__":
    import os
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    if not os.path.exists(SRC):
        sys.exit(f"Source not found: {os.path.abspath(SRC)}")
    main()
