#!/usr/bin/env python3
"""
Derive classification.tif (single-band, codes 0–14) from osm_wka_distance_zones_widmung.tif.

Source bands (54-band raster, "widmung_v1" pipeline, EPSG:31287, 25 m). Only the
default (Bundesland-specific) settlement distance is used here — the 6 settlement-
distance variants (bands 31–54) feed the interactive slider instead, via
extract_possible_zones.py / extract_band_geojson.py.

  02 settlement_widmung_buffer     → code 2  (Siedlungsabstand)
  04 important_objects_buffer      → code 9  (Wichtige Objekte, 250 m)
  06 cableway_buildings_buffer     → code 13 (Gebäude an Seilbahnen, 50 m)
  08 haeuser_im_gruenen_buffer     → code 3  (Haus im Grünen, 750 m)
  10 general_buildings_buffer      → code 12 (Allgemeine Gebäude, 25 m)
  11 power_380_400kv               → code 10 (Freileitung)
  12 road_motorway_trunk           → code 5  (Verkehrsweg 150 m)
  13 road_federal_state            → code 5  (Verkehrsweg 150 m)
  14 rail_main                     → code 6  (Eisenbahn 150 m)
  15 cableway_people_150m          → code 5  (Verkehrsweg 150 m)
  16 military_restricted_area      → code 4  (Sperrzone)
  17 airport_area                  → code 4  (Sperrzone)
  18 airport_lateral_check_6km     → code 4  (Sperrzone)
  19 nature_protection_areas       → code 1  (Schutzgebiet)
  20 osm_nature_protection_areas   → code 1  (Schutzgebiet)
  21 geography_slope_too_steep     → code 7  (Hangneigung >15°)
  22 geography_elevation_too_high  → code 8  (Seehöhe >2500 m)
  23 geography_wind_too_low        → code 11 (Wind zu gering, <150 W/m²)
  29 available_cleaned_min_10ha    → code 14 (geeignet, Default-Variante)

Priority: last-write wins (highest listed = highest priority).
  0 = outside Austria / no data (nothing set)

Output:
  scripts/raster/classification.tif  — single-band uint8, same CRS/resolution as source
"""

import json
import sys
import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.warp import transform_geom

SRC = "scripts/raster/osm_wka_distance_zones_widmung.tif"
OUT = "scripts/raster/classification.tif"
AUSTRIA_OUTLINE = "geodata/austria_outline.geojson"

# Band index (1-based) → output classification code, in ascending priority
# (lower-priority entries are written first and can be overwritten)
RULES = [
    (23, 11),   # geography_wind_too_low        → Wind zu gering
    (22,  8),   # geography_elevation_too_high  → Seehöhe >2500 m
    (21,  7),   # geography_slope_too_steep     → Hangneigung >15°
    (10, 12),   # general_buildings_buffer      → Allgemeine Gebäude
    ( 6, 13),   # cableway_buildings_buffer     → Gebäude an Seilbahnen
    (11, 10),   # power_380_400kv               → Freileitung
    (14,  6),   # rail_main                     → Eisenbahn
    (12,  5),   # road_motorway_trunk           → Verkehrsweg
    (13,  5),   # road_federal_state            → Verkehrsweg
    (15,  5),   # cableway_people_150m          → Verkehrsweg
    ( 4,  9),   # important_objects_buffer      → Wichtige Objekte
    (16,  4),   # military_restricted_area      → Sperrzone
    (17,  4),   # airport_area                  → Sperrzone
    (18,  4),   # airport_lateral_check_6km     → Sperrzone
    (20,  1),   # osm_nature_protection_areas   → Schutzgebiet
    (19,  1),   # nature_protection_areas       → Schutzgebiet
    ( 8,  3),   # haeuser_im_gruenen_buffer     → Haus im Grünen
    ( 2,  2),   # settlement_widmung_buffer     → Siedlungsabstand
    (29, 14),   # available_cleaned_min_10ha    → geeignet (Default-Variante)
]


def main():
    print(f"Reading {SRC} …")
    with rasterio.open(SRC) as src:
        profile = src.profile.copy()
        height, width = src.height, src.width

        classification = np.zeros((height, width), dtype=np.uint8)

        for band_idx, code in RULES:
            band_name = src.descriptions[band_idx - 1]
            print(f"  Band {band_idx:02d} ({band_name}) → code {code}")
            data = src.read(band_idx)
            classification[data == 1] = code

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
