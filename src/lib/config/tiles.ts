import { env } from '$env/dynamic/public';

export const TILE_SERVER_BASE = 'https://tiles.klimadashboard.org';

// TileServer GL serves raw MBTiles data at /data/{id}/{z}/{x}/{y}.{format}
export const CLASSIFICATION_TILES = `${TILE_SERVER_BASE}/data/windkraft_classification/{z}/{x}/{y}.png`;
export const CLASSIFICATION_TILES_MIN_ZOOM = 6;
export const CLASSIFICATION_TILES_MAX_ZOOM = 13;

// CARTO basemaps require an API key as of 2026 (https://carto.com/basemaps/apikey/).
// Set PUBLIC_CARTO_API_KEY in .env locally and in the Vercel project's env vars —
// see .env.example. Falls back to no key (CARTO will reject/rate-limit the request)
// so a missing key fails loudly in the map rather than silently.
const cartoKeyParam = env.PUBLIC_CARTO_API_KEY ? `?key=${env.PUBLIC_CARTO_API_KEY}` : '';

// No-labels basemap — clean background without streets/buildings/text.
// German label layers are fetched separately from CARTO_LABELS_STYLE and
// added dynamically on top of all data layers.
export const CARTO_BASEMAP       = `https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json${cartoKeyParam}`;
export const CARTO_LABELS_STYLE  = `https://basemaps.cartocdn.com/gl/positron-gl-style/style.json${cartoKeyParam}`;

// Semi-transparent street/building raster context layer (see Map.svelte).
export const CARTO_RASTER_CONTEXT = `https://basemaps.cartocdn.com/rastertiles/light_nolabels/{z}/{x}/{y}.png${cartoKeyParam}`;

// Nur noch als Rückfall gedacht; die Karte passt sich über AUSTRIA_BOUNDS ein.
export const AUSTRIA_CENTER: [number, number] = [13.4, 47.5];
// Amtliche Ausdehnung Österreichs (Statistik Austria). Die Karte wird darauf
// eingepasst statt auf feste Mittelpunkt/Zoom-Werte: nur so sitzt der Ausschnitt
// auf jedem Seitenverhältnis richtig — ein fester Zoom, der am Schreibtisch
// passt, schneidet auf dem Telefon Vorarlberg und das Burgenland ab.
export const AUSTRIA_BOUNDS: [[number, number], [number, number]] = [
	[9.53, 46.37],
	[17.16, 49.02],
];
export const AUSTRIA_ZOOM = 6.8;

// Potenzialflächen als Vektorkacheln statt als 15-MB-GeoJSON. Der Layername in
// den Kacheln ist `possible_zones`; `zone_id` dient als promoteId, damit der
// Hover-Zustand über Kachelgrenzen hinweg stabil bleibt.
export const POSSIBLE_ZONES_TILES =
	`${TILE_SERVER_BASE}/data/windkraft_possible_zones/{z}/{x}/{y}.pbf`;
export const POSSIBLE_ZONES_LAYER = 'possible_zones';
export const POSSIBLE_ZONES_MIN_ZOOM = 5;
export const POSSIBLE_ZONES_MAX_ZOOM = 14;
