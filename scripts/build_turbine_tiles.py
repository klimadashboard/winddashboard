#!/usr/bin/env python3
"""Baut scripts/raster/windkraft_turbines.mbtiles aus den Bestandsanlagen.

Warum als Kacheln
-----------------
`existing_turbines.geojson` darf nicht als Datensatz weitergegeben werden —
die Standorte zu *zeigen* ist erlaubt, die Datei selbst herauszugeben nicht.
Als GeoJSON unter `static/data/` lag sie im öffentlichen Repository und wurde
bei jedem Seitenaufruf am Stück ausgeliefert, also faktisch verteilt.

Vektorkacheln lösen genau diesen Punkt: der Browser bekommt nur den sichtbaren
Ausschnitt, die Quelldatei verlässt den eigenen Rechner nicht und liegt nicht
mehr im Repository. Die Karte zeigt dieselben Punkte wie vorher.

Der Layer heißt `existing_turbines` — gleich dem Dateinamen, wie bei den
Bändern und den Potenzialflächen.

Warum ohne Ausdünnung
---------------------
`-r1` schaltet tippecanoes Punktausdünnung ab. Ohne das verschwinden auf den
kleinen Zoomstufen gerade die dicht stehenden Anlagen im Weinviertel und im
Burgenland — also dort, wo die Karte zeigen soll, dass es viele sind. Bei 1.396
Punkten kostet das nichts: die fertigen Kacheln sind ein halbes Megabyte.

Aufruf
------
    python scripts/build_turbine_tiles.py
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, "geodata/existing_turbines.geojson")
OUT = os.path.join(REPO, "scripts/raster/windkraft_turbines.mbtiles")
LAYER = "existing_turbines"

# Österreich großzügig umschlossen — dient nur dazu, vertauschte Koordinaten
# zu erkennen (gleiche Box wie in build_region_stats.py).
AT_BBOX = (9.0, 46.0, 17.5, 49.5)

TIPPECANOE_OPTS = [
    "--force",
    # Ohne diese beiden schreibt tippecanoe den absoluten Pfad der Quelldatei
    # in die Metadaten — und der Tileserver gibt sie als TileJSON öffentlich
    # aus. Dort stünde dann der Benutzername des Rechners, auf dem gebaut wurde.
    "--name=windkraft_turbines",
    "--description=Bestehende Windkraftanlagen in Österreich",
    # Zoom 4 wie bei den Potenzialflächen: die Karte erlaubt auf schmalen
    # Fenstern minZoom 4.5, und unterhalb der Quell-Minzoomstufe zeichnet
    # MapLibre kommentarlos nichts.
    "--minimum-zoom=4",
    "--maximum-zoom=14",
    # Jede Anlage auf jeder Zoomstufe — siehe Modulkommentar.
    "-r1",
    "--no-tile-size-limit",
    "--no-feature-limit",
    "--no-tile-stats",
]


def sanitize(raw: dict) -> tuple[list, int, int]:
    """Repariert die bekannten Koordinatenfehler der Lieferung.

    Zwei Fehlerbilder, beide beim Anbieter gemeldet (siehe
    build_region_stats.py, das dieselbe Korrektur für die Gemeindezahlen
    vornimmt): einige Anlagen liegen auf [0, 0], bei anderen sind Länge und
    Breite vertauscht.

    Für die Kacheln zählt das doppelt: tippecanoe leitet die Bounds aus den
    Koordinaten ab, und ein einziger Punkt auf [0, 0] spannt sie quer über den
    Atlantik. MapLibre fordert dann Kacheln für ein Gebiet an, in dem nichts
    liegt, und die TileJSON behauptet eine Ausdehnung, die es nicht gibt.
    """
    kept, swapped, dropped = [], 0, 0
    for feat in raw["features"]:
        lon, lat = feat["geometry"]["coordinates"][:2]
        if lon == 0 and lat == 0:
            dropped += 1
            continue
        in_at = AT_BBOX[0] <= lon <= AT_BBOX[2] and AT_BBOX[1] <= lat <= AT_BBOX[3]
        flipped = AT_BBOX[0] <= lat <= AT_BBOX[2] and AT_BBOX[1] <= lon <= AT_BBOX[3]
        if not in_at and flipped:
            feat["geometry"]["coordinates"] = [lat, lon]
            swapped += 1
        kept.append(feat)
    return kept, swapped, dropped


def main() -> None:
    if not shutil.which("tippecanoe"):
        sys.exit("tippecanoe nicht gefunden (brew install tippecanoe)")
    if not os.path.exists(SRC):
        sys.exit(f"Fehlt: {SRC} — die Lieferung des Anbieters, nicht im Repository")

    with open(SRC, encoding="utf-8") as fh:
        raw = json.load(fh)
    source_count = len(raw["features"])
    features, swapped, dropped = sanitize(raw)
    if swapped or dropped:
        print(f"  {swapped} vertauschte Koordinaten korrigiert, "
              f"{dropped} Anlagen ohne Position ausgelassen")

    with tempfile.TemporaryDirectory() as tmp:
        clean = os.path.join(tmp, "turbines_clean.geojson")
        with open(clean, "w", encoding="utf-8") as fh:
            json.dump({"type": "FeatureCollection", "features": features}, fh)

        args = ["tippecanoe", "--output", OUT, *TIPPECANOE_OPTS, "-l", LAYER, clean]
        print(f"{source_count} Anlagen, {len(features)} mit Position → {OUT}", flush=True)
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

    # Die Tooltip-Felder müssen ankommen, sonst steht später eine leere Karte
    # voller Punkte ohne Angaben da.
    fields = layers[0].get("fields", {})
    for needed in ("gemeinde", "power_kw", "commissioned"):
        if needed not in fields:
            sys.exit(f"FEHLER: {needed} fehlt in den Kacheln")
    print("\nOK — bereit zum Hochladen.")


if __name__ == "__main__":
    main()
