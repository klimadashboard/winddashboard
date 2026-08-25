import type { SettlementVariant } from "./variants";

export interface BandDef {
	band: number;
	slug: string;
	label: string;
	description: string;
	color: string; // 8-digit hex RRGGBBAA
	group: BandGroup;
	// Only the settlement band (band 1) has variant-specific slugs — every other
	// band is identical across all 6 settlement-distance scenarios.
	variantSlugs?: Record<SettlementVariant, string>;
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
		band: 1,
		slug: "band_01_human_settlement",
		label: "Siedlungsabstand",
		description:
			"Mindestabstand zu Wohngebäuden und Siedlungen (bundeslandspezifisch, 1.000–1.500 m)",
		color: "#f97316cc",
		group: "human",
		variantSlugs: {
			default: "band_01_human_settlement",
			"800": "band_01_human_settlement_800",
			"1000": "band_01_human_settlement_1000",
			"1200": "band_01_human_settlement_1200",
			"1500": "band_01_human_settlement_1500",
			"2000": "band_01_human_settlement_2000",
		},
	},
	{
		band: 2,
		slug: "band_02_human_important_objects",
		label: "Wichtige Objekte",
		description:
			"Pufferzone (250 m) um besonders schutzwürdige Einzelobjekte — vorläufige Kategorie, genaue fachliche Definition noch nicht dokumentiert",
		color: "#9a3412a6",
		group: "human",
	},
	{
		band: 3,
		slug: "band_03_human_cableway_buildings",
		label: "Gebäude an Seilbahnen",
		description:
			"Pufferzone (50 m) um Gebäude an Seilbahnen — vorläufige Kategorie, genaue fachliche Definition noch nicht dokumentiert",
		color: "#c2410c8c",
		group: "human",
	},
	{
		band: 4,
		slug: "band_04_human_haeuser_im_gruenen",
		label: "Haus im Grünen",
		description: "Mindestabstand (750 m) zu Einzelgebäuden außerhalb von Siedlungen",
		color: "#fb923ca6",
		group: "human",
	},
	{
		band: 5,
		slug: "band_05_human_general_buildings",
		label: "Allgemeine Gebäude",
		description:
			"Pufferzone (25 m) um sonstige Gebäude — vorläufige Kategorie, genaue fachliche Definition noch nicht dokumentiert",
		color: "#fdba7482",
		group: "human",
	},
	{
		band: 6,
		slug: "band_06_human_power_380kv",
		label: "Freileitung 380/400 kV",
		description: "Pufferzone von 150 m entlang Hochspannungsfreileitungen (380/400 kV)",
		color: "#fbbf2496",
		group: "human",
	},
	{
		band: 7,
		slug: "band_07_human_road_motorway",
		label: "Autobahn/Schnellstraße",
		description: "Pufferzone von 150 m entlang Autobahnen und Schnellstraßen",
		color: "#f59e0b96",
		group: "human",
	},
	{
		band: 8,
		slug: "band_08_human_road_federal",
		label: "Bundes-/Landesstraße",
		description: "Pufferzone von 150 m entlang Bundes- und Landesstraßen",
		color: "#d9770696",
		group: "human",
	},
	{
		band: 9,
		slug: "band_09_human_rail",
		label: "Hauptbahn",
		description: "Pufferzone von 150 m entlang Haupteisenbahnstrecken",
		color: "#b45309a6",
		group: "human",
	},
	{
		band: 10,
		slug: "band_10_human_cableway_people",
		label: "Seilbahn",
		description: "Pufferzone von 150 m entlang Personenseilbahnen und Liften",
		color: "#92400e8c",
		group: "human",
	},
	{
		band: 11,
		slug: "band_11_human_military",
		label: "Militärsperrzone",
		description: "Sperrzone rund um militärische Gebiete",
		color: "#ef444496",
		group: "human",
	},
	{
		band: 12,
		slug: "band_12_human_airport",
		label: "Flughafen",
		description: "Sperrzone rund um Flughäfen und Flugplätze",
		color: "#dc262696",
		group: "human",
	},
	{
		band: 13,
		slug: "band_13_human_airport_lateral",
		label: "Flughafen Seitenbereich",
		description: "6-km-Prüfzone seitlich der sechs großen Verkehrsflughäfen",
		color: "#b91c1c8c",
		group: "human",
	},
	{
		band: 14,
		slug: "band_14_nature_protection",
		label: "Schutzgebiet (gesetzlich)",
		description: "Nationalpark, Naturschutzgebiet, Natura 2000, Ramsar-Gebiet",
		color: "#16a34ab0",
		group: "nature",
	},
	{
		band: 15,
		slug: "band_15_nature_osm",
		label: "Schutzgebiet (OSM)",
		description: "Weitere Schutzgebiete aus OpenStreetMap-Daten",
		color: "#4ade8096",
		group: "nature",
	},
	{
		band: 16,
		slug: "band_16_geo_slope",
		label: "Hangneigung >15°",
		description: "Gelände mit einer Neigung von mehr als 15 Grad",
		color: "#a8a29ea6",
		group: "terrain",
	},
	{
		band: 17,
		slug: "band_17_geo_elevation",
		label: "Seehöhe >2500 m",
		description: "Flächen über 2.500 m Seehöhe",
		color: "#d6d3d196",
		group: "terrain",
	},
	{
		band: 18,
		slug: "band_18_geo_wind",
		label: "Windleistung <150 W/m²",
		description:
			"Windleistungsdichte (@150 m) unter 150 W/m² oder keine Winddaten verfügbar",
		color: "#64748ba6",
		group: "wind",
	},
];

export const GROUP_ORDER: BandGroup[] = ["human", "nature", "terrain", "wind"];

// Single vector-tile source (TileServer GL) — all 16 bands as source-layers.
// Upload scripts/raster/windkraft_exclusion_bands.mbtiles to the tile server,
// then add to config.json:  "windkraft-exclusion-bands": { "mbtiles": "windkraft_exclusion_bands.mbtiles" }
export const EXCLUSION_BANDS_SOURCE = "exclusion-bands";
export const EXCLUSION_BANDS_TILES =
	"https://tiles.klimadashboard.org/data/windkraft_exclusion_bands/{z}/{x}/{y}.pbf";

export function bandLayerId(slug: string) {
	return `detail-${slug}-fill`;
}
export function bandSourceId(slug: string) {
	return `detail-${slug}`;
}
