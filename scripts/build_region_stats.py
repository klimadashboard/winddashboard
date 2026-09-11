#!/usr/bin/env python3
"""Baut geodata/region_stats.json — die Kennzahlen je Gemeinde.

Warum es dieses Skript gibt
---------------------------
Die App hat die Gemeinde-Kennzahlen früher zur Laufzeit aus der Karte gelesen:
`queryRenderedFeatures` über die **Bounding Box** des Gemeindeumrisses. Eine Box
ist aber keine Gemeinde — jede Zone und jede Anlage im umschreibenden Rechteck
zählte mit. So bekam Hausleiten die Windkraftzone der Nachbargemeinde Rußbach
zugeschrieben, und Potenzialflächen, die über eine Gemeindegrenze reichen,
schleppten die Anlagen der Nachbargemeinde mit.

Dazu kam: die Anlagenzahl stammte aus `n_existing_turbines` der Potenzialflächen.
Anlagen, die außerhalb jeder Potenzialfläche stehen, waren damit unsichtbar —
in Munderfing (OÖ) stehen 6 Anlagen, angezeigt wurden 0.

Dieses Skript verschneidet die Daten stattdessen einmalig gegen die **amtlichen
Gemeindegrenzen der Statistik Austria** (EPSG:31287, korrekt datumstransformiert)
und schreibt eine fertige Tabelle. Die App schlägt dann nur noch nach.

Datenquelle Gemeindegrenzen
---------------------------
Statistik Austria, "Gliederung Österreichs in Gemeinden", CC-BY 4.0:

    curl -L -A "Mozilla/5.0" -o gem.zip \\
      "https://www.statistik.gv.at/gs-open/GEODATA/ows?service=WFS&version=1.0.0\\
&request=GetFeature&typeName=GEODATA:STATISTIK_AUSTRIA_GEM_20260101\\
&outputFormat=SHAPE-ZIP&format_options=CHARSET:UTF-8"
    unzip gem.zip -d gemeinden/

Die `outline`-Geometrien der Regions-API waren bis 8.9.2026 einheitlich rund
205 m nach Westen und 77 m nach Norden versetzt (MGI → WGS84 ohne
Datumstransformation) und für eine Verschneidung unbrauchbar. Sie wurden am
9.9.2026 aus derselben amtlichen Quelle korrigiert (flow-Repository,
manual/wip/fix-at-outlines). Dieses Skript bleibt bei der amtlichen Lieferung:
die API-Umrisse sind für den Transport auf rund 200 Stützpunkte vereinfacht,
was an Gemeindegrenzen ein paar Hektar hin oder her ausmacht.

Aufruf
------
    python scripts/build_region_stats.py --gemeinden <verzeichnis-mit-shp>
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import sys

import geopandas as gpd
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEODATA = os.path.join(REPO, "geodata")

# Amtliche Grenzen liegen in MGI/Austria Lambert vor; darin wird verschnitten.
CRS_WORK = 31287
# Flächen werden in ETRS89-LAEA gerechnet (flächentreu).
CRS_AREA = 3035

# Genau ein Potenzialflächen-Datensatz. Die fünf Siedlungsabstands-Szenarien
# wurden am 10.9.2026 entfernt — siehe scripts/extract_possible_zones.py.
POSSIBLE_ZONES = "possible_zones.geojson"

# Splitterschwelle: Ragt eine Zone nur mit weniger als 1 ha in eine Gemeinde,
# zählt sie dort nicht. Ohne das würde ein Grenzverlauf-Artefakt von 0,15 ha
# genügen, damit "In X befindet sich eine Windkraftzone" erscheint — genau der
# Fall Hausleiten/Rußbach (WE121 liegt zu 99,9 % in Rußbach).
MIN_SHARE_HA = 1.0


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def load_gemeinden(directory: str) -> gpd.GeoDataFrame:
    shp = glob.glob(os.path.join(directory, "*.shp"))
    if not shp:
        sys.exit(f"Kein Shapefile in {directory} gefunden.")
    gem = gpd.read_file(shp[0])
    missing = {"g_id", "g_name"} - set(gem.columns)
    if missing:
        sys.exit(f"Spalten fehlen im Shapefile: {sorted(missing)}")
    gem = gem.to_crs(CRS_WORK)
    gem["g_id"] = gem["g_id"].astype(str)
    # Ein paar Gemeinden sind mehrteilig (Exklaven) — je GKZ eine Geometrie.
    gem = gem.dissolve(by="g_id", aggfunc={"g_name": "first"}).reset_index()
    log(f"Gemeinden: {len(gem)} ({os.path.basename(shp[0])})")
    return gem


def read_layer(name: str) -> gpd.GeoDataFrame:
    path = os.path.join(GEODATA, name)
    if not os.path.exists(path):
        sys.exit(f"Fehlt: {path}")
    return gpd.read_file(path).to_crs(CRS_WORK)


def clipped_area_ha(frame: gpd.GeoDataFrame) -> pd.Series:
    """Fläche der (bereits verschnittenen) Geometrien in Hektar."""
    return frame.geometry.to_crs(CRS_AREA).area / 10_000.0


def join_polygons(gem: gpd.GeoDataFrame, polys: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Verschneidet Polygone mit den Gemeinden; eine Zeile je (Zone, Gemeinde)."""
    parts = gpd.overlay(
        polys, gem[["g_id", "geometry"]], how="intersection", keep_geom_type=True
    )
    parts["area_in_gem_ha"] = clipped_area_ha(parts)
    return parts[parts["area_in_gem_ha"] >= MIN_SHARE_HA]


# Österreich-Bounding-Box, um kaputte Koordinaten zu erkennen.
AT_BBOX = (9.4, 46.3, 17.3, 49.1)
# Anlagen dürfen bis zu dieser Distanz außerhalb einer Gemeinde liegen und
# werden ihr trotzdem zugerechnet — deckt Ungenauigkeiten im Grenzverlauf ab
# (z.B. zwei Anlagen in Andau, 20 bzw. 29 m jenseits der Staatsgrenze).
SNAP_TOLERANCE_M = 100.0


def sanitize_turbines() -> gpd.GeoDataFrame:
    """Lädt die Bestandsanlagen und repariert offensichtlich kaputte Koordinaten.

    In der aktuellen Lieferung stecken zwei Fehlerbilder, beide gemeldet:
    8 Anlagen liegen auf [0, 0] und bei 2 sind Länge und Breite vertauscht.
    """
    path = os.path.join(GEODATA, "existing_turbines.geojson")
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)

    swapped = nulled = 0
    for feat in raw["features"]:
        lon, lat = feat["geometry"]["coordinates"][:2]
        # Merkmal vor der Umprojektion setzen — danach ist [0,0] nicht mehr
        # an den Koordinaten erkennbar.
        feat["properties"]["_has_pos"] = not (lon == 0 and lat == 0)
        if lon == 0 and lat == 0:
            nulled += 1
            continue
        in_at = AT_BBOX[0] <= lon <= AT_BBOX[2] and AT_BBOX[1] <= lat <= AT_BBOX[3]
        flipped = AT_BBOX[0] <= lat <= AT_BBOX[2] and AT_BBOX[1] <= lon <= AT_BBOX[3]
        if not in_at and flipped:
            feat["geometry"]["coordinates"] = [lat, lon]
            swapped += 1
    if swapped or nulled:
        log(f"  Anlagendaten: {swapped} vertauschte Koordinaten korrigiert, "
            f"{nulled} auf [0,0] ohne Position")

    turb = gpd.GeoDataFrame.from_features(raw["features"], crs=4326).to_crs(CRS_WORK)
    return turb


def turbines_per_gemeinde(gem: gpd.GeoDataFrame) -> dict[str, int]:
    """Anlagen je Gemeinde — primär geometrisch, mit Namensfallback.

    Die Geometrie ist maßgeblich, nicht das Attribut `gemeinde`: das fehlt bei
    51 der 1.396 Anlagen und ist gegen die amtlichen Namen nicht abgeglichen.
    Nur für Anlagen ohne brauchbare Koordinaten wird der Name herangezogen.
    """
    turb = sanitize_turbines()
    located = turb[turb["_has_pos"] & turb.geometry.notna() & ~turb.geometry.is_empty].copy()

    # Innerhalb einer Gemeinde, sonst zur nächsten innerhalb der Toleranz.
    hit = gpd.sjoin_nearest(
        located, gem[["g_id", "geometry"]], how="left",
        max_distance=SNAP_TOLERANCE_M, distance_col="dist_m",
    )
    counts: dict[str, int] = {}
    for g_id in hit["g_id"].dropna():
        counts[str(g_id)] = counts.get(str(g_id), 0) + 1
    placed = sum(counts.values())

    # Fallback über den Gemeindenamen — nur bei eindeutigem Treffer.
    by_name = gem.groupby("g_name")["g_id"].apply(list).to_dict()
    unplaced = len(turb) - placed
    by_name_hits = 0
    for _, row in turb.iterrows():
        if row["_has_pos"]:
            continue
        ids = by_name.get(row.get("gemeinde"), [])
        if len(ids) == 1:
            counts[str(ids[0])] = counts.get(str(ids[0]), 0) + 1
            by_name_hits += 1

    log(f"Anlagen: {len(turb)} gesamt, {placed} über Geometrie, "
        f"{by_name_hits} über Gemeindenamen, {unplaced - by_name_hits} ohne Zuordnung")
    return counts


def official_per_gemeinde(gem: gpd.GeoDataFrame) -> dict[str, dict]:
    """Offizielle Zonen je Gemeinde: Anzahl, Fläche und Zonentyp."""
    oz = read_layer("official_zoning.geojson")
    if "zone_type" not in oz.columns:
        oz["zone_type"] = None
    parts = join_polygons(gem, oz)

    out: dict[str, dict] = {}
    for g_id, grp in parts.groupby("g_id"):
        types = [t for t in grp["zone_type"].tolist() if t]
        # Ohne zone_type gilt eine Zone als positiv ausgewiesen — so behandeln
        # NÖ, Salzburg und die Steiermark ihre Zonen in den Rohdaten.
        # Ausschlusszonen dominieren nicht: liegt beides vor, gewinnt die
        # positive Ausweisung, weil sie die konkretere Aussage ist.
        order = ["vorrang", "eignung", "positive", "ausschluss"]
        chosen = next((t for t in order if t in types), "positive" if len(grp) else None)
        out[str(g_id)] = {
            "count": int(len(grp)),
            "type": chosen,
            "areaHa": round(float(grp["area_in_gem_ha"].sum()), 1),
        }
    log(f"Offizielle Zonen: {len(oz)} Objekte, in {len(out)} Gemeinden")
    return out


def potential_per_gemeinde(gem: gpd.GeoDataFrame) -> dict[str, dict]:
    """Potenzialflächen je Gemeinde."""
    zones = read_layer(POSSIBLE_ZONES)
    parts = join_polygons(gem, zones)

    out: dict[str, dict] = {}
    for g_id, grp in parts.groupby("g_id"):
        area = float(grp["area_in_gem_ha"].sum())
        pd_col = grp.get("pd_mean_w_m2")
        # Windleistungsdichte flächengewichtet über die Anteile in der Gemeinde.
        if pd_col is not None and area > 0:
            pd_mean = float((pd_col.fillna(0) * grp["area_in_gem_ha"]).sum() / area)
        else:
            pd_mean = 0.0
        out[str(g_id)] = {
            "count": int(len(grp)),
            "areaHa": round(area, 1),
            "pd": round(pd_mean),
        }
    log(f"Potenzialflächen: {len(zones)} Objekte, in {len(out)} Gemeinden")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--gemeinden",
        required=True,
        help="Verzeichnis mit dem entpackten Statistik-Austria-Shapefile",
    )
    ap.add_argument(
        "--out",
        default=os.path.join(GEODATA, "region_stats.json"),
        help="Zieldatei (Default: geodata/region_stats.json)",
    )
    args = ap.parse_args()

    gem = load_gemeinden(args.gemeinden)

    turbines = turbines_per_gemeinde(gem)
    official = official_per_gemeinde(gem)
    potential = potential_per_gemeinde(gem)

    bounds = gem.to_crs(4326).bounds
    bounds.index = gem["g_id"]

    regions: dict[str, dict] = {}
    for _, row in gem.iterrows():
        g_id = str(row["g_id"])
        b = bounds.loc[g_id]
        entry = {
            "name": row["g_name"],
            "turbines": turbines.get(g_id, 0),
            "bounds": [
                round(float(b["minx"]), 5),
                round(float(b["miny"]), 5),
                round(float(b["maxx"]), 5),
                round(float(b["maxy"]), 5),
            ],
            "potential": potential.get(g_id, {"count": 0, "areaHa": 0.0, "pd": 0}),
        }
        if g_id in official:
            entry["official"] = official[g_id]
        regions[g_id] = entry

    payload = {
        "generated": pd.Timestamp.utcnow().strftime("%Y-%m-%d"),
        "boundarySource": os.path.basename(glob.glob(os.path.join(args.gemeinden, "*.shp"))[0]),
        "minShareHa": MIN_SHARE_HA,
        "regions": regions,
    }

    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, separators=(",", ":"))
    log(f"→ {args.out} ({os.path.getsize(args.out) / 1024:.0f} kB, {len(regions)} Gemeinden)")


if __name__ == "__main__":
    main()
