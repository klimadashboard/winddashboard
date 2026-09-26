#!/usr/bin/env python3
"""Kopiert die ausgelieferten Geodaten nach static/data/.

Warum
-----
Bis September 2026 liefen diese Dateien über die Route `/data/[name]`, also über
eine Serverless-Funktion. Bei Vercel zählt jedes Byte, das eine Funktion an das
Edge-Netz schickt, auf das Origin-Transfer-Kontingent — und das waren rund 4 MB
je Seitenaufruf, zusätzlich zu den 15 MB Potenzialflächen (die inzwischen als
Vektorkacheln auf dem eigenen Tileserver liegen).

Statische Dateien liegen dagegen im Edge-Netz und erzeugen überhaupt keinen
Origin-Transfer. Der einzige Grund für die Funktion war ein Hotlink-Schutz über
den Origin-Header; der ist entfallen, weil er ohne Origin-Header ohnehin wirkungslos
war und gleichzeitig jedes CDN-Caching verhinderte. Die Daten sind offen.

Endung `.json`, nicht `.geojson`
--------------------------------
GeoJSON *ist* JSON, und MapLibre wertet den Content-Type nicht aus. Aber CDNs
leiten Content-Type und automatische Komprimierung aus der Dateiendung ab.
`.geojson` ist dort meist unbekannt — das Ergebnis wäre `application/octet-stream`
und unkomprimierte Auslieferung. Mit `.json` sind beide Punkte erledigt.

Läuft automatisch vor jedem Build (`npm run build`), siehe package.json.
"""

from __future__ import annotations

import os
import shutil
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEODATA = os.path.join(REPO, "geodata")
TARGET = os.path.join(REPO, "static/data")

# Genau die Dateien, welche die App lädt. possible_zones fehlt bewusst: die
# kommen als Vektorkacheln vom Tileserver (scripts/build_zone_tiles.py).
SERVED = [
    "austria_outline.geojson",
    "exclusion_schutz.geojson",
    "exclusion_siedlung.geojson",
    "exclusion_sonstige.geojson",
    "exclusion_wind.geojson",
    "existing_turbines.geojson",
    "official_zoning.geojson",
    "region_stats.json",
    "wka_bestand_ausserhalb_zonen.geojson",
    "zone_centroids.geojson",
    "zone_stats.json",
]


def main() -> None:
    os.makedirs(TARGET, exist_ok=True)

    # Vorher leeren, damit umbenannte oder entfallene Datensätze nicht als
    # Leichen im Build-Output liegen bleiben.
    for existing in os.listdir(TARGET):
        os.remove(os.path.join(TARGET, existing))

    missing, total = [], 0
    for name in SERVED:
        src = os.path.join(GEODATA, name)
        if not os.path.exists(src):
            missing.append(name)
            continue
        dest = os.path.join(TARGET, os.path.splitext(name)[0] + ".json")
        shutil.copyfile(src, dest)
        total += os.path.getsize(dest)
        print(f"  {name:32} → static/data/{os.path.basename(dest)}")

    if missing:
        sys.exit(f"\nFEHLT in geodata/: {', '.join(missing)}")
    print(f"\n{len(SERVED)} Dateien, {total / 1e6:.1f} MB nach static/data/")


if __name__ == "__main__":
    main()
