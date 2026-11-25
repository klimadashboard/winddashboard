import { env } from '$env/dynamic/public';

/** Der eigentliche Kachelserver (TileServer GL hinter Apache, 2 Kerne). */
export const TILE_ORIGIN = 'https://tiles.klimadashboard.org';

/**
 * Die Karte holt ihre Kacheln nicht direkt dort, sondern über /tiles auf der
 * eigenen Domain (src/routes/tiles/[...path]/+server.ts). Vercels CDN hält sie
 * dort vor; der Kachelserver sieht jede Kachel nur einmal je Cache-Zeitraum.
 * Direkt angefragt hielt er im Lasttest vom 24.11.2026 rund 400 Anfragen/s
 * aus und lief bei 400 offenen Verbindungen in Timeouts — bei rund 90 Kacheln
 * je Besuch reicht das nicht für einen Ansturm nach Medienberichten.
 *
 * Absolut, weil MapLibre die Kacheln in Web Workern lädt, in denen eine
 * relative URL nicht gegen die Seite aufgelöst wird. Die Karte läuft nur im
 * Browser; der Fallback ist nur für den Import beim Server-Rendering da.
 */
export const TILE_SERVER_BASE =
	// Auf Cloudflare: eigene Kachel-Subdomain hinter dem Cloudflare-Cache
	// (wrangler.jsonc, PUBLIC_TILE_BASE). Dann zählt keine Kachel als
	// Worker-Anfrage. Leer = Proxy wie oben.
	env.PUBLIC_TILE_BASE ||
	(typeof location !== 'undefined' ? `${location.origin}/tiles` : '/tiles');

// TileServer GL serves raw MBTiles data at /data/{id}/{z}/{x}/{y}.{format}
export const CLASSIFICATION_TILES = `${TILE_SERVER_BASE}/data/windkraft_classification/{z}/{x}/{y}.png`;
export const CLASSIFICATION_TILES_MIN_ZOOM = 6;
export const CLASSIFICATION_TILES_MAX_ZOOM = 13;

// Grundkarte: OpenFreeMap „Positron“ (OpenStreetMap-Daten im OpenMapTiles-Schema).
// Kein Schlüssel, kein Anfragelimit. Bis November 2026 kam die Grundkarte von
// CARTO; deren Kontingent (5 Mio. Anfragen/Monat für das ganze Konto) war nach
// dem Start nach wenigen Tagen aufgebraucht, vor allem durch die halbtransparente
// Raster-Straßenebene. Map.svelte nimmt die Beschriftung aus diesem Style heraus
// und legt sie nach den Datenebenen wieder obenauf, die Straßen ebenso als
// halbtransparente Kopie über die Flächen (statt der Rasterkacheln).
export const BASEMAP_STYLE = 'https://tiles.openfreemap.org/styles/positron';

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
//
// `_v3` (Bandschema 3.0, Lieferung 19.11.2026): neue Lieferungen bekommen eine
// eigene Kachel-ID, statt die alte Datei zu überschreiben. So zeigt die Seite
// bis zum Deploy weiter die zu ihren Texten passenden Flächen, und der neue
// Code schaltet mit dem Deploy um.
const POSSIBLE_ZONES_ID = 'windkraft_possible_zones_v3';
export const POSSIBLE_ZONES_TILES =
	`${TILE_SERVER_BASE}/data/${POSSIBLE_ZONES_ID}/{z}/{x}/{y}.pbf`;
/**
 * Kachel-URL der Potenzialflächen für eine Siedlungsabstands-Variante. Jede
 * Variante ist eine eigene MBTiles-Datei mit demselben Layernamen
 * (scripts/build_zone_tiles.py); die Karte tauscht nur die URL der Quelle.
 */
export function possibleZonesTiles(variant: string): string {
	return variant === 'default'
		? POSSIBLE_ZONES_TILES
		: `${TILE_SERVER_BASE}/data/${POSSIBLE_ZONES_ID}_${variant}/{z}/{x}/{y}.pbf`;
}
export const POSSIBLE_ZONES_LAYER = 'possible_zones';
// 4, nicht 5: die Karte lässt auf schmalen Fenstern minZoom 4.5 zu. Mit einer
// Quelle ab Zoom 5 war der Bereich 4,5–5 eine tote Zone — die Potenzialflächen
// fehlten dort vollständig, ohne Fehlermeldung.
export const POSSIBLE_ZONES_MIN_ZOOM = 4;
export const POSSIBLE_ZONES_MAX_ZOOM = 14;

// Bestandsanlagen ebenfalls als Vektorkacheln (scripts/build_turbine_tiles.py).
// Hier geht es nicht um die Dateigröße — die Punkte sind nur 260 kB —, sondern
// um die Lizenz: die Standorte dürfen gezeigt, der Datensatz aber nicht
// weitergegeben werden. Als Datei unter static/data/ lag er im öffentlichen
// Repository und ging bei jedem Aufruf am Stück an den Browser; als Kacheln
// bekommt der Browser nur den sichtbaren Ausschnitt.
export const TURBINE_TILES = `${TILE_SERVER_BASE}/data/windkraft_turbines/{z}/{x}/{y}.pbf`;
export const TURBINE_LAYER = 'existing_turbines';
export const TURBINE_MIN_ZOOM = 4;
export const TURBINE_MAX_ZOOM = 14;
