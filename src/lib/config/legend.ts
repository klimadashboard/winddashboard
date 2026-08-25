export interface LegendCode {
	code: number;
	name: string;
	group: 'none' | 'exclusion' | 'terrain' | 'wind' | 'suitable';
	color: string; // hex RRGGBBAA  e.g. "#2563ebdc"
	description: string;
}

// Colors are kept in sync with:
//   scripts/convert_raster.py  COLORMAP
//   Map.svelte                  fill-color / line-color for possible-zones
//   MapTooltip.svelte           classColor()
//
// Palette logic:
//   Suitable  → blue family (matching the simple-view vector fills)
//   Wind      → slate grey  (neutral, "not enough energy")
//   Terrain   → stone grey  (topographic, neutral)
//   Exclusion → semantic: green = nature, orange/red = infrastructure & safety
export const LEGEND_CODES: LegendCode[] = [
	{ code: 0,  name: 'Außerhalb',             group: 'none',      color: '#ffffff00', description: 'Außerhalb Österreichs' },
	{ code: 1,  name: 'Schutzgebiet',           group: 'exclusion', color: '#4ade8096', description: 'Nationalpark, Naturschutzgebiet, Natura 2000 oder Ramsar-Gebiet' },
	{ code: 2,  name: 'Siedlungsabstand',       group: 'exclusion', color: '#f9731696', description: 'Mindestabstand zu Wohngebäuden und Siedlungen (bundeslandspezifisch, 1.000–1.500 m)' },
	{ code: 3,  name: 'Haus im Grünen',         group: 'exclusion', color: '#fb923c8c', description: 'Mindestabstand (750 m) zu Einzelgebäuden außerhalb von Siedlungen' },
	{ code: 4,  name: 'Sperrzone',               group: 'exclusion', color: '#ef444496', description: 'Sperrzone rund um Flughäfen, Flugplätze und militärische Sperrbereiche' },
	{ code: 5,  name: 'Verkehrsweg (150 m)',    group: 'exclusion', color: '#facc158c', description: 'Pufferzone von 150 m entlang Straßen, Autobahnen und Personenseilbahnen' },
	{ code: 6,  name: 'Eisenbahn (150 m)',      group: 'exclusion', color: '#eab3088c', description: 'Pufferzone von 150 m entlang Eisenbahnstrecken' },
	{ code: 7,  name: 'Hangneigung >15°',       group: 'terrain',   color: '#a8a29e9b', description: 'Gelände mit einer Neigung von mehr als 15 Grad' },
	{ code: 8,  name: 'Seehöhe >2500 m',        group: 'terrain',   color: '#d6d3d191', description: 'Flächen über 2.500 m Seehöhe (topografische Grenze)' },
	{ code: 9,  name: 'Wichtige Objekte (250 m)', group: 'exclusion', color: '#9a341296', description: 'Pufferzone um besonders schutzwürdige Einzelobjekte (vorläufige Kategorie, genaue Definition folgt)' },
	{ code: 10, name: 'Freileitung 380/400 kV',  group: 'exclusion', color: '#fbbf248c', description: 'Pufferzone von 150 m entlang Hochspannungsfreileitungen (380/400 kV)' },
	{ code: 11, name: 'Wind zu gering',          group: 'wind',      color: '#94a3b896', description: 'Windleistungsdichte unter 150 W/m² (@150 m) oder keine Winddaten verfügbar' },
	{ code: 12, name: 'Allgemeine Gebäude (25 m)', group: 'exclusion', color: '#fdba7482', description: 'Pufferzone um sonstige Gebäude (vorläufige Kategorie, genaue Definition folgt)' },
	{ code: 13, name: 'Gebäude an Seilbahnen (50 m)', group: 'exclusion', color: '#c2410c8c', description: 'Pufferzone um Gebäude an Seilbahnen (vorläufige Kategorie, genaue Definition folgt)' },
	{ code: 14, name: 'Geeignet (≥150 W/m²)',   group: 'suitable',  color: '#93c5fddc', description: 'Potenziell geeignete Fläche: kein Ausschlussgrund, Windleistungsdichte ≥ 150 W/m² @150 m, zusammenhängende Zone ≥ 10 ha' },
];

export const SUITABLE_CODES = [14];

export function getCodeByNumber(code: number): LegendCode | undefined {
	return LEGEND_CODES.find(c => c.code === code);
}

export const GROUP_LABELS: Record<string, string> = {
	suitable:  'Geeignete Flächen',
	exclusion: 'Ausschlussgründe (regulatorisch)',
	terrain:   'Ausschlussgründe (Gelände)',
	wind:      'Windpotenzial unzureichend',
	none:      'Außerhalb',
};
