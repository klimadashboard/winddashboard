#!/usr/bin/env python3
"""
Compute each Bundesland's total area in hectares from classification.tif
(codes 1-14 = inside Austria's outline; code 0 = outside/no data), by
rasterizing geodata/austria_states.geojson per state and summing pixels.

Used to normalize the Scrollytelling "Potentialflächen"/"Zonierungsflächen"
Bundesland bars against each state's own area instead of Niederösterreich's
potential hectares (see PIPELINE.md, Scrollytelling.svelte BUNDESLAENDER).

Usage:
  python scripts/compute_bundesland_areas.py
"""

import json
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import rasterize
from rasterio.warp import transform_geom

CLASSIFICATION = "scripts/raster/classification.tif"
STATES = "geodata/austria_states.geojson"


def main():
    with rasterio.open(CLASSIFICATION) as src:
        classification = src.read(1)
        transform = src.transform
        crs = src.crs
        pixel_area_ha = abs(transform.a * transform.e) / 10_000

    inside_austria = classification != 0

    with open(STATES) as f:
        states = json.load(f)["features"]

    results = []
    for feat in states:
        name = feat["properties"]["NAME_1"]
        geom_native = transform_geom("EPSG:4326", crs, feat["geometry"])
        state_mask = rasterize(
            [(geom_native, 1)],
            out_shape=classification.shape,
            transform=transform,
            fill=0,
            dtype=np.uint8,
        )
        px = int(np.sum((state_mask == 1) & inside_austria))
        results.append((name, px, round(px * pixel_area_ha)))

    results.sort(key=lambda r: -r[2])
    total = 0
    print(f"{'Bundesland':<18} {'px':>12} {'ha':>12}")
    for name, px, ha in results:
        total += ha
        print(f"{name:<18} {px:>12,d} {ha:>12,d}")
    print(f"{'TOTAL':<18} {'':>12} {total:>12,d}")


if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent.parent)
    main()
