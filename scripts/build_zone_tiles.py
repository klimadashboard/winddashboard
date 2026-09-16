#!/usr/bin/env python3
"""Baut scripts/raster/windkraft_possible_zones.mbtiles aus den Potenzialflächen.

Warum als Kacheln
-----------------
`possible_zones.geojson` sind 15 MB und wurden bei jedem Seitenaufruf komplett
geladen — über eine Vercel-Funktion, was dort auf das Origin-Transfer-Kontingent
zählt. Als Vektorkacheln auf dem eigenen Tileserver fällt das bei Vercel ganz weg,
und die Karte lädt nach Ausschnitt statt erst nach einem 15-MB-Download.

Der Layer heißt `possible_zones` — gleich dem Dateinamen, wie bei den Bändern.
`zone_id` bleibt als Eigenschaft erhalten und wird in der App als `promoteId`
verwendet: ohne stabile Feature-ID bricht der Hover-Zustand an Kachelgrenzen.

Aufruf
------
    python scripts/build_zone_tiles.py
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "geodata/possible_zones.geojson")
OUT = os.path.join(REPO, "scripts/raster/windkraft_possible_zones.mbtiles")
LAYER = "possible_zones"

TIPPECANOE_OPTS = [
    "--force",
    "--minimum-zoom=5",
    "--maximum-zoom=14",
    # Die Flächen müssen auf jeder Zoomstufe vollständig sein — eine Zone, die
    # in der Übersicht fehlt, sieht aus wie "hier ist kein Potenzial".
    "--no-tile-size-limit",
    "--no-feature-limit",
    "--simplification=4",
    "--detect-shared-borders",
    "--no-tile-stats",
]


def main() -> None:
    if not shutil.which("tippecanoe"):
        sys.exit("tippecanoe nicht gefunden (brew install tippecanoe)")
    if not os.path.exists(SRC):
        sys.exit(f"Fehlt: {SRC} — erst extract_possible_zones.py laufen lassen")

    with open(SRC, encoding="utf-8") as fh:
        source_count = len(json.load(fh)["features"])

    args = ["tippecanoe", "--output", OUT, *TIPPECANOE_OPTS, "-l", LAYER, SRC]
    print(f"{source_count} Flächen → {OUT}", flush=True)
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

    print(f"\n{os.path.getsize(OUT) / 1e6:.1f} MB, {tiles:,} Kacheln, "
          f"Zoom {meta.get('minzoom')}–{meta.get('maxzoom')}")
    for layer in layers:
        fields = ", ".join(sorted(layer.get("fields", {})))
        print(f"   {layer['id']}: {fields}")

    names = [layer["id"] for layer in layers]
    if names != [LAYER] or tiles == 0:
        sys.exit(f"FEHLER: erwartet genau Layer '{LAYER}' mit Kacheln, "
                 f"bekommen {names} / {tiles} Kacheln")
    if "zone_id" not in layers[0].get("fields", {}):
        sys.exit("FEHLER: zone_id fehlt in den Kacheln — promoteId würde brechen")
    print("\nOK — bereit zum Hochladen.")


if __name__ == "__main__":
    main()
