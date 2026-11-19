// ⚠️ Erzeugt von scripts/generate_bands_config.py — nicht von Hand ändern.
// Quelle: scripts/raster/abschichtung.bands.json
// Bandschema: varianten-50-nov-2026
// Manifest erzeugt: 2026-11-18T14:22:53Z
//
// Layer sind alle Bänder mit `dashboard_layer: true` und `rolle: "bedingung"`,
// plus `exclusion_nature` (widmung_v2 blendet die einzelnen Schutzgebietsbänder
// aus). `slug` ist der Bandname aus dem Manifest und zugleich der Layername in
// den Vektorkacheln und das `source-layer` in MapLibre.

export interface BandDef {
	band: number;
	slug: string;
	label: string;
	description: string;
	color: string; // 8-digit hex RRGGBBAA
	group: BandGroup;
	/** Ersatzbänder je Siedlungsabstands-Variante (Schlüssel aus SETTLEMENT_VARIANTS). */
	variants?: Record<string, string>;
}

export interface SettlementVariantDef {
	key: string;
	label: string;
	description: string;
	isDefault: boolean;
}

// Siedlungsabstands-Varianten aus `varianten` im Manifest (Schema 3.0). Die
// Default-Variante speist Story, Texte und Gemeindezahlen; die übrigen sind
// nur in der Detailansicht wählbar.
export const SETTLEMENT_VARIANTS: SettlementVariantDef[] = [
	{
		key: "default",
		label: "Länderregel",
		description: "1.200 m in Niederösterreich und im Burgenland, sonst 1.000 m.",
		isDefault: true,
	},
	{
		key: "1km",
		label: "1 km überall",
		description: "1.000 m in ganz Österreich.",
		isDefault: false,
	},
	{
		key: "1d2km",
		label: "1,2 km überall",
		description: "1.200 m in ganz Österreich.",
		isDefault: false,
	},
];
export const DEFAULT_VARIANT: string =
	SETTLEMENT_VARIANTS.find((v) => v.isDefault)?.key ?? "default";

/** source-layer eines Bands für die gewählte Variante. */
export function bandSourceLayer(def: BandDef, variant: string): string {
	return def.variants?.[variant] ?? def.slug;
}

export type BandGroup = "human" | "nature" | "terrain" | "wind";

export const BAND_GROUPS: Record<BandGroup, { label: string; color: string }> =
	{
		human: { label: "Mensch", color: "#f97316" },
		nature: { label: "Naturschutz", color: "#16a34a" },
		terrain: { label: "Gelände & Topografie", color: "#78716c" },
		wind: { label: "Windpotenzial", color: "#475569" },
	};

export const BAND_DEFS: BandDef[] = [
	{
		band: 2,
		slug: "settlement_buffer",
		label: "Siedlungsabstand",
		description:
			"Abstand von 1.000 m um amtliches Wohn-, Misch-, Kern- und Dorfgebiet aller neun Bundesländer; in Niederösterreich und im Burgenland 1.200 m.",
		color: "#4682dc8c",
		group: "human",
		variants: { "1km": "settlement_buffer_1km", "1d2km": "settlement_buffer_1d2km" },
	},
	{
		band: 7,
		slug: "haeuser_im_gruenen",
		label: "Häuser im Grünen (750 m)",
		description:
			"Abstand von 750 m um amtliche Sonderwidmungen außerhalb des Baulands (die Liste der Widmungsarten unterscheidet sich je Bundesland) und um bewohnte Streusiedlungen mit mindestens fünf Adressen, erkannt aus Kataster und Adressregister. In Niederösterreich gelten stattdessen die amtlichen Mindestabstandszonen des Sektoralen Raumordnungsprogramms, die den Abstand bereits enthalten. Einzelne Häuser und Gruppen mit weniger als fünf Adressen erhalten nur den Gebäudeabstand von 25 m.",
		color: "#ff8c3c96",
		group: "human",
	},
	{
		band: 9,
		slug: "nonresidential_hulls_buffer",
		label: "Ausschluss Nicht-Wohn-Hüllen (25 m)",
		description:
			"Abstand von 25 m um unbewohnte und industrieartige Kataster-Hüllen; das entspricht praktisch dem Fußabdruck.",
		color: "#b4b4b482",
		group: "human",
	},
	{
		band: 11,
		slug: "cableway_buildings_buffer",
		label: "Ausschluss Seilbahn-Gebäude (50 m)",
		description:
			"Abstand von 50 m um Gebäude an Seilbahnlinien.",
		color: "#50bebe96",
		group: "human",
	},
	{
		band: 13,
		slug: "general_buildings_buffer",
		label: "Ausschluss sonstige Gebäude (25 m)",
		description:
			"Abstand von 25 m um sonstige Gebäude und Einzellagen; das entspricht praktisch dem Fußabdruck.",
		color: "#b478dc96",
		group: "human",
	},
	{
		band: 14,
		slug: "road_motorway_trunk",
		label: "Autobahnen und Schnellstraßen (150 m)",
		description:
			"Abstand von 150 m beiderseits von Autobahnen und Schnellstraßen aus OpenStreetMap. Als Tunnel ausgewiesene Abschnitte bleiben unberücksichtigt.",
		color: "#ff8c0096",
		group: "human",
	},
	{
		band: 15,
		slug: "road_federal_state",
		label: "Bundes- und Landesstraßen (150 m)",
		description:
			"Abstand von 150 m beiderseits von Bundes- und Landesstraßen aus OpenStreetMap, einschließlich der nachgeordneten Landesstraßen. Als Tunnel ausgewiesene Abschnitte bleiben unberücksichtigt.",
		color: "#ffb40091",
		group: "human",
	},
	{
		band: 16,
		slug: "rail_main",
		label: "Hauptbahnen (150 m)",
		description:
			"Abstand von 150 m beiderseits von Haupt- und Schmalspurbahnen aus OpenStreetMap. Als Tunnel ausgewiesene Abschnitte bleiben unberücksichtigt.",
		color: "#78502896",
		group: "human",
	},
	{
		band: 17,
		slug: "cableway_people_150m",
		label: "Personenseilbahnen (150 m)",
		description:
			"Abstand von 150 m um Personenseilbahnen aus OpenStreetMap: Gondelbahnen, Kabinen- und Pendelbahnen, Sessellifte und Kombibahnen. Schlepplifte und Materialseilbahnen erzeugen keine Zone.",
		color: "#ff00008c",
		group: "human",
	},
	{
		band: 18,
		slug: "military_restricted_area",
		label: "Militärische Flächen",
		description:
			"Militärische Flächen aus OpenStreetMap, ohne zusätzlichen Abstand: Truppen- und Schießübungsplätze, Kasernen, Gefahrengebiete, Militärflugplätze, Marinestützpunkte und sonstige militärische Anlagen sowie Munitionslager.",
		color: "#ff00008c",
		group: "human",
	},
	{
		band: 19,
		slug: "airport_area_major",
		label: "Hauptflughafen-Areale",
		description:
			"Areale der Hauptflughäfen aus OpenStreetMap, ohne zusätzlichen Abstand.",
		color: "#ff00008c",
		group: "human",
	},
	{
		band: 20,
		slug: "airport_runway_corridor_5km",
		label: "An- und Abflugkorridore",
		description:
			"Korridore ab beiden Landebahn-Enden der Hauptflughäfen: 5 km lang, ±15 Grad um die verlängerte Bahnachse.",
		color: "#ff00ff6e",
		group: "human",
	},
	{
		band: 22,
		slug: "geography_slope_too_steep",
		label: "Hangneigung zu steil",
		description:
			"Hangneigung über 15 Grad. Das Geländemodell mit 25 m Auflösung wird in 4×4-Blöcken zu 100-m-Zellen gemittelt, die Neigung aus der 3×3-Nachbarschaft dieses Rasters (rund 300 m) berechnet.",
		color: "#78461e96",
		group: "terrain",
	},
	{
		band: 23,
		slug: "geography_elevation_too_high",
		label: "Seehöhe zu hoch",
		description:
			"Seehöhe über 2.500 m, ermittelt aus dem Geländemodell mit 25 m Auflösung.",
		color: "#78787896",
		group: "terrain",
	},
	{
		band: 24,
		slug: "geography_wind_too_low",
		label: "Wind zu gering",
		description:
			"Windleistungsdichte in 150 m Höhe unter rund 160 W/m², aus dem Globalen Windatlas. Der Grenzwert entspricht 150 W/m² in 130 m Höhe, mit dem Windprofil auf 150 m hochgerechnet.",
		color: "#50a0ff91",
		group: "wind",
	},
	{
		band: 25,
		slug: "geography_water_bodies",
		label: "Größere Gewässer",
		description:
			"Seen, Stauseen und Flüsse aus OpenStreetMap, zusammenhängende Wasserflächen ab 1 ha.",
		color: "#005aaaaa",
		group: "terrain",
	},
	{
		band: 27,
		slug: "exclusion_nature",
		label: "Ausschluss Natur",
		description:
			"Amtliche Schutzgebiete, die nach Naturschutzrecht der Länder per Verordnung oder Bescheid festgelegt sind, einschließlich Naturdenkmälern (siehe „Amtliche Schutzgebiete“), auf das Staatsgebiet zugeschnitten. Ohne Abstandspuffer.",
		color: "#00b40096",
		group: "nature",
	},
	{
		band: 40,
		slug: "power_lines_110kv_plus",
		label: "Hochspannungsfreileitungen (136 m)",
		description:
			"Freileitungen ab 110 kV aus OpenStreetMap, als Streifen beiderseits der Leitungsachse: 116 m bei 110 kV, 136 m bei 220, 380 und 400 kV. Leitungen mit mehreren Spannungsebenen erhalten den größeren Abstand. Mittelspannung unter 110 kV und Erdkabel erzeugen keine Zone; die Herleitung steht im Whitepaper.",
		color: "#9632dc96",
		group: "human",
	},
];

export const GROUP_ORDER: BandGroup[] = ["human", "nature", "terrain", "wind"];

export function bandLayerId(slug: string): string {
	return `detail-${slug}-fill`;
}

export function bandSourceId(slug: string): string {
	return `detail-${slug}`;
}

export const EXCLUSION_BANDS_SOURCE = "exclusion-bands";
export const EXCLUSION_BANDS_TILES =
	"https://tiles.klimadashboard.org/data/windkraft_exclusion_bands_v3/{z}/{x}/{y}.pbf";
