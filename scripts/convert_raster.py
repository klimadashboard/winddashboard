#!/usr/bin/env python3
"""
Convert classification.tif → RGBA GeoTIFF (EPSG:3857) → MBTiles for TileServer GL.

Prerequisites:
    pip install rasterio numpy
    gdal tools: gdalwarp, gdal2tiles.py
    mb-util:    pip install mbutil  (or: git clone https://github.com/mapbox/mbutil)

Usage:
    cd /path/to/windkraft_export_v1/raster
    python ../../windkraft/scripts/convert_raster.py

Output:
    classification_rgba_3857.tif   — RGBA GeoTIFF reprojected to EPSG:3857
    tiles/                         — XYZ PNG tile tree (zoom 6–13)
    windkraft_classification.mbtiles — packaged MBTiles for TileServer GL

TileServer GL setup:
    1. Copy windkraft_classification.mbtiles to your TileServer GL data directory
    2. In config.json add under "data":
          "windkraft-classification": { "mbtiles": "windkraft_classification.mbtiles" }
    3. Tile URL: https://tiles.klimadashboard.org/tiles/windkraft-classification/{z}/{x}/{y}.png
"""

import os
import subprocess
import sys
import numpy as np

try:
    import rasterio
    from rasterio.warp import calculate_default_transform, reproject, Resampling, transform_bounds
    from rasterio.crs import CRS
    from rasterio.transform import from_bounds as transform_from_bounds
except ImportError:
    sys.exit("rasterio not found. Run: pip install rasterio numpy")

# Auto-install lightweight deps if missing
for pkg, imp in [("mercantile", "mercantile"), ("Pillow", "PIL")]:
    try:
        __import__(imp)
    except ImportError:
        print(f"Installing {pkg} …")
        subprocess.run([sys.executable, "-m", "pip", "install", pkg], check=True)

import mercantile
from PIL import Image

# ---------------------------------------------------------------------------
# Color map: code → (R, G, B, A)
#
# Kept in sync with src/lib/config/legend.ts and Map.svelte.
# Palette logic:
#   Suitable (14)       → blue family, alpha 220 – matches vector fill colours
#   Wind (11)           → slate grey,  alpha 150 – "not enough energy"
#   Terrain (7-8)       → stone grey,  alpha 145-155 – topographic exclusion
#   Exclusion:
#     Nature (1)              → green-400,  alpha 150
#     Settlement (2,3,9,12,13) → orange spectrum, alpha 130-150
#     Safety (4)               → red-500,    alpha 150
#     Roads/rail (5,6,10)      → yellow/amber, alpha 140
# ---------------------------------------------------------------------------
COLORMAP = {
    0:  (0,   0,   0,   0),    # transparent (outside)
    1:  (74,  222, 128, 150),  # Schutzgebiet             – green-400
    2:  (249, 115, 22,  150),  # Siedlungsabstand          – orange-500
    3:  (251, 146, 60,  140),  # Haus im Grünen            – orange-400
    4:  (239, 68,  68,  150),  # Sperrzone                 – red-500
    5:  (250, 204, 21,  140),  # Verkehrsweg (150 m)       – yellow-400
    6:  (234, 179, 8,   140),  # Eisenbahn (150 m)         – yellow-600
    7:  (168, 162, 158, 155),  # Hangneigung >15°          – stone-400
    8:  (214, 211, 209, 145),  # Seehöhe >2500 m           – stone-300
    9:  (154, 52,  18,  150),  # Wichtige Objekte (250 m)  – orange-900
    10: (251, 191, 36,  140),  # Freileitung 380/400 kV    – amber-400
    11: (148, 163, 184, 150),  # Wind zu gering            – slate-400
    12: (253, 186, 116, 130),  # Allgemeine Gebäude (25 m) – orange-300
    13: (194, 65,  12,  140),  # Gebäude an Seilbahnen (50 m) – orange-700
    14: (147, 197, 253, 220),  # Geeignet                  – blue-300
}

INPUT_TIF  = "classification.tif"
RGBA_TIF   = "classification_rgba_3857.tif"
TILES_DIR  = "tiles"
MBTILES    = "windkraft_classification.mbtiles"
ZOOM_RANGE = "6-13"

def make_rgba():
    print(f"Reading {INPUT_TIF} …")
    with rasterio.open(INPUT_TIF) as src:
        data = src.read(1)  # band 1: classification codes
        src_crs   = src.crs
        src_trans = src.transform
        src_width = src.width
        src_height = src.height

    print("Applying color map …")
    r = np.zeros_like(data, dtype=np.uint8)
    g = np.zeros_like(data, dtype=np.uint8)
    b = np.zeros_like(data, dtype=np.uint8)
    a = np.zeros_like(data, dtype=np.uint8)

    for code, (rv, gv, bv, av) in COLORMAP.items():
        mask = data == code
        r[mask] = rv
        g[mask] = gv
        b[mask] = bv
        a[mask] = av

    dst_crs = CRS.from_epsg(3857)
    transform_3857, width_3857, height_3857 = calculate_default_transform(
        src_crs, dst_crs, src_width, src_height,
        left=src_trans.c,
        top=src_trans.f,
        right=src_trans.c + src_trans.a * src_width,
        bottom=src_trans.f + src_trans.e * src_height,
    )

    print(f"Writing {RGBA_TIF} (EPSG:3857, {width_3857}×{height_3857}) …")
    with rasterio.open(
        RGBA_TIF, 'w',
        driver='GTiff',
        height=height_3857,
        width=width_3857,
        count=4,
        dtype=np.uint8,
        crs=dst_crs,
        transform=transform_3857,
        compress='deflate',
    ) as dst:
        for i, band_data in enumerate([r, g, b, a], 1):
            reprojected = np.zeros((height_3857, width_3857), dtype=np.uint8)
            reproject(
                source=band_data,
                destination=reprojected,
                src_transform=src_trans,
                src_crs=src_crs,
                dst_transform=transform_3857,
                dst_crs=dst_crs,
                resampling=Resampling.nearest,
            )
            dst.write(reprojected, i)

    print(f"✓ {RGBA_TIF} written")


TILE_SIZE = 256

def make_tiles():
    zoom_min, zoom_max = map(int, ZOOM_RANGE.split("-"))
    print(f"\nGenerating tiles (zoom {zoom_min}–{zoom_max}) with rasterio + mercantile …")

    with rasterio.open(RGBA_TIF) as src:
        # Bounds in WGS84 for mercantile
        west, south, east, north = transform_bounds(src.crs, "EPSG:4326", *src.bounds)

        all_tiles = []
        for z in range(zoom_min, zoom_max + 1):
            all_tiles.extend(mercantile.tiles(west, south, east, north, zooms=z))

        total = len(all_tiles)
        print(f"  {total} tiles to generate …")
        done = skipped = 0

        for tile in all_tiles:
            xy = mercantile.xy_bounds(tile)
            dst_transform = transform_from_bounds(
                xy.left, xy.bottom, xy.right, xy.top, TILE_SIZE, TILE_SIZE
            )

            # Reproject all 4 bands into a (4, 256, 256) array
            data = np.zeros((4, TILE_SIZE, TILE_SIZE), dtype=np.uint8)
            for band in range(4):
                reproject(
                    source=rasterio.band(src, band + 1),
                    destination=data[band],
                    dst_transform=dst_transform,
                    dst_crs="EPSG:3857",
                    resampling=Resampling.nearest,
                )

            # Skip fully transparent tiles
            if data[3].max() == 0:
                skipped += 1
                done += 1
                continue

            tile_path = os.path.join(TILES_DIR, str(tile.z), str(tile.x), f"{tile.y}.png")
            os.makedirs(os.path.dirname(tile_path), exist_ok=True)
            Image.fromarray(data.transpose(1, 2, 0), "RGBA").save(tile_path, "PNG")
            done += 1

            if done % 200 == 0:
                print(f"  {done}/{total} ({skipped} empty skipped) …", end="\r")

    print(f"\n✓ Tiles written to {TILES_DIR}/  ({total - skipped} non-empty, {skipped} empty skipped)")


def make_mbtiles():
    print(f"\nPackaging {MBTILES} with mb-util …")
    if os.path.exists(MBTILES):
        os.remove(MBTILES)
    cmd = ["mb-util", "--image_format=png", TILES_DIR, MBTILES]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("mb-util failed (is it installed? pip install mbutil):\n", result.stderr)
        print("You can also use: python -m mbutil", TILES_DIR, MBTILES)
        return
    _write_mbtiles_metadata()
    print(f"✓ {MBTILES} ready – upload to TileServer GL data directory")


def _write_mbtiles_metadata():
    import sqlite3
    from rasterio.warp import transform_bounds
    with rasterio.open(RGBA_TIF) as src:
        w, s, e, n = transform_bounds(src.crs, "EPSG:4326", *src.bounds)
    cx, cy = (w + e) / 2, (s + n) / 2
    zoom_min, zoom_max = ZOOM_RANGE.split("-")
    meta = [
        ("name",        "windkraft-classification"),
        ("format",      "png"),
        ("bounds",      f"{w:.6f},{s:.6f},{e:.6f},{n:.6f}"),
        ("center",      f"{cx:.6f},{cy:.6f},{zoom_min}"),
        ("minzoom",     zoom_min),
        ("maxzoom",     zoom_max),
        ("type",        "overlay"),
        ("description", "Windkraft-Abschichtung Österreich – Klassifikationsraster"),
        ("version",     "1"),
    ]
    con = sqlite3.connect(MBTILES)
    con.executemany("INSERT OR REPLACE INTO metadata (name, value) VALUES (?, ?)", meta)
    con.commit()
    con.close()
    print("✓ MBTiles metadata written")


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/raster")
    print(f"Working in: {os.getcwd()}\n")

    if not os.path.exists(INPUT_TIF):
        sys.exit(f"Input file not found: {os.path.abspath(INPUT_TIF)}")

    make_rgba()
    make_tiles()
    make_mbtiles()

    print("\nDone! Next steps:")
    print(f"  1. scp {MBTILES} user@tileserver:/data/")
    print( "  2. Add to TileServer GL config.json:")
    print( '       "windkraft-classification": { "mbtiles": "windkraft_classification.mbtiles" }')
    print( "  3. Restart TileServer GL")
    print( "  4. Verify: https://tiles.klimadashboard.org/tiles/windkraft-classification/8/136/89.png")
