#!/usr/bin/env python3
"""Übernimmt das steirische SAPRO Windenergie 2026 aus dem Landesdatensatz.

Quelle
------
Land Steiermark, Abteilung 17, Open Government Data:
    https://service.stmk.gv.at/ogd/OGD_Data_ABT17/geoinformation/SAPRO_Windenergie_zone.zip
→ entpackt nach scripts/raster/stmk_sapro_windenergie/ (gitignoriert, bei Bedarf
neu laden). EPSG:4258 (ETRS89), 29 Objekte, Felder Zone/Name/Von_Dat/Von_LGBL:

    Vorrang     25 Zonen     6.853 ha
    Eignung      3 Zonen     1.711 ha
    Ausschluss   1 Objekt  444.258 ha   (gut ein Viertel der Steiermark)

Was das Skript tut
------------------
1. **Vorrang- und Eignungszonen** ersetzen in `geodata/official_zoning.geojson`
   die bisherigen steirischen Zonen. Diese stammten aus dem Rasterband
   `official_wind_zoning` der Lieferung (extract_official_zoning_extra.py) — gleiche
   28 Zonen, gleiche 8.564 ha, aber ohne Namen und ohne Typ. Mit dem Typ können die
   Gemeindetexte Vorrang- und Eignungszone unterscheiden, statt beide neutral als
   „ausgewiesene Windkraftzone“ zu beschreiben.

2. **Die Ausschlusszone** geht in eine eigene Datei,
   `geodata/official_exclusion.geojson`, und bewusst *nicht* in official_zoning:
   - Die Karte zeichnet official_zoning als lila „Windkraftzone“. Ein Ausschluss
     dort wäre das Gegenteil dessen, was er bedeutet (aus demselben Grund fehlen
     bis heute die 31 burgenländischen Ausschlusszonen, add_ktn_bgld_zoning.py).
   - official_zoning wird an jeden Browser ausgeliefert. Ein Polygon über 444.000 ha
     mitzuschicken, das nirgends gezeichnet wird, wäre reiner Ballast.
   Die Datei speist build_region_stats.py (je Gemeinde: wie viel Gemeinde- und
   Potenzialfläche in der Ausschlusszone liegt) und wird seit 16.11.2026 als
   eigener, schraffierter Layer gezeichnet (Map.svelte, „official-exclusion“).

Das Skript ist wiederholbar: vorhandene steirische Objekte werden in beiden Dateien
ersetzt, alles andere bleibt unangetastet.

Aufruf
------
    python scripts/add_stmk_sapro_zoning.py
"""

from __future__ import annotations

import json
import os
import sys

import geopandas as gpd
import shapely
from shapely.geometry import mapping

SHP = "scripts/raster/stmk_sapro_windenergie/SAPRO_Windenergie_zone.shp"
SOURCE_URL = "https://service.stmk.gv.at/ogd/OGD_Data_ABT17/geoinformation/SAPRO_Windenergie_zone.zip"
ZONING = "geodata/official_zoning.geojson"
EXCLUSION = "geodata/official_exclusion.geojson"
BUNDESLAND = "Steiermark"
SIMPLIFY_TOL = 0.00005  # Grad, ~5 m

ZONE_TYPE = {"Vorrang": "vorrang", "Eignung": "eignung", "Ausschluss": "ausschluss"}


def iso_date(dmy: str | None) -> str | None:
    """'15.10.2026' → '2026-10-15'."""
    if not dmy:
        return None
    d, m, y = dmy.strip().split(".")
    return f"{y}-{int(m):02d}-{int(d):02d}"


def legal_basis(lgbl: str | None) -> str:
    # Feld lautet „LGBl.Nr.87/2026“ — in die Schreibweise der übrigen Länder bringen.
    nr = (lgbl or "").replace("LGBl.Nr.", "").strip()
    return f"SAPRO Windenergie 2026, Stmk. LGBl. Nr. {nr}" if nr else "SAPRO Windenergie 2026"


def replace_state(path: str, new_features: list[dict]) -> tuple[int, int]:
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            fc = json.load(fh)
    else:
        fc = {"type": "FeatureCollection", "features": []}
    before = len(fc["features"])
    fc["features"] = [f for f in fc["features"]
                      if f["properties"].get("bundesland") != BUNDESLAND]
    dropped = before - len(fc["features"])
    fc["features"].extend(new_features)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(fc, fh, ensure_ascii=False, separators=(",", ":"))
    return dropped, len(fc["features"])


def main() -> None:
    if not os.path.exists(SHP):
        sys.exit(f"Fehlt: {SHP}\nHerunterladen und entpacken: {SOURCE_URL}")

    src = gpd.read_file(SHP, encoding="utf-8")
    unknown = set(src["Zone"]) - set(ZONE_TYPE)
    if unknown:
        sys.exit(f"Unbekannte Zonenart(en) im Landesdatensatz: {unknown}")
    stale = src[src["aktuell"].fillna("J") != "J"]
    if len(stale):
        print(f"  {len(stale)} nicht mehr aktuelle Objekte ausgelassen")
        src = src[src["aktuell"].fillna("J") == "J"]

    # Die Landesgeometrie ist nicht durchgehend gültig (Selbstüberschneidungen) —
    # ohne Reparatur scheitern die Verschneidungen in build_region_stats.py.
    src["geometry"] = src.make_valid()
    # ETRS89 und WGS84 liegen in Österreich unter einem Meter auseinander; die
    # Fläche wird trotzdem flächentreu in MGI/Lambert gerechnet wie überall sonst.
    src["area_ha"] = (src.to_crs(31287).area / 10_000).round(2)
    src = src.to_crs(4326)
    # Auf ~5 m vereinfachen, wie extract_official_zoning_extra.py und die
    # Bandextraktion. Ohne das wäre official_zoning.json (geht an jeden Browser)
    # um rund 190 kB gewachsen — für Kanten, die man auf der Karte nicht sieht.
    # Die Fläche oben ist vorher und aus der Originalgeometrie gerechnet.
    src["geometry"] = src.simplify(SIMPLIFY_TOL, preserve_topology=True)
    # Koordinaten auf 5 Nachkommastellen (~1 m). Ohne das schreibt GeoPandas
    # volle Gleitkommagenauigkeit, und die Ausschlusszone — sie wird seit
    # 16.11.2026 auf der Karte gezeichnet — war mit 1,2 MB doppelt so groß.
    src["geometry"] = shapely.set_precision(src.geometry.values, 0.00001)

    zones, exclusions = [], []
    positives = src[src["Zone"] != "Ausschluss"].sort_values(["Zone", "Name"], ascending=[False, True])
    for i, (_, row) in enumerate(positives.iterrows(), 1):
        zones.append({
            "type": "Feature",
            "geometry": mapping(row.geometry),
            "properties": {
                "zoning_id": f"STMK-{i:02d}",
                "bundesland": BUNDESLAND,
                "name": row["Name"],
                "area_ha": float(row["area_ha"]),
                "zone_type": ZONE_TYPE[row["Zone"]],
                "legal_basis": legal_basis(row["Von_LGBL"]),
                "effective_from": iso_date(row["Von_Dat"]),
                "source_url": SOURCE_URL,
            },
        })
    for i, (_, row) in enumerate(src[src["Zone"] == "Ausschluss"].iterrows(), 1):
        exclusions.append({
            "type": "Feature",
            "geometry": mapping(row.geometry),
            "properties": {
                "exclusion_id": f"STMK-AUS-{i:02d}",
                "bundesland": BUNDESLAND,
                "area_ha": float(row["area_ha"]),
                "zone_type": "ausschluss",
                "legal_basis": legal_basis(row["Von_LGBL"]),
                "effective_from": iso_date(row["Von_Dat"]),
                "source_url": SOURCE_URL,
            },
        })

    by_type: dict[str, list[float]] = {}
    for f in zones + exclusions:
        by_type.setdefault(f["properties"]["zone_type"], []).append(f["properties"]["area_ha"])
    for t, areas in by_type.items():
        print(f"  {t:<11} {len(areas):>3} Objekte {sum(areas):>12,.0f} ha")

    dropped, total = replace_state(ZONING, zones)
    print(f"→ {ZONING}: {dropped} bisherige steirische Zonen ersetzt durch {len(zones)}, "
          f"jetzt {total} Objekte")
    dropped, total = replace_state(EXCLUSION, exclusions)
    print(f"→ {EXCLUSION}: {len(exclusions)} Ausschlusszone(n), jetzt {total} Objekte "
          f"({os.path.getsize(EXCLUSION) / 1e6:.1f} MB)")


if __name__ == "__main__":
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    main()
