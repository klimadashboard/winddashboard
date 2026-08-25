#!/usr/bin/env python3
"""
Add Steiermark + Salzburg zoning polygons to geodata/official_zoning.geojson.

geodata/official_zoning.geojson historically only contained Niederösterreich's
official Windkraft-Eignungszonen (richly attributed: zoning_id, name, legal_basis,
effective_from, communities, source_url — vectorized from the NÖ Sektorales
Raumordnungsprogramm directly, not from this repo's raster pipeline).

The current source raster (osm_wka_distance_zones_widmung.tif) additionally embeds
Steiermark (SAPRO Windenergie) and Salzburg zoning as part of its band 30
("official_wind_zoning") reference layer — see README §4.7 / methodik page. This
script extracts ONLY the Steiermark/Salzburg polygons from that band (NÖ is left
untouched, since the existing curated NÖ dataset is more precise and richly
attributed than a raster-derived re-extraction would be) and appends them.

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

SRC = "scripts/raster/osm_wka_distance_zones_widmung.tif"
STATES = "geodata/austria_states.geojson"
OUT = "geodata/official_zoning.geojson"

BAND_NAME = "official_wind_zoning"
MIN_HA = 1.0
SIMPLIFY_TOL = 0.00005  # degrees (~5 m), matches extract_band_geojson.py

# Bundesländer to add from the raster (Niederösterreich is intentionally excluded —
# the existing curated dataset for NÖ stays authoritative).
ADD_STATES = {
    "Steiermark": "SAPRO Windenergie Steiermark 2013",
    "Salzburg": "Zonierung Salzburg (digitale Zonengeometrien)",
}


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
        prefix = {"Steiermark": "STMK", "Salzburg": "SBG"}[bundesland]
        new_features.append({
            "type": "Feature",
            "geometry": mapping(geom),
            "properties": {
                "zoning_id": f"{prefix}-{counters[bundesland]:02d}",
                "bundesland": bundesland,
                "area_ha": area_ha,
                "legal_basis": ADD_STATES[bundesland],
                "source": "raster-derived (osm_wka_distance_zones_widmung.tif, Band 30)",
            },
        })

    print(f"Extracted {len(new_features)} polygons ({sum(counters.values())} total): "
          f"{ {k: v for k, v in counters.items()} }")

    existing = json.load(open(OUT))
    existing["features"].extend(new_features)

    with open(OUT, "w") as f:
        json.dump(existing, f, separators=(",", ":"))
    print(f"→ {OUT} now has {len(existing['features'])} features "
          f"({Path(OUT).stat().st_size // 1024} KB)")


if __name__ == "__main__":
    import os
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    main()
