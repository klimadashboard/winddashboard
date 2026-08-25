export const TILE_SERVER_BASE = 'https://tiles.klimadashboard.org';

// TileServer GL serves raw MBTiles data at /data/{id}/{z}/{x}/{y}.{format}
export const CLASSIFICATION_TILES = `${TILE_SERVER_BASE}/data/windkraft_classification/{z}/{x}/{y}.png`;
export const CLASSIFICATION_TILES_MIN_ZOOM = 6;
export const CLASSIFICATION_TILES_MAX_ZOOM = 13;

// No-labels basemap — clean background without streets/buildings/text.
// German label layers are fetched separately from CARTO_LABELS_STYLE and
// added dynamically on top of all data layers.
export const CARTO_BASEMAP       = 'https://basemaps.cartocdn.com/gl/positron-nolabels-gl-style/style.json';
export const CARTO_LABELS_STYLE  = 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json';

export const AUSTRIA_BOUNDS: [number, number, number, number] = [9.5, 46.3, 17.2, 49.0];
export const AUSTRIA_CENTER: [number, number] = [13.4, 47.5];
export const AUSTRIA_ZOOM = 6.8;
