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
                  └─▶ geodata/possible_zones.geojson
                      geodata/zone_centroids.geojson
                      geodata/zone_stats.json
```

Danach in Schritt 6 die App-Konstanten aktualisieren.

---

## Lieferung widmung_v2 (9.9.2026) — Teilstand

Neues Paket vom Datenanbieter: `abschichtung.tif` (153 MB, sha256
`c1809c4cf9cb243d420efc949ff5543130ef3c5a75db9e948d2ea53c94416f37`),
`abschichtung.bands.json` (Manifest 2.2.1), `LAYER.md`, `LAYER-MANIFEST.md`.
Bandschema `clean-44-ohne-wichtige-objekte-aug-2026`, Pipeline `widmung_v2`,
44 Bänder, EPSG:31287, 24001×14001, 25 m. Geprüft: alle 44 Bandnamen im TIF
stimmen mit dem Manifest überein, Rasterblock im Manifest passt zum File.

**Stand: vollständig auf widmung_v2 umgestellt (10.9.2026)**

| Schritt | Stand |
|---|---|
| 1 Klassifikationsraster | neu — Codes 9 und 10 stillgelegt, 15 (Nicht-Wohn-Hüllen) und 16 (Gewässer) neu |
| 2 Rasterkacheln | **nicht gelaufen, bewusst** — der Layer `classification-raster` wird in der App nie sichtbar geschaltet |
| 3 Ausschluss-GeoJSONs (Story) | neu |
| 4 Detailansicht-Vektorkacheln | neu — 17 Layer statt 23, Layernamen sind jetzt die Bandnamen des Manifests |
| 5 Potenzialflächen | neu — 3.812 Flächen, 365.161 ha (vorher 4.093 / 351.912) |
| 5b Gemeinde-Kennzahlen | neu |
| 6 App-Konstanten | alle fünf Balkenwerte plus `POTENTIAL_VECTOR_HA` und `BUNDESLAENDER` |

**Die Layerliste ist nicht mehr handgepflegt.** `scripts/generate_bands_config.py`
erzeugt `src/lib/config/bands.ts` aus dem Manifest, `extract_band_geojson.py` liest
dieselbe Auswahl, und die Methodik-Seite rendert die Bandtabelle direkt aus
`src/lib/data/abschichtung.bands.json`. Nach einer neuen Lieferung genügt es, das
Manifest zu ersetzen und die Skripte laufen zu lassen.

**Klassencodes:** 9 (Wichtige Objekte) und 10 (Freileitung 380/400 kV) sind
stillgelegt und werden nicht neu vergeben, damit ältere Kacheln lesbar bleiben.

**Was noch aussteht — und warum**

- Das Manifest-Dokument beschreibt in Abschnitt 6 ein Ziel-Dashboard mit 17 Layern
  und setzt dafür drei neue Sammelbänder 45–47 voraus (`gebaeude_zone`,
  `verkehr_zone`, `luftfahrt_zone`). Die sind in diesem TIF **nicht enthalten**.
  Wir kommen mit den Detailbändern auf dieselben 17 Layer; sobald W7.8 kommt,
  ersetzen die drei Sammelbänder die neun Detailbänder von Gebäuden, Verkehr und
  Luftfahrt. `generate_bands_config.py` zieht das dann automatisch nach.
- Der Bedienfeld-Baum aus dem Manifest (Kategorie → Familie → Stufe) ist **nicht**
  umgesetzt; das Panel gruppiert weiter nach `BandGroup`. Das ist die eigentliche
  W7.8-Arbeit.

**Offene Punkte beim Anbieter**

| | |
|---|---|
| Siedlungsabstands-Varianten | `SETTLEMENT_BUFFER_VARIANTS` ist `{}`, die Kategorie „Siedlungsabstand-Varianten" hat 0 Bänder. **Am 10.9.2026 auf Entscheidung ersatzlos entfernt** — die zehn `possible_zones_*`/`zone_centroids_*`-Dateien, `variants.ts`, der `settlementVariant`-Store und die Variantenspalten in `region_stats.json` sind weg. Ein Szenario, ein Datensatz |
| `wka_bestand_punkte.geojson` | in der Übergabetabelle des Manifests genannt, im Paket nicht enthalten; `existing_turbines.geojson` bleibt auf dem alten Stand |
| Siedlungsabstand je Bundesland | neu NÖ 1.200 m, alle übrigen 1.000 m (vorher Kärnten 1.500, Burgenland/NÖ 1.200). Erklärt den Sprung in Burgenland (48.457 → 71.014 ha) und Kärnten (19.613 → 25.420 ha) |
| Windschwelle | jetzt 150 W/m² bei **130 m** Nabenhöhe (≙ 159,5 W/m² @150 m), vorher @150 m. Legende und FAQ sagen noch „@150 m" |
| **Freileitungen ganz entfallen** | `POWER_LINES = "kein Ausschlusskriterium (Clean-Schema Aug 2026)"`. Es gibt kein Band mehr — auch 380/400 kV sind raus, nicht nur die 110 kV. Damit ist die Entscheidung vom 8.9.2026, bei 380 kV zu bleiben, gegenstandslos, solange das Band nicht zurückkommt |
| Windleistungsdichte je Fläche | das Raster liefert nur ein binäres „Wind zu gering"-Band. Laut `LAYER.md` liegt beim Anbieter `data/gelaende/AUT_power-density_150m.tif` (Stand 29.3.2026) — genau das bräuchten wir für `pd_mean_w_m2` |

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
aufgebaut — 18 Layer in einer einzigen mbtiles. Die GeoJSONs werden bei
**voller 25-m-Auflösung** erzeugt, damit die Grenzen exakt mit den Potenzialzonen aus
Schritt 5 übereinstimmen.

### 4a – GeoJSONs extrahieren

```bash
python scripts/extract_band_geojson.py
```

Schreibt `geodata/band_01_human_settlement.geojson` … `band_18_geo_wind.geojson`
(18 Bänder). Die früheren fünf Siedlungsabstands-Varianten-Layer entfielen am
10.9.2026 zusammen mit dem Rest der Variantenlogik.

Jedes Band wird vor dem Vektorisieren auf `geodata/austria_outline.geojson` maskiert
(`load_austria_mask()`) — mehrere Quellbänder (v. a. `geography_wind_too_low`) sind
selbst nicht auf Österreich geclippt und würden sonst weit ins benachbarte Ausland
(Bayern, Südtirol, Slowenien …) hineinreichen, sichtbar z. B. im Experten-Panel als
riesige „Wind zu gering"-Fläche außerhalb der Landesgrenze.

Alle Features tragen eine stabile `band_id` (1–18, s. Tabelle unten), an der Legende und
Hover-Tooltip hängen.

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
# Layerliste kommt aus dem Manifest — nie von Hand pflegen, sonst laufen
# Kacheln, bands.ts und Legende auseinander.
LAYERS=$(python3 -c "
import json,sys; sys.path.insert(0,'scripts')
from generate_bands_config import MANIFEST, select_bands
m=json.load(open(MANIFEST))
print(' '.join(f'-L {b[\"name\"]}:geodata/{b[\"name\"]}.geojson' for b in select_bands(m)))
")

tippecanoe \
  --output scripts/raster/windkraft_exclusion_bands.mbtiles \
  --force \
  --minimum-zoom=5 --maximum-zoom=14 \
  --no-tile-size-limit --simplification=4 --detect-shared-borders --no-tile-stats \
  $LAYERS
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

## Schritt 5 – Potenzialzonen-GeoJSONs

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

`extract_possible_zones.py` liest das Ergebnisband (`available_cleaned_min_10ha` in
widmung_v2, `…_default` in widmung_v1), maskiert auf Österreich und schreibt:

- `geodata/possible_zones.geojson` — Polygone mit Bundesland-Zuweisung und Turbinenzählung
- `geodata/zone_centroids.geojson` — Zentroide (Gewicht `w`) für den Heatmap-Layer
- `geodata/zone_stats.json` — `{count, totalHa, perBundesland}`, gelesen von Inspector
  und Scrollytelling

Bis 10.9.2026 entstanden hier zusätzlich fünf uniforme Siedlungsabstands-Szenarien
(800/1000/1200/1500/2000 m). Sie waren im UI nie erreichbar und fehlen in widmung_v2;
sie wurden deshalb ersatzlos entfernt.

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

## Schritt 5b – Gemeinde-Kennzahlen (`region_stats.json`)

```bash
# Amtliche Gemeindegrenzen holen (einmalig je Jahrgang)
curl -L -A "Mozilla/5.0" -o /tmp/gem.zip \
  "https://www.statistik.gv.at/gs-open/GEODATA/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=GEODATA:STATISTIK_AUSTRIA_GEM_20260101&outputFormat=SHAPE-ZIP&format_options=CHARSET:UTF-8"
unzip -q /tmp/gem.zip -d /tmp/gemeinden

python scripts/build_region_stats.py --gemeinden /tmp/gemeinden
```

Verschneidet `possible_zones*.geojson` (alle 6 Varianten), `official_zoning.geojson` und
`existing_turbines.geojson` mit den **amtlichen Gemeindegrenzen der Statistik Austria**
(EPSG:31287, CC-BY 4.0) und schreibt `geodata/region_stats.json` — je Gemeindekennziffer
Potenzialflächen, offizielle Zone und Bestandsanlagen. Die App liest diese Tabelle und
aggregiert Bezirke und Bundesländer über das GKZ-Präfix.

**Warum vorberechnet:** die Zahlen kamen früher zur Laufzeit aus
`queryRenderedFeatures` über die **Bounding Box** des Gemeindeumrisses. Eine Box ist
keine Gemeinde — Hausleiten bekam so die Windkraftzone der Nachbargemeinde Rußbach
zugeschrieben. Die Anlagenzahl stammte zudem aus `n_existing_turbines` der
Potenzialflächen, wodurch Anlagen außerhalb jeder Potenzialfläche unsichtbar blieben
(Munderfing: 6 Anlagen, angezeigt 0).

**Trotzdem nicht die `outline`-Geometrien der Regions-API verwenden.** Die waren bis
8.9.2026 einheitlich rund **205 m nach Westen und 77 m nach Norden versetzt** — MGI
(EPSG:31287) → WGS84 ohne Datumstransformation. Gemessen gegen OSM-Verwaltungsgrenzen an
Hausleiten (+201/+205 m), Rußbach (+206 m) und Munderfing (+208/+213 m), jeweils −77 m in
der Breite. Der Kacheldatensatz `tiles.klimadashboard.org/data/municipalities-at`
(© Statistik Austria) war nie betroffen und deckt sich metergenau mit OSM — deshalb
zeichnet die App den Auswahlrahmen aus den Kacheln und nicht aus der API-Geometrie.

> **Behoben am 9.9.2026.** Alle 2.116 österreichischen Gemeinden haben `outline` und
> `outline_simple` aus der amtlichen Lieferung neu bekommen (flow-Repository,
> `manual/wip/fix-at-outlines`). Restversatz im Median 0 m, keine Gemeinde weicht um mehr
> als 25 m ab, IoU gegen die amtliche Grenze im Median 0,996. Die Bezirke waren nie
> betroffen und blieben unangetastet. Für die Verschneidung hier bleibt die amtliche
> Quelle maßgeblich: die API-Umrisse sind für den Transport auf rund 200 Stützpunkte
> vereinfacht, was an Gemeindegrenzen ein paar Hektar hin oder her ausmacht.

**Bekannte Mängel der Lieferung** (an den Datenanbieter gemeldet, im Skript abgefangen):

| Problem | Umfang | Umgang im Skript |
|---|---|---|
| Anlagen auf Koordinate `[0, 0]` | 8 von 1.396 | Über den Gemeindenamen zugeordnet (6), 2 bleiben offen |
| Länge/Breite vertauscht | 2 (Leoben, Potzneusiedl) | Automatisch erkannt und getauscht |
| `pd_mean_w_m2` durchgehend 0 | alle 4.093 Flächen | Windleistungsdichte wird nicht ausgewiesen |
| `zone_type` fehlt bei Stmk/Sbg/NÖ | 99 von 143 Zonen | Gilt als positiv ausgewiesene Zone |
| `communities` fehlt | 32 von 143 Zonen | Zuordnung rein geometrisch |

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
| `geodata/region_stats.json` | Kennzahlen je Gemeinde (`build_region_stats.py`, Schritt 5b) | ✓ |
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
