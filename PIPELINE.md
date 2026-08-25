# Datenpipeline — Windkraft Österreich

Dieses Dokument beschreibt alle Schritte, die beim Einspielen neuer Quelldaten durchzuführen sind.

> **Kurzfassung:** Neue `osm_wka_distance_zones_widmung.tif` ablegen → Schritte 1–5 ausführen →
> zwei MBTiles hochladen → App-Konstanten prüfen (Schritt 6).

---

## Überblick

```
osm_wka_distance_zones_widmung.tif  (Quelldaten, extern generiert, "widmung_v1")
        │
        ├─ Schritt 1: scripts/create_classification_from_simplified.py
        │         └─▶ scripts/raster/classification.tif
        │
        ├─ Schritt 2: scripts/convert_raster.py
        │         └─▶ windkraft_classification.mbtiles  ──▶  Tileserver
        │
        ├─ Schritt 3: scripts/extract_exclusion_geojson.py
        │         └─▶ geodata/exclusion_{schutz,siedlung,sonstige,wind}.geojson
        │
        ├─ Schritt 4: scripts/extract_band_geojson.py  +  tippecanoe
        │         └─▶ windkraft_exclusion_bands.mbtiles  ──▶  Tileserver
        │
        └─ Schritt 5: scripts/fetch_water_bodies.py (GGN + OSM, unabhängig vom .tif)
                       + scripts/extract_possible_zones.py
                  └─▶ geodata/possible_zones_<variant>.geojson  (6×)
                      geodata/zone_centroids_<variant>.geojson  (6×)
                      geodata/variant_stats.json
```

Danach in Schritt 6 die App-Konstanten aktualisieren.

---

## Quelldaten

Die Datei `osm_wka_distance_zones_widmung.tif` nach
`scripts/raster/osm_wka_distance_zones_widmung.tif` kopieren. Das Verzeichnis ist per
`.gitignore` ausgeschlossen — die Datei liegt nicht im Repository.

**Achtung, Größenordnung:** Die Datei ist ~850 MB (vorheriger Stand: ~150 MB) und hat
**54 Bänder** (vorher 23) bei gleicher Auflösung (25 m, EPSG:31287, 24.001×14.001 Zellen).
Alle Pipeline-Schritte laufen dadurch spürbar länger — mehrere Minuten statt Sekunden pro
Skript, insbesondere `extract_band_geojson.py` (vektorisiert 18 Bänder bei voller
Auflösung) und `convert_raster.py`s Tile-Erzeugung (~28.000 PNG-Kacheln). Rechne mit
15–30 Minuten für den gesamten Lauf, abhängig von der Maschine.

Metadaten-Tag `PIPELINE=widmung_v1` im File markiert die Pipeline-Version. Wichtigste
Unterschiede zur vorherigen `simplified_300w.tif`-Generation:

- Siedlungsquelle ist jetzt **österreichweit auf amtlicher Flächenwidmung** basierend
  (`settlement_widmung_*`), mit OSM-Adress-Seed-Fallback nur für Wien & Burgenland
  (Tag `WIEN_BGLD_FALLBACK`).
- Siedlungsabstand ist **bundeslandspezifisch** (Tag `SETTLEMENT_BUFFER_BY_BL`: Kärnten
  1.500 m, Burgenland/Niederösterreich 1.200 m, restliche Bundesländer 1.000 m) —
  **plus 5 zusätzliche uniforme Vergleichsvarianten** (800/1000/1200/1500/2000 m,
  Tag `SETTLEMENT_BUFFER_VARIANTS`), die den neuen Siedlungsabstands-Schieberegler in
  der App speisen.
- Wind-Schwelle jetzt **150 W/m²** @150 m (vorher 300 W/m²), Hangneigungs-Schwelle
  **>15°** (vorher >20°).
- **110-kV-Freileitungen werden nicht mehr gepuffert** (nur noch 380/400 kV).
- **4 neue Objekt-Kategorien** ohne bisheriges Gegenstück: `important_objects` (250 m
  Puffer), `cableway_buildings` (50 m), `haeuser_im_gruenen` (750 m, ersetzt das alte
  "Einzelobjekt/Greenland-Buildings"-Konzept), `general_buildings` (25 m). Die genaue
  fachliche Definition dieser vier Kategorien ist aktuell **nicht dokumentiert** — nur
  Bandname und Pufferwert sind bekannt (siehe `src/lib/config/bands.ts`, `legend.ts`).

Das TIF hat **54 Bänder** (binär uint8, EPSG:31287, 25 m Auflösung):

| Bänder | Name | Bedeutung |
|---:|---|---|
| 1–2 | settlement_widmung_source/buffer | Siedlungsabstand (bundeslandspezifisch) |
| 3–4 | important_objects_source/buffer | Wichtige Objekte (250 m) — undokumentierte Kategorie |
| 5–6 | cableway_buildings_source/buffer | Gebäude an Seilbahnen (50 m) — undokumentierte Kategorie |
| 7–8 | haeuser_im_gruenen_source/buffer | Haus im Grünen (750 m) |
| 9–10 | general_buildings_source/buffer | Allgemeine Gebäude (25 m) — undokumentierte Kategorie |
| 11 | power_380_400kv | Freileitungspuffer (nur 380/400 kV) |
| 12–13 | road_motorway_trunk / road_federal_state | Straßenpuffer |
| 14 | rail_main | Bahnpuffer |
| 15 | cableway_people_150m | Seilbahnpuffer |
| 16 | military_restricted_area | Militärische Sperrzone |
| 17–18 | airport_area / airport_lateral_check_6km | Flughafenzone |
| 19–20 | nature_protection_areas / osm_nature_protection_areas | Schutzgebiete |
| 21 | geography_slope_too_steep | Hangneigung >15° |
| 22 | geography_elevation_too_high | Seehöhe >2.500 m |
| 23 | geography_wind_too_low | Wind <150 W/m² @150 m |
| 24–27 | exclusion_human/nature/geography, all_exclusions | Summierte Ausschlüsse |
| 28 | available_after_all_exclusions_raw | Verfügbar (vor Größenfilter) |
| **29** | **available_cleaned_min_10ha** | **Verfügbar ≥10 ha (Default-Variante) ← Hauptband** |
| 30 | official_wind_zoning | Offizielle Eignungszonen NÖ+Stmk+Sbg (Referenz) |
| 31–34 | Variante `default` | settlement_widmung_buffer/exclusion_human/raw/cleaned |
| 35–38 | Variante `800m` | dito |
| 39–42 | Variante `1000m` | dito |
| 43–46 | Variante `1200m` | dito |
| 47–50 | Variante `1500m` | dito |
| 51–54 | Variante `2000m` | dito |

> ⚠️ Die mitgelieferte README des Datenpakets war beim Einspielen dieser Version bereits
> veraltet (beschrieb ein älteres 48-Band-Schema) — die obige Tabelle stammt aus
> `rasterio`/`gdalinfo` direkt gegen das File, nicht aus der README.

---

## Schritt 1 – Klassifikationsraster ableiten

```bash
python scripts/create_classification_from_simplified.py
```

Liest die 18 "Default"-Bänder (Bundesland-spezifischer Siedlungsabstand) mit
Prioritätsreihenfolge (letzte gewinnt) und schreibt `scripts/raster/classification.tif`
(1 Band, uint8, Codes 0–14). **Maskiert anschließend auf `geodata/austria_outline.geojson`**
— wichtig, weil `geography_wind_too_low` in dieser Datei nicht auf Österreich geclippt ist
(fehlende Winddaten außerhalb der Landesgrenze werden als "zu wenig Wind" markiert; ohne
Maskierung würde die rechteckige Rasterausdehnung rund um Österreich fälschlich als riesige
Windausschlussfläche erscheinen).

Das Skript gibt am Ende die **Pixelverteilung** aus (× 0,0625 ha/px = Hektar). Diese Zahlen
werden in Schritt 6 für `Scrollytelling.svelte` benötigt.

| Code | Bedeutung | Quelleband |
|---:|---|---|
| 0 | Außerhalb Österreichs / kein Datum | — |
| 1 | Schutzgebiet | 19, 20 |
| 2 | Siedlungsabstand | 2 |
| 3 | Haus im Grünen | 8 |
| 4 | Sperrzone | 16, 17, 18 |
| 5 | Verkehrsweg 150 m | 12, 13, 15 |
| 6 | Eisenbahn 150 m | 14 |
| 7 | Hangneigung >15° | 21 |
| 8 | Seehöhe >2.500 m | 22 |
| 9 | Wichtige Objekte | 4 |
| 10 | Freileitung 380/400 kV | 11 |
| 11 | Wind zu gering (<150 W/m²) | 23 |
| 12 | Allgemeine Gebäude | 10 |
| 13 | Gebäude an Seilbahnen | 6 |
| **14** | **Geeignet (Default-Variante)** | **29** |

---

## Schritt 2 – Klassifikations-MBTiles erzeugen

```bash
cd scripts/raster
python ../convert_raster.py
```

Erzeugt `classification_rgba_3857.tif`, `tiles/` (PNG, Zoom 6–13) und
`windkraft_classification.mbtiles`. `COLORMAP` in diesem Skript ist an die 15 Codes aus
Schritt 1 angepasst und muss mit `src/lib/config/legend.ts` synchron gehalten werden.

**Auf den Tileserver hochladen:**

```bash
scp scripts/raster/windkraft_classification.mbtiles user@tileserver:/data/
# TileServer GL neu starten
```

Prüfen: `https://tiles.klimadashboard.org/data/windkraft_classification/8/136/89.png`

> Dieser Layer wird aktuell nur noch intern genutzt (als Fallback); die Detailansicht
> verwendet stattdessen die Vektorkacheln aus Schritt 4.

---

## Schritt 3 – Ausschluss-GeoJSONs (Story-Modus)

```bash
python scripts/extract_exclusion_geojson.py
```

Liest `scripts/raster/classification.tif` (Band 1) und schreibt vier vereinfachte
GeoJSONs für die animierten Ausschluss-Overlays im Scrollytelling:

- `geodata/exclusion_schutz.geojson` (Code 1 — Schutzgebiete)
- `geodata/exclusion_siedlung.geojson` (Code 2 — Siedlungsabstand)
- `geodata/exclusion_sonstige.geojson` (Codes 3–10, 12–13 — Infrastruktur/Gelände)
- `geodata/exclusion_wind.geojson` (Code 11 — Wind zu gering, <150 W/m²; eigener Scrollytelling-Schritt)

---

## Schritt 4 – Detailansicht-Vektorkacheln erzeugen

Die 18 Ausschluss-Ebenen werden als **Vektor-MBTiles** für die interaktive Detailansicht
aufgebaut, plus 5 zusätzliche Siedlungsabstand-Varianten-Layer für den Schieberegler
(siehe unten) — macht 23 Layer in einer einzigen mbtiles. Die GeoJSONs werden bei
**voller 25-m-Auflösung** erzeugt, damit die Grenzen exakt mit den Potenzialzonen aus
Schritt 5 übereinstimmen.

### 4a – GeoJSONs extrahieren

```bash
python scripts/extract_band_geojson.py
```

Schreibt `geodata/band_01_human_settlement.geojson` … `band_18_geo_wind.geojson` (18
Bänder), plus `band_01_human_settlement_800.geojson`, `_1000.geojson`, `_1200.geojson`,
`_1500.geojson`, `_2000.geojson` — die 5 alternativen Siedlungsabstand-Varianten. Nur der
Siedlungsabstand unterscheidet sich zwischen den 6 Varianten (siehe Datei-Metadaten
`SETTLEMENT_BUFFER_VARIANTS`); alle anderen 17 Bänder sind variantenunabhängig und werden
nur einmal extrahiert.

Jedes Band wird vor dem Vektorisieren auf `geodata/austria_outline.geojson` maskiert
(`load_austria_mask()`) — mehrere Quellbänder (v. a. `geography_wind_too_low`) sind
selbst nicht auf Österreich geclippt und würden sonst weit ins benachbarte Ausland
(Bayern, Südtirol, Slowenien …) hineinreichen, sichtbar z. B. im Experten-Panel als
riesige „Wind zu gering"-Fläche außerhalb der Landesgrenze.

Alle Features tragen eine stabile `band_id` (1–18, s. Tabelle unten) — bei den 5
Siedlungsabstand-Varianten ist das *immer* `1`, unabhängig vom Quellband im TIF, damit
Hover-Tooltips & Legende unabhängig von der gewählten Variante funktionieren.

| Slug | band_id | Quellband (Default) |
|---|---:|---:|
| band_01_human_settlement(_800/_1000/_1200/_1500/_2000) | 1 | 2 (bzw. 31/35/39/43/47/51) |
| band_02_human_important_objects | 2 | 4 |
| band_03_human_cableway_buildings | 3 | 6 |
| band_04_human_haeuser_im_gruenen | 4 | 8 |
| band_05_human_general_buildings | 5 | 10 |
| band_06_human_power_380kv | 6 | 11 |
| band_07_human_road_motorway | 7 | 12 |
| band_08_human_road_federal | 8 | 13 |
| band_09_human_rail | 9 | 14 |
| band_10_human_cableway_people | 10 | 15 |
| band_11_human_military | 11 | 16 |
| band_12_human_airport | 12 | 17 |
| band_13_human_airport_lateral | 13 | 18 |
| band_14_nature_protection | 14 | 19 |
| band_15_nature_osm | 15 | 20 |
| band_16_geo_slope | 16 | 21 |
| band_17_geo_elevation | 17 | 22 |
| band_18_geo_wind | 18 | 23 |

### 4b – MBTiles mit Tippecanoe packen

```bash
tippecanoe \
  --output scripts/raster/windkraft_exclusion_bands.mbtiles \
  --force \
  --minimum-zoom=5 --maximum-zoom=14 \
  --no-tile-size-limit --simplification=4 --detect-shared-borders --no-tile-stats \
  -L band_01_human_settlement:geodata/band_01_human_settlement.geojson \
  -L band_01_human_settlement_800:geodata/band_01_human_settlement_800.geojson \
  -L band_01_human_settlement_1000:geodata/band_01_human_settlement_1000.geojson \
  -L band_01_human_settlement_1200:geodata/band_01_human_settlement_1200.geojson \
  -L band_01_human_settlement_1500:geodata/band_01_human_settlement_1500.geojson \
  -L band_01_human_settlement_2000:geodata/band_01_human_settlement_2000.geojson \
  -L band_02_human_important_objects:geodata/band_02_human_important_objects.geojson \
  -L band_03_human_cableway_buildings:geodata/band_03_human_cableway_buildings.geojson \
  -L band_04_human_haeuser_im_gruenen:geodata/band_04_human_haeuser_im_gruenen.geojson \
  -L band_05_human_general_buildings:geodata/band_05_human_general_buildings.geojson \
  -L band_06_human_power_380kv:geodata/band_06_human_power_380kv.geojson \
  -L band_07_human_road_motorway:geodata/band_07_human_road_motorway.geojson \
  -L band_08_human_road_federal:geodata/band_08_human_road_federal.geojson \
  -L band_09_human_rail:geodata/band_09_human_rail.geojson \
  -L band_10_human_cableway_people:geodata/band_10_human_cableway_people.geojson \
  -L band_11_human_military:geodata/band_11_human_military.geojson \
  -L band_12_human_airport:geodata/band_12_human_airport.geojson \
  -L band_13_human_airport_lateral:geodata/band_13_human_airport_lateral.geojson \
  -L band_14_nature_protection:geodata/band_14_nature_protection.geojson \
  -L band_15_nature_osm:geodata/band_15_nature_osm.geojson \
  -L band_16_geo_slope:geodata/band_16_geo_slope.geojson \
  -L band_17_geo_elevation:geodata/band_17_geo_elevation.geojson \
  -L band_18_geo_wind:geodata/band_18_geo_wind.geojson
```

### 4c – Metadaten setzen & hochladen

```bash
python3 -c "
import sqlite3
con = sqlite3.connect('scripts/raster/windkraft_exclusion_bands.mbtiles')
con.execute(\"UPDATE metadata SET value='windkraft-exclusion-bands' WHERE name='name'\")
con.commit(); con.close()
print('Metadaten OK')
"

scp scripts/raster/windkraft_exclusion_bands.mbtiles user@tileserver:/data/
# TileServer GL neu starten
```

**TileServer GL `config.json`** (einmalig, falls noch nicht vorhanden):
```json
"windkraft_exclusion_bands": { "mbtiles": "windkraft_exclusion_bands.mbtiles" }
```

> ⚠️ Der Name auf dem Tileserver verwendet **Unterstriche** (`windkraft_exclusion_bands`),
> nicht Bindestriche. Die App-Konfiguration in `src/lib/config/bands.ts` (`EXCLUSION_BANDS_TILES`)
> muss damit übereinstimmen.

Prüfen: `https://tiles.klimadashboard.org/data/windkraft_exclusion_bands/10/560/356.pbf`

**Erwartete Ausgabe:** 23 `source-layer`, Zoom 5–14.

---

## Schritt 5 – Potenzialzonen-GeoJSONs (6 Siedlungsabstands-Varianten)

```bash
python scripts/fetch_water_bodies.py     # einmalig / bei Bedarf neu — siehe unten
python scripts/extract_possible_zones.py
```

`fetch_water_bodies.py` schreibt `scripts/raster/water_bodies.geojson` (gitignored)
und vereint dafür **zwei** Quellen — jede für das, was sie tatsächlich gut modelliert:

1. **Seen/Speicher: "Stehende Gewässer des Gesamtgewässernetz Österreich (GGN)"**
   (Umweltbundesamt, CC BY 4.0, ~34.800 Polygone, bereits in EPSG:31287 — keine
   Reprojektionsverzerrung beim Rasterisieren).
2. **Flüsse/Kanäle: OSM** (`natural=water` + `waterway=riverbank`, als Flächen).

Ohne diese Datei läuft `extract_possible_zones.py` trotzdem durch (nur eine Warnung),
schließt dann aber keine Gewässer aus.

> **Warum zwei Quellen?** Reines OSM hat an Flussdeltas Lücken gelassen (konkret: das
> Rheindelta am österreichischen Ende des Bodensees — dort ist der Untergrund in OSM
> als Feuchtgebiet/Schilf/Schotterbank getaggt, nicht als Wasserfläche; die betroffene
> Zone lag zu 100 % im GGN-Seepolygon, aber bei <1 % Überlappung in OSM). Reines GGN
> wiederum kennt **keine Flussflächen**: die GGN-Fließgewässer-Distribution ist
> LineString-Geometrie (89.577 Routen-Mittellinien, Attribute nur `LAENGE_KM`/`GEW_KAT`,
> keine Breite) — allein im Donaukorridor lagen dadurch 8 Zonen zu >1 % im Fluss,
> die schlimmste (Zone 549, 5,4 ha) zu 42 %. Nach dem Zusammenführen sind es 3 Zonen
> mit max. 2,9 %, was der 25-m-Rasterkörnung an gewundenen Ufern entspricht.
> Ein Puffern der Mittellinien mit geschätzter Breite würde auf dem 25-m-Raster in
> beide Richtungen falsch liegen, daher die Kombination.

> **Zwei Fallstricke, die hier schon zugeschlagen haben** (beide behoben, bitte nicht
> reintroduzieren):
> 1. **OSM-Multipolygon-Zusammenbau.** Große Flüsse teilen ihren äußeren Ring auf
>    mehrere Member-Ways auf; ein Member ist also meist ein *offenes Fragment*.
>    Jedes Fragment einzeln zu schließen erzeugt riesige Sliver-Polygone quer über
>    Land (statt des Flusses) — das maskiert dann willkürlich Landflächen weg und
>    liefert gleichzeitig frei erfundene "Zone liegt zu 100 % im Fluss"-Treffer.
>    `_stitch_rings()` fügt Fragmente end-to-end zusammen; Inner-Rings (Flussinseln)
>    werden als Löcher abgezogen, bleiben also Land.
> 2. **Simplify-Toleranz.** `SIMPLIFY_TOL` muss deutlich unter der 25-m-Pixelgröße
>    bleiben. Mit ~50 m (0.0005°) waren Seen noch in Ordnung, Flüsse (oft nur
>    50–100 m breit) wurden aber praktisch weggeschliffen: die Donau deckte an
>    Zone 549 nur 3,5 % statt 42 % ab. Jetzt ~5 m (0.00005°).

> Die öffentliche Overpass-API bricht einzelne Kacheln unvorhersehbar ab (429/504).
> Das Skript retried mit langem Backoff und legt die Roh-Elemente danach unter
> `scripts/raster/osm_water_raw.json` ab — ein erneuter Lauf nutzt diesen Cache und
> überspringt den ~10-minütigen Fetch (zum Neuladen die Datei löschen). Zeigt das
> Log eine Kachel mit 0 Elementen, war sie nicht erfolgreich: erneut laufen lassen
> bzw. nur die fehlenden Kacheln nachziehen und in den Cache mergen (dedupliziert
> über die OSM-ID).

`extract_possible_zones.py` liest für jede der 6 Siedlungsabstand-Varianten (`default`,
`800`, `1000`, `1200`, `1500`, `2000`) das jeweilige `available_cleaned_min_10ha_<variant>`-Band
bei **voller 25-m-Auflösung**, maskiert es auf `geodata/austria_outline.geojson`
(`load_austria_mask()`) und auf `water_bodies.geojson` (`load_water_mask()`, beide einmal
berechnet und über alle Varianten wiederverwendet) und schreibt pro Variante:

- `geodata/possible_zones_<variant>.geojson` — Polygone mit Bundesland-Zuweisung und Turbinenzählung
- `geodata/zone_centroids_<variant>.geojson` — Zentroide (Gewicht `w`) für Heatmap-Layer

Die `default`-Variante wird stattdessen unsuffixiert geschrieben
(`possible_zones.geojson`/`zone_centroids.geojson`) — es gibt also keine
`possible_zones_default.geojson` als separate ~15-MB-Kopie.

Zusätzlich entsteht `geodata/variant_stats.json` — pro Variante `{count, totalHa,
perBundesland}` — Grundlage für den Siedlungsabstand-Schieberegler in der App (Inspector-
Zonenzahl, Scrollytelling-Konstanten) und für Schritt 6 unten.

Das Skript lädt `geodata/austria_states.geojson` (GADM Austria level-1, bereits im Repo)
für den räumlichen Bundesland-Join. Turbinen-Zuordnung läuft über einen räumlichen Index
(`shapely.strtree.STRtree`, `predicate="within"`) statt einer verschachtelten Schleife —
bei ~5.000 Zonen × 6 Varianten sonst spürbar langsam.

### Optional – Steiermark/Salzburg zu official_zoning.geojson ergänzen

```bash
python scripts/extract_official_zoning_extra.py
```

`geodata/official_zoning.geojson` enthielt historisch nur amtlich kuratierte
NÖ-Zonen (mit `legal_basis`, `effective_from`, `communities` — extern vektorisiert,
nicht aus dem Raster). Dieses Skript ergänzt **nur** Steiermark und Salzburg aus
Band 30 (`official_wind_zoning`) der Quelldatei — NÖ bleibt unangetastet. Nur nötig,
wenn `official_zoning.geojson` aus Versehen auf einen reinen NÖ-Stand zurückgesetzt
wurde; normalerweise bleibt die Datei so wie sie ist.

### Optional – Kärnten/Burgenland zu official_zoning.geojson ergänzen

```bash
python scripts/add_ktn_bgld_zoning.py
```

Ergänzt Kärnten (4 Beschleunigungsgebiete) und Burgenland (40 Eignungszonen —
die 31 Ausschlusszonen aus derselben Quelle werden bewusst NICHT übernommen,
siehe Docstring) aus eigenständig herunterladbaren Shapefiles der jeweiligen
Landes-GIS-Portale (nicht aus dem Raster). Erwartet die Shapefiles unter
`scripts/raster/ktn_windkraftbeschleunigungszone/` bzw.
`scripts/raster/bgld_wk_eignungszonen/` (gitignored — Download-URLs siehe
Skript-Docstring). Setzt als einzige der bisherigen Quellen auch `zone_type`
korrekt (`positive` bzw. `eignung`) — bei NÖ/Steiermark/Salzburg fehlt dieses
Feld aktuell noch, wodurch deren zonenspezifische Text-Zweige in
`regionIntro.ts` faktisch nie greifen (Map.svelte liefert ohne `zone_type`
immer `'positive'` zurück).

### Optional – Bundesland-Flächen zur Konsistenzprüfung berechnen

```bash
python scripts/compute_bundesland_areas.py
```

Rasterisiert `geodata/austria_states.geojson` pro Bundesland gegen
`scripts/raster/classification.tif` und summiert die Pixel je Bundesland (Codes 1–14,
also innerhalb der Österreich-Maske) — liefert die Gesamtfläche jedes Bundeslands in der
gleichen raster-basierten Zählweise wie `AUSTRIA_HA`. Genutzt für die
„Anteil an der Bundeslandfläche"-Balken in `Scrollytelling.svelte` (Potentialflächen/
Zonierungsflächen). Gegen Statistik Austria geprüft (Fläche und Benützungsarten,
Stand 1.1.2025) — alle 9 Bundesländer liegen innerhalb von ~1 % der amtlichen Zahl.

---

## Schritt 6 – App-Konstanten aktualisieren

Nach jedem Datensatz folgende Konstanten in der App prüfen und anpassen (Werte hier sind
Beispiele aus dem `default`-Lauf — immer die tatsächliche Skript-Ausgabe verwenden, nicht
diese Zahlen blind übernehmen):

### `src/lib/components/Scrollytelling.svelte`

```typescript
// Aus Schritt 1 (classification.tif Pixelzählung × 0,0625 ha/px):
const SCHUTZ_HA    =   987_740;   // Code 1        → aus Script-Output Schritt 1
const SIEDLUNG_HA  = 4_678_664;   // Code 2        → aus Script-Output Schritt 1
const SONSTIGE_HA  = 2_280_513;   // Codes 3–10, 12–13 (Wind separat, siehe unten)
const WIND_HA      =    38_530;   // Code 11 — Wind zu gering (<150 W/m²)
const POTENTIAL_HA =   355_378;   // Code 14
// AUSTRIA_HA kommt aus src/lib/config/austria.ts (fix — tatsächliche Fläche Österreichs)

// Aus Schritt 5 ("default"-Variante — geodata/variant_stats.json):
const POTENTIAL_VECTOR_HA = 349_326;

// Aus Schritt 5 — perBundesland-Output (absteigend nach ha sortieren):
const BUNDESLAENDER = [
    { name: "Niederösterreich", short: "NÖ", ha: 152_549 },
    { name: "Burgenland",       short: "B",  ha:  48_772 },
    { name: "Steiermark",       short: "ST", ha:  45_446 },
    { name: "Oberösterreich",   short: "OÖ", ha:  35_966 },
    { name: "Tirol",            short: "T",  ha:  21_194 },
    { name: "Kärnten",          short: "K",  ha:  19_407 },
    { name: "Salzburg",         short: "S",  ha:  18_683 },
    { name: "Vorarlberg",       short: "V",  ha:   5_306 },
    { name: "Wien",             short: "W",  ha:      57 },
];

// Aus scripts/compute_bundesland_areas.py (siehe Schritt 5, "Optional"):
const BUNDESLAND_HA: Record<string, number> = {
    "Niederösterreich": 1_913_316, "Steiermark": 1_629_196, "Tirol": 1_252_069,
    "Oberösterreich": 1_193_705, "Kärnten": 948_875, "Salzburg": 709_212,
    "Burgenland": 395_412, "Vorarlberg": 257_781, "Wien": 41_467,
};
```

> Prosa-Aussagen, die von den Prozentanteilen abhängen (z. B. „mehr als die Hälfte des
> Landes" beim Siedlungsabstand-Schritt), händisch gegen die neuen Prozentsätze prüfen —
> die Anteile verschieben sich bei jedem Datensatz-Update.

### `src/lib/components/Inspector.svelte`

Die Zonenzahl liest sich seit diesem Update automatisch aus `variantStats` (siehe
`src/lib/stores/windStore.ts`) — kein manueller Zahlen-Edit mehr nötig, nur der Fallback-Wert
im Code sollte grob aktuell gehalten werden.

### Prüfliste

- [ ] `SCHUTZ_HA`, `SIEDLUNG_HA`, `SONSTIGE_HA`, `WIND_HA`, `POTENTIAL_HA` aus Script-Output Schritt 1 aktualisiert
- [ ] `BUNDESLAND_HA` aus `scripts/compute_bundesland_areas.py` aktualisiert (falls sich die Österreich-Maske/Bundesland-Grenzen geändert haben)
- [ ] Prozentabhängige Prosa in `Scrollytelling.svelte` geprüft (SEG_*-Anteile ändern sich)
- [ ] `POTENTIAL_VECTOR_HA` + `BUNDESLAENDER`-Array aus `variant_stats.json` (`default`) aktualisiert
- [ ] Bandtabellen in `src/routes/methodik/+page.svelte` mit den echten Bandnamen/-nummern abgeglichen
- [ ] Beide MBTiles hochgeladen und Tileserver neugestartet
- [ ] Tileserver-URLs im Browser geprüft (siehe oben)

---

## Dateien im Repository

| Pfad | Beschreibung | Im Git? |
|---|---|:---:|
| `scripts/raster/osm_wka_distance_zones_widmung.tif` | Quelldaten (extern) | ✗ |
| `scripts/raster/classification.tif` | Prioritäts-Klassenraster | ✗ |
| `scripts/raster/classification_rgba_3857.tif` | RGBA für PNG-Tiles | ✗ |
| `scripts/raster/tiles/` | PNG-Kachelbaum | ✗ |
| `scripts/raster/water_bodies.geojson` | Gewässerflächen WGS84: GGN-Seen + OSM-Flüsse (`fetch_water_bodies.py`) | ✗ |
| `scripts/raster/ggn_stehende_gewaesser/` | GGN-Rohdaten (Shapefile, EPSG:31287) | ✗ |
| `scripts/raster/osm_water_raw.json` | Overpass-Roh-Elemente (Cache, erspart den ~10-min-Fetch) | ✗ |
| `scripts/raster/ktn_windkraftbeschleunigungszone/`, `scripts/raster/bgld_wk_eignungszonen/` | Kärnten/Burgenland-Zonierungs-Shapefiles (`add_ktn_bgld_zoning.py`) | ✗ |
| `scripts/raster/windkraft_classification.mbtiles` | Klassifikation (Raster) | ✗ |
| `scripts/raster/windkraft_exclusion_bands.mbtiles` | Ausschluss-Ebenen (Vektor, 23 Layer) | ✗ |
| `geodata/austria_states.geojson` | GADM Bundeslandgrenzen | ✓ |
| `geodata/austria_outline.geojson` | Österreich-Umriss (aus States) — auch zum Maskieren in Schritt 1 | ✓ |
| `geodata/possible_zones.geojson` / `zone_centroids.geojson` | Default-Variante (Bundesland-spezifisch) | ✓* |
| `geodata/possible_zones_<800\|1000\|1200\|1500\|2000>.geojson` (×5) | Potenzialzonen-Polygone je Vergleichs-Variante | ✓* |
| `geodata/zone_centroids_<800\|1000\|1200\|1500\|2000>.geojson` (×5) | Zentroide für Heatmap je Vergleichs-Variante | ✓* |
| `geodata/variant_stats.json` | Pro-Variante-Kennzahlen (Zonenzahl, ha, Bundesland-Aufteilung) | ✓* |
| `geodata/exclusion_*.geojson` | Story-Ausschluss-Overlays | ✓* |
| `geodata/official_zoning.geojson` | Offizielle Eignungszonen NÖ + Steiermark + Salzburg | ✓ |
| `geodata/existing_turbines.geojson` | Bestandsanlagen | ✓ |
| `geodata/band_*.geojson` (18 Basisbänder + 5 Siedlungsabstand-Varianten) | Tippecanoe-Rohdaten für `windkraft_exclusion_bands.mbtiles` (Zwischenergebnis, ~470 MB) | ✗ |

> \* Die mit ✓* markierten `geodata/*.geojson`-Dateien sind vom SvelteKit-Server
> zur Laufzeit benötigt (`src/routes/data/[name]/+server.ts`) — ohne sie fehlen
> der App Daten. Sie sind trotzdem aus `osm_wka_distance_zones_widmung.tif`
> reproduzierbar, liegen aber im Repo, damit ein Checkout ohne Zugriff auf die
> (gitignorte, 850 MB große) Quelldatei sofort lauffähig ist.
>
> `geodata/band_*.geojson` ist bewusst **nicht** im Git — die App liest diese
> Dateien nie (sie werden nur lokal von Tippecanoe zu
> `windkraft_exclusion_bands.mbtiles` verarbeitet, siehe Schritt 4), und bei
> ~470 MB lohnt sich das Tracking nicht. Nach dem Klonen einmalig Schritt 4a
> laufen lassen, falls die mbtiles neu gebaut werden muss.
>
> Es gibt **keine** separate `possible_zones_default.geojson` /
> `zone_centroids_default.geojson` — `possible_zones.geojson` /
> `zone_centroids.geojson` sind bereits die Default-Variante; beide Namen
> zeigen im `+server.ts` auf dieselbe Datei, um keine ~15 MB doppelt zu halten.

---

## Abhängigkeiten

```bash
# Python-Pakete
pip install rasterio numpy shapely geopandas

# Tippecanoe (macOS)
brew install tippecanoe

# mb-util (für Schritt 2)
pip install mbutil
```
