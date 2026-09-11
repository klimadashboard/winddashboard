#!/usr/bin/env python3
"""Baut scripts/raster/windkraft_exclusion_bands.mbtiles aus den Band-GeoJSONs.

Warum ein Skript und kein Shell-Einzeiler
-----------------------------------------
Die Layerliste hat 17 Einträge à zwei Argumenten. Sie in einer Shell-Variablen
zusammenzubauen und unquotiert zu expandieren ist fehleranfällig: je nach Shell
wird nicht in Wörter zerlegt, und tippecanoe bekommt die gesamte Liste als einen
einzigen Dateinamen ("File name too long"). `mapfile` wiederum ist ein
bash-Builtin und existiert in zsh nicht. Hier wird die Argumentliste in Python
gebaut und ohne Shell an tippecanoe übergeben — damit gibt es kein Quoting.

Die Layerauswahl kommt aus dem Manifest, dieselbe wie in
generate_bands_config.py und extract_band_geojson.py.

Aufruf
------
    python scripts/build_band_tiles.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sqlite3
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "scripts"))
from generate_bands_config import MANIFEST, select_bands  # noqa: E402

GEODATA = os.path.join(REPO, "geodata")
OUT = os.path.join(REPO, "scripts/raster/windkraft_exclusion_bands.mbtiles")

TIPPECANOE_OPTS = [
    "--force",
    "--minimum-zoom=5",
    "--maximum-zoom=14",
    "--no-tile-size-limit",
    "--simplification=4",
    "--detect-shared-borders",
    "--no-tile-stats",
]


def main() -> None:
    if not shutil.which("tippecanoe"):
        sys.exit("tippecanoe nicht gefunden (brew install tippecanoe)")

    with open(MANIFEST, encoding="utf-8") as fh:
        manifest = json.load(fh)
    bands = select_bands(manifest)

    args = ["tippecanoe", "--output", OUT, *TIPPECANOE_OPTS]
    missing = []
    for b in bands:
        path = os.path.join(GEODATA, f"{b['name']}.geojson")
        if not os.path.exists(path):
            missing.append(b["name"])
            continue
        args += ["-L", f"{b['name']}:{path}"]
    if missing:
        sys.exit(f"GeoJSONs fehlen — erst extract_band_geojson.py laufen lassen: {missing}")

    print(f"{len(bands)} Layer → {OUT}", flush=True)
    result = subprocess.run(args)
    if result.returncode != 0:
        sys.exit(f"tippecanoe endete mit Code {result.returncode}")

    # Ergebnis prüfen, statt der Rückgabe zu vertrauen: ein Lauf ohne gültige
    # Geometrien endet ebenfalls mit Code 0 und hinterlässt eine leere Datei.
    con = sqlite3.connect(OUT)
    meta = dict(con.execute("select name, value from metadata").fetchall())
    layers = json.loads(meta.get("json", "{}")).get("vector_layers", [])
    tiles = con.execute("select count(*) from tiles").fetchone()[0]
    con.close()

    size_mb = os.path.getsize(OUT) / 1e6
    print(f"\n{size_mb:.1f} MB, {tiles:,} Kacheln, {len(layers)} Layer, "
          f"Zoom {meta.get('minzoom')}–{meta.get('maxzoom')}")
    for layer in layers:
        print(f"   {layer['id']}")

    if len(layers) != len(bands) or tiles == 0:
        sys.exit(f"FEHLER: erwartet {len(bands)} Layer mit Kacheln, "
                 f"bekommen {len(layers)} Layer / {tiles} Kacheln")
    print("\nOK — bereit zum Hochladen.")


if __name__ == "__main__":
    main()
