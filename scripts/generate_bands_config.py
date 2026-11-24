#!/usr/bin/env python3
"""Erzeugt src/lib/config/bands.ts aus dem Bandmanifest des Datenanbieters.

Warum generiert statt gepflegt
------------------------------
Bis widmung_v1 stand die Layerliste der Detailansicht als handgeschriebene
Tabelle in `bands.ts` **und** noch einmal als `BAND_SLUGS` in
`extract_band_geojson.py`. Bei jedem Schemawechsel mussten beide nachgezogen
werden, und die Slugs (`band_06_human_power_380kv`) hatten mit den Bandnamen der
Lieferung nichts mehr zu tun.

Das Manifest schreibt dazu selbst vor (LAYER-MANIFEST.md, Abschnitt 3.2): der
Bandname ist zugleich Dateiname der GeoJSON, Layername in den Vektorkacheln,
`source-layer` in MapLibre und Schlüssel im Sichtbarkeits-Store. Es gibt keine
Dashboard-eigenen Slugs mehr.

Welche Bänder Layer werden
--------------------------
Alle Bänder mit `dashboard_layer: true` **und** `rolle: "bedingung"` — also die
eigentlichen Ausschlussgründe, nicht die Summen- und Ergebnisbänder. Dazu kommt
`exclusion_nature`, weil widmung_v2 die beiden einzelnen Schutzgebietsbänder
ausblendet und die Detailansicht sonst gar keine Naturschutzebene hätte.

Aufruf
------
    python scripts/generate_bands_config.py
"""

from __future__ import annotations

import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(REPO, "scripts/raster/abschichtung.bands.json")
OUT = os.path.join(REPO, "src/lib/config/bands.ts")

# Kachel-ID auf dem Tileserver. Neue Lieferungen bekommen eine neue ID statt die
# alte Datei zu überschreiben — sonst passen bis zum Deploy die band_id in den
# Kacheln nicht mehr zu bands.ts der Live-Seite. Lokal heißt die Datei weiter
# windkraft_exclusion_bands.mbtiles, hochgeladen wird sie als <TILESET_ID>.mbtiles.
TILESET_ID = "windkraft_exclusion_bands_v3"

# Zusätzlich zu den "bedingung"-Bändern aufgenommen, siehe Modulkopf.
EXTRA_BANDS = ["exclusion_nature"]

# Manifest-Kategorie → Gruppe im Bedienfeld. Der Windlayer bekommt eine eigene
# Gruppe, weil "zu wenig Wind" kein Geländemerkmal ist.
GROUP_BY_CATEGORY = {
    "Mensch": "human",
    "Natur": "nature",
    "Geografie": "terrain",
}
GROUP_OVERRIDES = {"geography_wind_too_low": "wind"}


def to_hex(rgba) -> str:
    """[r, g, b, a] → #RRGGBBAA. Alpha kommt als 0..1 oder 0..255."""
    r, g, b, a = (list(rgba) + [255])[:4]
    alpha = round(a * 255) if isinstance(a, float) and a <= 1 else round(a)
    return "#{:02x}{:02x}{:02x}{:02x}".format(
        int(r) & 255, int(g) & 255, int(b) & 255, max(0, min(255, alpha))
    )


def escape(text: str) -> str:
    return (text or "").replace("\\", "\\\\").replace('"', '\\"')


def select_bands(manifest: dict) -> list[dict]:
    chosen = [
        b for b in manifest["bands"]
        if b.get("dashboard_layer") is not False and b.get("rolle") == "bedingung"
        and not b.get("variante_von")
    ]
    by_name = {b["name"]: b for b in manifest["bands"]}
    for name in EXTRA_BANDS:
        if name in by_name and by_name[name] not in chosen:
            chosen.append(by_name[name])
    chosen.sort(key=lambda b: b["index"])
    return chosen


def variant_bands(manifest: dict, base: dict) -> dict[str, dict]:
    """Varianten eines Bands ({Variantenschlüssel: Band}), seit Schema 3.0.

    Die Varianten tragen `dashboard_layer: false` — sie sind kein eigener
    Schalter, sondern ersetzen ihr Default-Band, wenn in der Detailansicht eine
    andere Siedlungsabstands-Variante gewählt ist.
    """
    return {
        b["variante"]: b for b in manifest["bands"]
        if b.get("variante_von") == base["name"]
    }


def variant_layer_bands(manifest: dict) -> list[dict]:
    """Alle Variantenbänder der gewählten Layer — für Extraktion und Kacheln."""
    out = []
    for b in select_bands(manifest):
        out.extend(variant_bands(manifest, b).values())
    return sorted(out, key=lambda b: b["index"])


def main() -> None:
    if not os.path.exists(MANIFEST):
        sys.exit(f"Manifest fehlt: {MANIFEST}")
    with open(MANIFEST, encoding="utf-8") as fh:
        manifest = json.load(fh)

    bands = select_bands(manifest)
    lines = []
    for b in bands:
        group = GROUP_OVERRIDES.get(b["name"], GROUP_BY_CATEGORY.get(b["category"], "human"))
        label = b.get("label_de") or b["name"]
        desc = b.get("description_de") or ""
        if b.get("puffer_m"):
            metres = f"{b['puffer_m']:,.0f}".replace(",", ".")
            label = f"{label} ({metres} m)" if "(" not in label else label
        variants = variant_bands(manifest, b)
        variant_line = ""
        if variants:
            entries = ", ".join(f'"{k}": "{v["name"]}"' for k, v in variants.items())
            variant_line = f"\t\tvariants: {{ {entries} }},\n"
        lines.append(
            "\t{\n"
            f"\t\tband: {b['index']},\n"
            f'\t\tslug: "{b["name"]}",\n'
            f'\t\tlabel: "{escape(label)}",\n'
            f'\t\tdescription:\n\t\t\t"{escape(desc)}",\n'
            f'\t\tcolor: "{to_hex(b["color_rgba"])}",\n'
            f'\t\tgroup: "{group}",\n'
            f"{variant_line}"
            "\t},"
        )
    variant_defs = []
    for v in manifest.get("varianten", []):
        variant_defs.append(
            "\t{\n"
            f'\t\tkey: "{v["key"]}",\n'
            f'\t\tlabel: "{escape(v.get("label_de") or v["key"])}",\n'
            f'\t\tdescription: "{escape(v.get("description_de") or "")}",\n'
            f'\t\tisDefault: {"true" if v.get("default") else "false"},\n'
            "\t},"
        )

    generated = manifest.get("generated_at", "?")
    schema = manifest.get("band_schema", "?")
    content = f'''import {{ TILE_SERVER_BASE }} from "./tiles";
// ⚠️ Erzeugt von scripts/generate_bands_config.py — nicht von Hand ändern.
// Quelle: scripts/raster/abschichtung.bands.json
// Bandschema: {schema}
// Manifest erzeugt: {generated}
//
// Layer sind alle Bänder mit `dashboard_layer: true` und `rolle: "bedingung"`,
// plus `exclusion_nature` (widmung_v2 blendet die einzelnen Schutzgebietsbänder
// aus). `slug` ist der Bandname aus dem Manifest und zugleich der Layername in
// den Vektorkacheln und das `source-layer` in MapLibre.

export interface BandDef {{
\tband: number;
\tslug: string;
\tlabel: string;
\tdescription: string;
\tcolor: string; // 8-digit hex RRGGBBAA
\tgroup: BandGroup;
\t/** Ersatzbänder je Siedlungsabstands-Variante (Schlüssel aus SETTLEMENT_VARIANTS). */
\tvariants?: Record<string, string>;
}}

export interface SettlementVariantDef {{
\tkey: string;
\tlabel: string;
\tdescription: string;
\tisDefault: boolean;
}}

// Siedlungsabstands-Varianten aus `varianten` im Manifest (Schema 3.0). Die
// Default-Variante speist Story, Texte und Gemeindezahlen; die übrigen sind
// nur in der Detailansicht wählbar.
export const SETTLEMENT_VARIANTS: SettlementVariantDef[] = [
{chr(10).join(variant_defs)}
];
export const DEFAULT_VARIANT: string =
\tSETTLEMENT_VARIANTS.find((v) => v.isDefault)?.key ?? "default";

/** source-layer eines Bands für die gewählte Variante. */
export function bandSourceLayer(def: BandDef, variant: string): string {{
\treturn def.variants?.[variant] ?? def.slug;
}}

export type BandGroup = "human" | "nature" | "terrain" | "wind";

export const BAND_GROUPS: Record<BandGroup, {{ label: string; color: string }}> =
\t{{
\t\thuman: {{ label: "Mensch", color: "#f97316" }},
\t\tnature: {{ label: "Naturschutz", color: "#16a34a" }},
\t\tterrain: {{ label: "Gelände & Topografie", color: "#78716c" }},
\t\twind: {{ label: "Windpotenzial", color: "#475569" }},
\t}};

export const BAND_DEFS: BandDef[] = [
{chr(10).join(lines)}
];

export const GROUP_ORDER: BandGroup[] = ["human", "nature", "terrain", "wind"];

export function bandLayerId(slug: string): string {{
\treturn `detail-${{slug}}-fill`;
}}

export function bandSourceId(slug: string): string {{
\treturn `detail-${{slug}}`;
}}

export const EXCLUSION_BANDS_SOURCE = "exclusion-bands";
export const EXCLUSION_BANDS_TILES = `${{TILE_SERVER_BASE}}/data/{TILESET_ID}/{{z}}/{{x}}/{{y}}.pbf`;
'''
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(content)
    print(f"→ {OUT}: {len(bands)} Layer")
    for b in bands:
        print(f"   {b['index']:2}  {b['name']:34} {b.get('label_de','')}")


if __name__ == "__main__":
    main()
