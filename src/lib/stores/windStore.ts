import { writable } from 'svelte/store';
import type { Map } from 'maplibre-gl';

export interface Region {
	id: string;
	name: string;
	slug: string;
	code: string;
	layer: string;
	layer_label: string;
	postcodes: string[];
	center: [string, string];
	outline: GeoJSON.Polygon | GeoJSON.MultiPolygon | null;
	parents?: Array<{ id: string; layer: string }>;
}

export type OfficialZoneType = 'positive' | 'vorrang' | 'eignung' | 'ausschluss' | null;

export interface ZoneStats {
	count: number;
	totalAreaHa: number;
	meanPdWm2: number;
	turbineCount: number;
	officialZoneCount: number;
	officialZoneType: OfficialZoneType; // null = no official zone data for this region
}

export type VizMode = 'zones' | 'heatmap' | 'hexbin' | 'dots';

export interface ZoneStatsTotals {
	count: number;
	totalHa: number;
	perBundesland: Record<string, number>;
}

export const mapInstance    = writable<Map | null>(null);
export const expertMode     = writable(false);
export const vizMode        = writable<VizMode>('zones');
export const selectedRegion = writable<Region | null>(null);
export const regionStats    = writable<ZoneStats | null>(null);
export const dataLoaded     = writable(false);
export const austriaOutline = writable<GeoJSON.Polygon | GeoJSON.MultiPolygon | null>(null);
// -1 = story complete/inactive, 0-4 = active story step.
// Default is -1 so non-root pages (no Scrollytelling) work immediately.
// Scrollytelling.svelte sets it to 0 in onMount when the story is active.
export const storyStep      = writable<number>(-1);
export const storyComplete  = writable<boolean>(false);
export const hiddenBands       = writable<Set<number>>(new Set<number>());
export const detailLayersReady = writable(false);
// Band IDs with no rendered features in the current viewport (updated on map idle)
export const emptyBands        = writable<Set<number>>(new Set<number>());
// Österreichweite Summen aus geodata/zone_stats.json (einmal geladen).
export const zoneStats         = writable<ZoneStatsTotals | null>(null);
// Current map zoom + the Bundesland under the viewport center (null once zoomed
// out past a single state, or over a gap with no municipality feature there).
// Drives map-level contextual notices, e.g. the NÖ Mindestabstand hint.
export const mapZoom          = writable<number>(6.8);
export const centerBundesland = writable<string | null>(null);
