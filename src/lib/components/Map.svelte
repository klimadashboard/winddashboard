<script lang="ts">
	import { onMount } from "svelte";
	import { get } from "svelte/store";
	import { goto } from "$app/navigation";
	import {
		mapInstance,
		expertMode,
		vizMode,
		selectedRegion,
		regionStats,
		dataLoaded,
		austriaOutline,
		storyStep,
		hiddenBands,
		detailLayersReady,
		emptyBands,
		settlementVariant,
		mapZoom,
		centerBundesland,
	} from "$lib/stores/windStore";
	import type { VizMode, OfficialZoneType } from "$lib/stores/windStore";
	import { BAND_DEFS, bandLayerId, EXCLUSION_BANDS_SOURCE, EXCLUSION_BANDS_TILES } from "$lib/config/bands";
	import type { BandGroup, BandDef } from "$lib/config/bands";
	import { possibleZonesUrl, zoneCentroidsUrl } from "$lib/config/variants";
	import type { SettlementVariant } from "$lib/config/variants";
	import {
		CARTO_BASEMAP,
		CARTO_LABELS_STYLE,
		CARTO_RASTER_CONTEXT,
		AUSTRIA_CENTER,
		AUSTRIA_ZOOM,
		CLASSIFICATION_TILES,
		CLASSIFICATION_TILES_MIN_ZOOM,
		CLASSIFICATION_TILES_MAX_ZOOM,
	} from "$lib/config/tiles";
	import type { Region, ZoneStats } from "$lib/stores/windStore";

	export interface HoverInfo {
		zone?: Record<string, unknown>;
		official?: Record<string, unknown>;
		turbine?: Record<string, unknown>;
		bands?: Array<{ label: string; description: string; color: string }>;
		x: number;
		y: number;
	}

	let {
		onHover = (_: HoverInfo | null) => {},
	}: { onHover?: (info: HoverInfo | null) => void } = $props();

	let mapContainer: HTMLDivElement;

	// First digit of an Austrian Gemeindekennziffer (AGS) identifies the Bundesland.
	const BUNDESLAND_BY_AGS_PREFIX: Record<string, string> = {
		"1": "Burgenland",
		"2": "Kärnten",
		"3": "Niederösterreich",
		"4": "Oberösterreich",
		"5": "Salzburg",
		"6": "Steiermark",
		"7": "Tirol",
		"8": "Vorarlberg",
		"9": "Wien",
	};

	// Every slug a band def can render as. Only the settlement band (band 1) has
	// more than one — one per settlement-distance variant; every other band has
	// exactly one slug regardless of the selected variant.
	function allSlugsForDef(def: BandDef): string[] {
		return def.variantSlugs ? Object.values(def.variantSlugs) : [def.slug];
	}
	// The slug that should currently be shown for a band def, given the selected
	// settlement-distance variant.
	function activeSlugForDef(def: BandDef, variant: SettlementVariant): string {
		return def.variantSlugs?.[variant] ?? def.slug;
	}

	onMount(async () => {
		// Dynamic import keeps maplibre-gl out of SSR bundle
		const { default: maplibregl } = await import("maplibre-gl");
		await import("maplibre-gl/dist/maplibre-gl.css");

		const isMobile = window.innerWidth < 768;
		const map = new maplibregl.Map({
			container: mapContainer,
			style: CARTO_BASEMAP,
			// On mobile the story card covers the top ~half of the viewport.
			// Centering further north pushes Austria into the visible lower half.
			center: isMobile ? [13.4, 50.0] : AUSTRIA_CENTER,
			zoom: isMobile ? 5.5 : AUSTRIA_ZOOM,
			minZoom: isMobile ? 4.5 : 6.5,
			maxZoom: 16,
			attributionControl: false,
		});

		map.addControl(
			new maplibregl.AttributionControl({ compact: true }),
			"bottom-right",
		);
		map.addControl(
			new maplibregl.NavigationControl({ showCompass: false }),
			"top-right",
		);

		// ── Helpers (defined inside onMount so they close over `map` and `maplibregl`) ──

		function addSources() {
			map.addSource("exclusion-schutz", { type: "geojson", data: "/data/exclusion_schutz" });
			map.addSource("exclusion-siedlung", { type: "geojson", data: "/data/exclusion_siedlung" });
			map.addSource("exclusion-sonstige", { type: "geojson", data: "/data/exclusion_sonstige" });
			map.addSource("exclusion-wind", { type: "geojson", data: "/data/exclusion_wind" });

			map.addSource("possible-zones", {
				type: "geojson",
				data: possibleZonesUrl(get(settlementVariant)),
				generateId: true,
			});

			map.addSource("official-zones", {
				type: "geojson",
				data: "/data/official_zoning",
				generateId: true,
			});

			map.addSource("turbines", {
				type: "geojson",
				data: "/data/existing_turbines",
				generateId: true,
			});

			map.addSource("classification-raster", {
				type: "raster",
				tiles: [CLASSIFICATION_TILES],
				tileSize: 256,
				minzoom: CLASSIFICATION_TILES_MIN_ZOOM,
				maxzoom: CLASSIFICATION_TILES_MAX_ZOOM,
				attribution: "© Klimadashboard",
			});

			map.addSource("zone-centroids", {
				type: "geojson",
				data: zoneCentroidsUrl(get(settlementVariant)),
			});

			map.addSource("municipalities", {
				type: "vector",
				url: "https://tiles.klimadashboard.org/data/municipalities-at.json",
				promoteId: { "municipalities": "AGS" },
			});

			// Generic selected-region outline — driven by the `outline` geometry
			// from the regions API, not the municipalities vector tile. This is
			// what makes district (Bezirk) and other non-municipality search
			// results show up on the map: the municipalities tileset only has
			// municipality-level features, so a Bezirk's feature-state never
			// matches anything in it.
			map.addSource("region-highlight", {
				type: "geojson",
				data: { type: "FeatureCollection", features: [] },
			});

			// Semi-transparent street/building context layer (sits above data fills,
			// below labels). Uses the no-labels raster so text stays solely from the
			// German GL label fetch.
			map.addSource("carto-context", {
				type: "raster",
				tiles: [CARTO_RASTER_CONTEXT],
				tileSize: 256,
				attribution: "© CARTO",
			});

			// Single vector-tile source for all 16 exclusion band layers.
			// Uses tiles: directly so activateBandLayers() only needs to re-add
			// the *layers* (not the source) — avoids the remove-source race condition.
			map.addSource(EXCLUSION_BANDS_SOURCE, {
				type: "vector",
				tiles: [EXCLUSION_BANDS_TILES],
				minzoom: 5,
				maxzoom: 14,
			});
		}

		// ── Austria mask: loaded from static GeoJSON ───────────────────────────────
		async function addAustriaMask() {
			try {
				const res = await fetch("/data/austria_outline");
				const feature: GeoJSON.Feature = await res.json();
				const outline = feature.geometry as
					| GeoJSON.Polygon
					| GeoJSON.MultiPolygon;
				if (!outline) return;

				// Share outline with DotGrid via store
				austriaOutline.set(outline);

				// Build inverted polygon: world box as outer ring, Austria as hole
				const worldBox: [number, number][] = [
					[-180, -85],
					[180, -85],
					[180, 85],
					[-180, 85],
					[-180, -85],
				];
				const rings: [number, number][][] = [worldBox];
				if (outline.type === "Polygon") {
					rings.push(outline.coordinates[0] as [number, number][]);
				} else if (outline.type === "MultiPolygon") {
					for (const poly of (outline as GeoJSON.MultiPolygon).coordinates) {
						rings.push(poly[0] as [number, number][]);
					}
				}

				map.addSource("austria-mask", {
					type: "geojson",
					data: {
						type: "Feature",
						geometry: { type: "Polygon", coordinates: rings },
						properties: {},
					},
				});
				// Fill mask — placed just below the first data layer
				map.addLayer(
					{
						id: "austria-mask",
						type: "fill",
						source: "austria-mask",
						paint: { "fill-color": "#f1f5f9", "fill-opacity": 0.78 },
					},
					"possible-zones-fill",
				);
				// Subtle border line along Austria's edge
				map.addSource("austria-border", {
					type: "geojson",
					data: { type: "Feature", geometry: outline, properties: {} },
				});
				// Bold while the intro story is active — visually ties the map's
				// Austria outline to the story's area bar (same "this is the
				// country" outline on both). Subtle once the story is done.
				const storyActive = get(storyStep) >= 0;
				map.addLayer(
					{
						id: "austria-border",
						type: "line",
						source: "austria-border",
						paint: {
							"line-color": storyActive ? "#0f172a" : "#94a3b8",
							"line-width": storyActive ? 2.5 : 1,
							"line-opacity": storyActive ? 0.9 : 0.5,
						},
					},
					"possible-zones-fill",
				);
			} catch {
				// Mask is optional — silently skip on error
			}
		}

		function addLayers(firstSymbolId: string | undefined) {
			// All fill/line data layers are inserted BEFORE the basemap's first symbol
			// layer so that Carto's GL labels always render on top of our fills.
			// Outline + hit layers are added without beforeId (they float above labels).
			const B = firstSymbolId; // shorthand

			// ── Exclusion layers — story mode only, hidden by default ──────────────
			map.addLayer({ id: "exclusion-schutz-fill",   type: "fill", source: "exclusion-schutz",   layout: { visibility: "none" }, paint: { "fill-color": "#4ade80", "fill-opacity": 0.45 } }, B);
			map.addLayer({ id: "exclusion-siedlung-fill", type: "fill", source: "exclusion-siedlung", layout: { visibility: "none" }, paint: { "fill-color": "#fb923c", "fill-opacity": 0.45 } }, B);
			map.addLayer({ id: "exclusion-sonstige-fill", type: "fill", source: "exclusion-sonstige", layout: { visibility: "none" }, paint: { "fill-color": "#94a3b8", "fill-opacity": 0.40 } }, B);
			map.addLayer({ id: "exclusion-wind-fill",     type: "fill", source: "exclusion-wind",     layout: { visibility: "none" }, paint: { "fill-color": "#2dd4bf", "fill-opacity": 0.40 } }, B);

			// Classification raster — always hidden; added early so it's below zone fills
			map.addLayer({ id: "classification-raster", type: "raster", source: "classification-raster", layout: { visibility: "none" }, paint: { "raster-opacity": 0.85, "raster-resampling": "linear", "raster-fade-duration": 200 } }, B);

			// ── Detail band layers — 18 bands, below zone fills. The settlement
			// band (1) gets one layer per settlement-distance variant; only the
			// one matching $settlementVariant is ever shown (see updateLayers). ──
			for (const def of BAND_DEFS) {
				const r = parseInt(def.color.slice(1,3),16);
				const g = parseInt(def.color.slice(3,5),16);
				const b2 = parseInt(def.color.slice(5,7),16);
				for (const slug of allSlugsForDef(def)) {
					map.addLayer({ id: bandLayerId(slug), type: "fill", source: EXCLUSION_BANDS_SOURCE, "source-layer": slug, paint: { "fill-color": `rgb(${r},${g},${b2})`, "fill-opacity": 0 } }, B);
				}
			}
			detailLayersReady.set(true);

			// Municipality fill — below zone fills
			map.addLayer({
				id: "municipalities-fill",
				type: "fill",
				source: "municipalities",
				"source-layer": "municipalities",
				paint: {
					"fill-color": "#64748b",
					"fill-opacity": ["case", ["boolean", ["feature-state", "hover"], false], 0.06, 0],
				},
			}, B);

			map.addLayer({
				id: "possible-zones-fill",
				type: "fill",
				source: "possible-zones",
				paint: { "fill-color": "#2563eb", "fill-opacity": ["case", ["boolean", ["feature-state", "hover"], false], 0.72, 0.48] },
			}, B);

			map.addLayer({
				id: "possible-zones-border",
				type: "line",
				source: "possible-zones",
				paint: { "line-color": "#1d4ed8", "line-width": 1.5, "line-blur": 0, "line-opacity": 0.55 },
			}, B);

			// Added after possible-zones-fill/border (same beforeId=B) so official
			// zones render visually above them. fill-opacity is fully opaque (1) —
			// at the old 0.12 the blue underneath (0.48/0.72) still showed through
			// and read as "on top" even though this layer is stacked above it.
			// Deep purple (was amber) — pairs better with the blue potential zones.
			map.addLayer({ id: "official-zones-fill",    type: "fill", source: "official-zones", paint: { "fill-color": "#7c3aed", "fill-opacity": 1 } }, B);
			map.addLayer({ id: "official-zones-outline", type: "line", source: "official-zones", paint: { "line-color": "#6d28d9", "line-width": 1.5, "line-dasharray": [4, 2], "line-opacity": 0.8 } }, B);

			map.addLayer({
				id: "turbines",
				type: "circle",
				source: "turbines",
				minzoom: 7,
				paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 7, 2, 10, 3.5, 13, 5], "circle-color": "#1e3a8a", "circle-stroke-color": "#ffffff", "circle-stroke-width": 1, "circle-opacity": 0.85 },
			}, B);

			// Heatmap layer — used by 'heatmap' viz mode
			map.addLayer({
				id: "zones-heatmap",
				type: "heatmap",
				source: "zone-centroids",
				layout: { visibility: "none" },
				paint: {
					"heatmap-weight": ["get", "w"],
					"heatmap-intensity": ["interpolate", ["linear"], ["zoom"], 5, 0.6, 9, 2.0, 13, 4.0],
					"heatmap-radius": ["interpolate", ["linear"], ["zoom"], 5, 20, 8, 45, 13, 80],
					"heatmap-color": ["interpolate", ["linear"], ["heatmap-density"], 0, "rgba(147,197,253,0)", 0.15, "rgba(147,197,253,0.55)", 0.4, "rgba(96,165,250,0.75)", 0.65, "rgba(59,130,246,0.88)", 0.85, "rgba(29,78,216,0.94)", 1, "rgba(30,58,138,1)"],
					"heatmap-opacity": ["interpolate", ["linear"], ["zoom"], 7, 1, 11, 0.6],
				},
			}, B);

			// ── Road/building context — above data fills, below labels ──────────────
			// Carto light_nolabels raster at low opacity: gives road-network context
			// without dominating the data fills. Labels come on top via addGermanLabels.
			map.addLayer({
				id: "carto-context",
				type: "raster",
				source: "carto-context",
				paint: { "raster-opacity": 0.30 },
			});

			// ── Municipality outline — just below GL labels, above all data fills ──
			map.addLayer({
				id: "municipalities-outline",
				type: "line",
				source: "municipalities",
				"source-layer": "municipalities",
				paint: {
					"line-color": "#64748b",
					"line-width": 1.5,
					"line-opacity": ["case", ["boolean", ["feature-state", "hover"], false], 0.5, 0],
				},
			}, B);

			// Selected-region outline (any layer: Gemeinde, Bezirk, …) — see the
			// "region-highlight" source above for why this exists separately
			// from the municipalities feature-state highlighting.
			map.addLayer({
				id: "region-highlight-fill",
				type: "fill",
				source: "region-highlight",
				paint: { "fill-color": "#1d4ed8", "fill-opacity": 0.06 },
			}, B);
			map.addLayer({
				id: "region-highlight-outline",
				type: "line",
				source: "region-highlight",
				paint: {
					"line-color": "#1d4ed8",
					"line-width": 2.5,
					"line-opacity": 0.9,
				},
			}, B);

			// Invisible hit layers — float above everything; opacity 0 so invisible
			map.addLayer({ id: "possible-zones-hit", type: "fill", source: "possible-zones", paint: { "fill-opacity": 0 } });
			map.addLayer({ id: "official-zones-hit",  type: "fill", source: "official-zones",  paint: { "fill-opacity": 0 } });
			// GL basemap labels are already on top — no separate carto-labels needed
		}

		// ── Unified layer-state: called whenever expert OR viz mode changes ─────
		function updateLayers(expert: boolean, viz: VizMode) {
			if (!map.isStyleLoaded()) return;
			const showZones = viz === "zones";
			const showHeatmap = viz === "heatmap";
			const showPolys = showZones || showHeatmap;

			// Classification raster — now always hidden; the 16 detail band layers
			// replaced it in expert mode, and it was never shown in standard mode.
			if (map.getLayer("classification-raster"))
				map.setLayoutProperty("classification-raster", "visibility", "none");

			// MapLibre heatmap layer
			if (map.getLayer("zones-heatmap"))
				map.setLayoutProperty(
					"zones-heatmap",
					"visibility",
					showHeatmap ? "visible" : "none",
				);

			// Polygon fill
			if (map.getLayer("possible-zones-fill")) {
				map.setLayoutProperty(
					"possible-zones-fill",
					"visibility",
					showPolys ? "visible" : "none",
				);
				if (showZones) {
					map.setPaintProperty("possible-zones-fill", "fill-opacity", [
						"case",
						["boolean", ["feature-state", "hover"], false],
						expert ? 0.15 : 0.72,
						expert ? 0 : 0.48,
					]);
				} else if (showHeatmap) {
					map.setPaintProperty("possible-zones-fill", "fill-opacity", [
						"interpolate",
						["linear"],
						["zoom"],
						9,
						0,
						13,
						0.7,
					]);
				}
			}

			// Border
			if (map.getLayer("possible-zones-border")) {
				map.setLayoutProperty(
					"possible-zones-border",
					"visibility",
					showPolys ? "visible" : "none",
				);
				if (showZones) {
					map.setPaintProperty("possible-zones-border", "line-width", expert ? 2 : 1.5);
					map.setPaintProperty("possible-zones-border", "line-blur", 0);
					map.setPaintProperty(
						"possible-zones-border",
						"line-opacity",
						expert ? 0.8 : 0.55,
					);
				} else if (showHeatmap) {
					map.setPaintProperty("possible-zones-border", "line-width", 1.5);
					map.setPaintProperty("possible-zones-border", "line-blur", 0);
					map.setPaintProperty("possible-zones-border", "line-opacity", [
						"interpolate",
						["linear"],
						["zoom"],
						9,
						0,
						13,
						0.6,
					]);
				}
			}

			// Detail band layers — opacity-based show/hide. For the settlement band
			// (variantSlugs set), only the slug matching the selected variant may
			// ever be visible — every other variant's slug always stays at 0.
			if (get(detailLayersReady)) {
				const variant = get(settlementVariant);
				if (expert) {
					try { activateBandLayers(variant); } catch(e) {
						console.warn('[bands] activateBandLayers failed, resetting:', e);
						activatedSlugs.clear(); // allow retry on next toggle
					}
				}
				const hidden = get(hiddenBands);
				for (const def of BAND_DEFS) {
					const activeSlug = activeSlugForDef(def, variant);
					const baseOpacity = (parseInt(def.color.slice(7,9),16) / 255) * 0.6;
					const showThisBand = expert && !hidden.has(def.band);
					for (const slug of allSlugsForDef(def)) {
						const id = bandLayerId(slug);
						if (!map.getLayer(id)) continue;
						const isActiveSlug = slug === activeSlug;
						map.setPaintProperty(id, 'fill-opacity',
							showThisBand && isActiveSlug ? baseOpacity : 0);
					}
				}
			}
		}

		// ── Auto-pitch for hexbin 3D view ──────────────────────────────────────
		function applyPitch(viz: VizMode) {
			if (viz === "hexbin") {
				map.easeTo({ pitch: 45, bearing: -15, duration: 900 });
			} else if (map.getPitch() > 0) {
				map.easeTo({ pitch: 0, bearing: 0, duration: 600 });
			}
		}

		// Bbox of the currently selected region in geo coords — used by computeRegionStats
		// to restrict queryRenderedFeatures to just that area.
		let currentRegionBbox: [number, number, number, number] | null = null;
		// True once addSources() has run inside the "load" handler — map.isStyleLoaded()
		// can report true before our custom sources (e.g. "municipalities") exist, so it
		// is not a reliable readiness check on its own.
		let sourcesReady = false;

		// Drives map-level contextual notices (e.g. the NÖ Mindestabstand hint) that
		// depend on the viewport rather than a selected region.
		function updateCenterInfo() {
			mapZoom.set(map.getZoom());
			if (!sourcesReady) { centerBundesland.set(null); return; }
			const centerPx = map.project(map.getCenter());
			const feats = map.queryRenderedFeatures(centerPx, { layers: ["municipalities-fill"] });
			const ags = feats[0]?.properties?.AGS as string | undefined;
			centerBundesland.set(ags ? (BUNDESLAND_BY_AGS_PREFIX[ags[0]] ?? null) : null);
		}

		function setRegionHighlight(region: Region | null) {
			const src = map.getSource("region-highlight") as maplibregl.GeoJSONSource | undefined;
			if (!src) return;
			src.setData(
				region?.outline
					? { type: "Feature", geometry: region.outline, properties: {} }
					: { type: "FeatureCollection", features: [] },
			);
		}

		function highlightRegion(region: Region) {
			if (!sourcesReady) return;
			setRegionHighlight(region);

			// Zoom to the region using its outline bbox
			if (!region.outline) {
				// No outline geometry available — can't scope the query to this region's
				// bounds, but still resolve stats for the current viewport rather than
				// leaving the Inspector stuck on "wird geladen" forever.
				currentRegionBbox = null;
				computeRegionStats();
				return;
			}
			const allCoords: [number, number][] =
				region.outline.type === "Polygon"
					? (region.outline.coordinates[0] as [number, number][])
					: region.outline.coordinates.flatMap((poly) => poly[0] as [number, number][]);
			let minLon = Infinity, minLat = Infinity, maxLon = -Infinity, maxLat = -Infinity;
			for (const [lon, lat] of allCoords) {
				if (lon < minLon) minLon = lon;
				if (lat < minLat) minLat = lat;
				if (lon > maxLon) maxLon = lon;
				if (lat > maxLat) maxLat = lat;
			}
			currentRegionBbox = [minLon, minLat, maxLon, maxLat];
			map.fitBounds(currentRegionBbox, { padding: 160, duration: 1200 });
			// Use idle (not moveend) so tiles at the new zoom are fully loaded first
			map.once("idle", computeRegionStats);
		}

		function clearRegionHighlight() {
			if (!sourcesReady) return;
			setRegionHighlight(null);
			currentRegionBbox = null;
			regionStats.set(null);
		}

		function computeRegionStats() {
			// Convert geo bbox → pixel bbox so we query only features inside the region,
			// not everything else visible in the wider viewport
			let queryArea: [maplibregl.PointLike, maplibregl.PointLike] | undefined;
			if (currentRegionBbox) {
				const sw = map.project([currentRegionBbox[0], currentRegionBbox[1]]);
				const ne = map.project([currentRegionBbox[2], currentRegionBbox[3]]);
				queryArea = [
					[Math.floor(sw.x), Math.floor(ne.y)],
					[Math.ceil(ne.x), Math.ceil(sw.y)],
				];
			}
			// Use the always-visible hit layer so stats are correct regardless of
			// story step or viz mode (possible-zones-fill may be visibility:none).
			const features = map.queryRenderedFeatures(queryArea, {
				layers: ["possible-zones-hit"],
			});

			// Query official zones — use hit layer so it works even when fill is hidden
			const officialFeatures = map.queryRenderedFeatures(queryArea, {
				layers: ["official-zones-hit"],
			});
			const officialZoneCount = officialFeatures.length;
			// Determine zone type: use `zone_type` property if present, otherwise
			// treat all current zones as positive (NÖ Windkraftzonen).
			let officialZoneType: OfficialZoneType = null;
			if (officialZoneCount > 0) {
				const rawType = officialFeatures[0].properties?.zone_type as string | undefined;
				if (rawType === 'ausschluss') officialZoneType = 'ausschluss';
				else if (rawType === 'vorrang') officialZoneType = 'vorrang';
				else if (rawType === 'eignung') officialZoneType = 'eignung';
				else officialZoneType = 'positive';
			}

			if (!features.length) {
				regionStats.set({
					count: 0,
					totalAreaHa: 0,
					meanPdWm2: 0,
					turbineCount: 0,
					officialZoneCount,
					officialZoneType,
				});
				return;
			}
			const seen = new Set<number>();
			const unique = features.filter((f) => {
				const id = f.properties?.zone_id as number;
				if (seen.has(id)) return false;
				seen.add(id);
				return true;
			});
			regionStats.set({
				count: unique.length,
				totalAreaHa: Math.round(
					unique.reduce(
						(s, f) => s + ((f.properties?.area_ha as number) || 0),
						0,
					),
				),
				meanPdWm2: Math.round(
					unique.reduce(
						(s, f) => s + ((f.properties?.pd_mean_w_m2 as number) || 0),
						0,
					) / unique.length,
				),
				turbineCount: unique.reduce(
					(s, f) => s + ((f.properties?.n_existing_turbines as number) || 0),
					0,
				),
				officialZoneCount,
				officialZoneType,
			});
		}

		let hoveredZoneId: number | null = null;
		let hoveredRegionFeatureId: string | null = null;

		function clearRegionHover() {
			if (hoveredRegionFeatureId !== null) {
				map.setFeatureState(
					{ source: "municipalities", sourceLayer: "municipalities", id: hoveredRegionFeatureId },
					{ hover: false },
				);
				hoveredRegionFeatureId = null;
			}
		}

		function setupHoverEvents() {
			const zoneLayers = ["possible-zones-fill", "official-zones-fill", "turbines"];

			map.on("mousemove", (e) => {
				const bbox = [
					[e.point.x - 3, e.point.y - 3],
					[e.point.x + 3, e.point.y + 3],
				] as [[number, number], [number, number]];
				const zoneFeatures = map.queryRenderedFeatures(bbox, { layers: zoneLayers });

				if (zoneFeatures.length > 0) {
					map.getCanvas().style.cursor = "crosshair";
					clearRegionHover();
					const zone = zoneFeatures.find((f) => f.layer.id === "possible-zones-fill");
					const official = zoneFeatures.find((f) => f.layer.id === "official-zones-fill");
					const turbine = zoneFeatures.find((f) => f.layer.id === "turbines");
					if (zone) {
						if (hoveredZoneId !== null)
							map.setFeatureState(
								{ source: "possible-zones", id: hoveredZoneId },
								{ hover: false },
							);
						hoveredZoneId = zone.id as number;
						map.setFeatureState(
							{ source: "possible-zones", id: hoveredZoneId },
							{ hover: true },
						);
					}
					onHover({
						zone: zone?.properties ?? undefined,
						official: official?.properties ?? undefined,
						turbine: turbine?.properties ?? undefined,
						x: e.point.x,
						y: e.point.y,
					});
				} else {
					// Clear zone hover
					if (hoveredZoneId !== null) {
						map.setFeatureState(
							{ source: "possible-zones", id: hoveredZoneId },
							{ hover: false },
						);
						hoveredZoneId = null;
					}

					// Band hover in expert mode — collect ALL bands at cursor
					if (currentExpert && get(detailLayersReady)) {
						const hidden = get(hiddenBands);
						const variant = get(settlementVariant);
						const visibleBandLayers = BAND_DEFS
							.filter(d => !hidden.has(d.band))
							.map(d => bandLayerId(activeSlugForDef(d, variant)));
						if (visibleBandLayers.length > 0) {
							const bandFeats = map.queryRenderedFeatures(
								[[e.point.x - 3, e.point.y - 3], [e.point.x + 3, e.point.y + 3]],
								{ layers: visibleBandLayers }
							);
							if (bandFeats.length > 0) {
								const uniqueIds = [...new Set(
									bandFeats.map(f => f.properties?.band_id as number).filter(Boolean)
								)];
								const bands = uniqueIds
									.map(bid => BAND_DEFS.find(d => d.band === bid))
									.filter((d): d is typeof BAND_DEFS[0] => !!d)
									.map(d => ({ label: d.label, description: d.description, color: d.color }));
								if (bands.length > 0) {
									map.getCanvas().style.cursor = 'crosshair';
									onHover({ bands, x: e.point.x, y: e.point.y });
									return;
								}
							}
						}
					}

					onHover(null);

					// Municipality hover
					const muniFeatures = map.queryRenderedFeatures(e.point, {
						layers: ["municipalities-fill"],
					});
					if (muniFeatures.length > 0) {
						map.getCanvas().style.cursor = "pointer";
						const fid = muniFeatures[0].properties?.AGS as string;
						if (fid && hoveredRegionFeatureId !== fid) {
							clearRegionHover();
							hoveredRegionFeatureId = fid;
							map.setFeatureState(
								{ source: "municipalities", sourceLayer: "municipalities", id: fid },
								{ hover: true },
							);
						}
					} else {
						map.getCanvas().style.cursor = "";
						clearRegionHover();
					}
				}
			});

			map.on("click", async (e) => {
				// Turbine clicks: do nothing (no region to navigate to)
				const zoneFeat = map.queryRenderedFeatures(e.point, { layers: zoneLayers });
				if (zoneFeat.length > 0 && zoneFeat.every(f => f.layer.id === "turbines")) return;
				// Zone clicks (potential zones, official zones) fall through to municipality
				// selection — same crosshair + click-to-select behaviour for both.
				const muniFeat = map.queryRenderedFeatures(e.point, {
					layers: ["municipalities-fill"],
				});
				if (muniFeat.length === 0) return;
				const ags = muniFeat[0].properties?.AGS as string | undefined;
				if (!ags) return;
				const fields = "id,name,code,layer,layer_label,postcodes,center,outline,parents";
				const res = await fetch(
					`https://base.klimadashboard.org/items/regions?filter[country][_eq]=AT&filter[code][_eq]=${encodeURIComponent(ags)}&fields=${fields}&limit=1`,
				);
				const json = await res.json();
				const region = json.data?.[0] as Region | undefined;
				if (!region) return;
				selectedRegion.set(region);
				goto("/regions/" + region.id, { noScroll: true });
			});

			map.on("mouseleave", () => {
				map.getCanvas().style.cursor = "";
				if (hoveredZoneId !== null) {
					map.setFeatureState(
						{ source: "possible-zones", id: hoveredZoneId },
						{ hover: false },
					);
					hoveredZoneId = null;
				}
				clearRegionHover();
				onHover(null);
			});
		}

		// ── Band layer activation (once per slug, on first use) ─────────────────
		// MapLibre does not fetch tiles for layers added with fill-opacity:0.
		// On first activation of a given slug we remove-and-readd its layer with
		// real opacity so MapLibre starts loading tiles. After that,
		// setPaintProperty works fine from the tile cache. Tracked per-slug (not
		// one global flag) because the settlement band's 6 variant slugs only
		// need activating once the user actually selects them via the slider.
		let activatedSlugs = new Set<string>();

		function activateBandLayers(variant: SettlementVariant) {
			const hidden = get(hiddenBands);
			for (const def of BAND_DEFS) {
				const slug = activeSlugForDef(def, variant);
				if (activatedSlugs.has(slug)) continue;
				activatedSlugs.add(slug);

				const id = bandLayerId(slug);
				if (map.getLayer(id)) map.removeLayer(id);
				const r = parseInt(def.color.slice(1,3),16);
				const g = parseInt(def.color.slice(3,5),16);
				const b = parseInt(def.color.slice(5,7),16);
				const baseOpacity = (parseInt(def.color.slice(7,9),16) / 255) * 0.6;
				map.addLayer({
					id,
					type: 'fill',
					source: EXCLUSION_BANDS_SOURCE,
					'source-layer': slug,
					paint: {
						'fill-color': `rgb(${r},${g},${b})`,
						'fill-opacity': hidden.has(def.band) ? 0 : baseOpacity,
					},
				}, 'possible-zones-fill');
			}
		}

		// ── Wire everything up ──────────────────────────────────────────────────
		let currentExpert: boolean = false;
		let currentViz: VizMode = "zones";
		let currentStoryStep: number = 0;

		function applyStoryVisibility(step: number) {
			if (!map.isStyleLoaded()) return;

			// Helper: set visibility on a layer if it exists
			const show = (id: string, visible: boolean) => {
				if (map.getLayer(id))
					map.setLayoutProperty(id, "visibility", visible ? "visible" : "none");
			};

			// Bold Austria outline while the story runs; subtle once it's done —
			// see the matching initial style in addAustriaMask().
			if (map.getLayer("austria-border")) {
				const storyActive = step >= 0;
				map.setPaintProperty("austria-border", "line-color", storyActive ? "#0f172a" : "#94a3b8");
				map.setPaintProperty("austria-border", "line-width", storyActive ? 2.5 : 1);
				map.setPaintProperty("austria-border", "line-opacity", storyActive ? 0.9 : 0.5);
			}

			if (step < 0) {
				// Story done — hide exclusion overlays, restore normal layer state
				["exclusion-schutz-fill", "exclusion-siedlung-fill", "exclusion-sonstige-fill", "exclusion-wind-fill"].forEach(
					(id) => show(id, false),
				);
				updateLayers(currentExpert, currentViz);
				["official-zones-fill", "official-zones-outline", "turbines"].forEach(
					(id) => show(id, true),
				);
				if (map.getLayer("turbines")) {
					map.setLayerZoomRange("turbines", 7, 24);
					map.setPaintProperty("turbines", "circle-radius", [
						"interpolate", ["linear"], ["zoom"], 7, 2, 10, 3.5, 13, 5,
					]);
					map.setPaintProperty("turbines", "circle-color", "#1e3a8a");
					map.setPaintProperty("turbines", "circle-stroke-color", "#ffffff");
					map.setPaintProperty("turbines", "circle-stroke-width", 1);
					map.setPaintProperty("turbines", "circle-opacity", 0.85);
				}
				if (map.getLayer("official-zones-fill"))
					map.setPaintProperty("official-zones-fill", "fill-opacity", 1);
				if (map.getLayer("official-zones-outline")) {
					map.setPaintProperty("official-zones-outline", "line-width", 1.5);
					map.setPaintProperty("official-zones-outline", "line-opacity", 0.8);
					map.setPaintProperty("official-zones-outline", "line-dasharray", [4, 2]);
				}
				return;
			}

			// Steps 0–8 (0 Titel, 1 Siedlung, 2 Schutz, 3 Sonstige, 4 Wind,
			// 5 Potential, 6 Zonierung, 7 Windkraft heute, 8 CTA)
			// Exclusion layers: cumulative — each stays visible once introduced
			show("exclusion-siedlung-fill", step >= 1 && step <= 4);
			show("exclusion-schutz-fill",   step >= 2 && step <= 4);
			show("exclusion-sonstige-fill", step >= 3 && step <= 4);
			show("exclusion-wind-fill",     step >= 4 && step <= 4);

			// Potential zones: step 5+
			show("possible-zones-fill",   step >= 5);
			show("possible-zones-border", step >= 5);

			// Official zoning: step 6+
			show("official-zones-fill",    step >= 6);
			show("official-zones-outline", step >= 6);
			if (step >= 6) {
				if (map.getLayer("official-zones-fill"))
					map.setPaintProperty("official-zones-fill", "fill-opacity", 1);
				if (map.getLayer("official-zones-outline")) {
					map.setPaintProperty("official-zones-outline", "line-width", 2.5);
					map.setPaintProperty("official-zones-outline", "line-opacity", 1);
					map.setPaintProperty("official-zones-outline", "line-dasharray", [3, 1.5]);
				}
			}

			// Turbines: step 7+
			show("turbines", step >= 7);
			if (step >= 7 && map.getLayer("turbines")) {
				map.setLayerZoomRange("turbines", 0, 24);
				map.setPaintProperty("turbines", "circle-radius", [
					"interpolate", ["linear"], ["zoom"], 6, 2.5, 10, 4, 13, 6,
				]);
				map.setPaintProperty("turbines", "circle-color", "#fef08a");
				map.setPaintProperty("turbines", "circle-stroke-color", "#ca8a04");
				map.setPaintProperty("turbines", "circle-stroke-width", 1.5);
				map.setPaintProperty("turbines", "circle-opacity", 0.9);
			}

			// Always hide raster + heatmap during story
			["zones-heatmap", "classification-raster"].forEach((id) => show(id, false));
			if (get(detailLayersReady)) {
				for (const def of BAND_DEFS) {
					for (const slug of allSlugsForDef(def)) {
						const id = bandLayerId(slug);
						if (map.getLayer(id)) map.setPaintProperty(id, 'fill-opacity', 0);
					}
				}
			}
		}

		// ── German labels: fetch symbol layers from full GL style, add on top ──────
		// The basemap uses positron-nolabels-gl-style (no streets/buildings/text).
		// We fetch only the symbol layers from the full style, switch text-field
		// to local language (German for AT/DE), and add them above everything.
		async function addGermanLabels() {
			try {
				const style = await fetch(CARTO_LABELS_STYLE).then(r => r.json());
				for (const layer of style.layers.filter((l: { type: string }) => l.type === "symbol")) {
					if (layer.layout?.["text-field"]) {
						layer.layout["text-field"] = JSON.parse(
							JSON.stringify(layer.layout["text-field"]).replace(/name_en/g, "name")
						);
					}
					try { map.addLayer(layer); } catch (_) {}
				}
			} catch (e) {
				console.warn("[labels] could not add German labels:", e);
			}
		}

		map.on("load", () => {
			// Basemap is positron-nolabels: no symbol layers, no streets/buildings.
			// Data layers are added to the top of the stack.
			// addGermanLabels() then places German text labels above all data fills.
			addSources();
			sourcesReady = true;
			addLayers(undefined);
			setupHoverEvents();
			addAustriaMask(); // async, non-blocking
			addGermanLabels(); // async, non-blocking
			updateLayers(currentExpert, currentViz);
			// Override with story visibility if story is active
			applyStoryVisibility(currentStoryStep);
			mapInstance.set(map);
			dataLoaded.set(true);
			// Highlight region that was set before the map finished loading (URL navigation)
			const initialRegion = get(selectedRegion);
			if (initialRegion) highlightRegion(initialRegion);
			updateCenterInfo();
		});

		// "idle" (not "moveend") so the municipalities tile at the new viewport
		// has actually finished loading before we query it for the AGS code.
		map.on("idle", updateCenterInfo);

		// ── Update emptyBands whenever the viewport settles ─────────────────────
		map.on("idle", () => {
			if (!currentExpert || !get(detailLayersReady)) {
				emptyBands.set(new Set());
				return;
			}
			const hidden = get(hiddenBands);
			const variant = get(settlementVariant);
			const visibleLayers = BAND_DEFS
				.filter(d => !hidden.has(d.band))
				.map(d => bandLayerId(activeSlugForDef(d, variant)))
				.filter(id => map.getLayer(id));
			if (visibleLayers.length === 0) return;
			const features = map.queryRenderedFeatures(undefined, { layers: visibleLayers });
			const present = new Set(features.map(f => f.properties?.band_id as number));
			emptyBands.set(new Set(BAND_DEFS.filter(d => !present.has(d.band)).map(d => d.band)));
		});

		const unsubExpert = expertMode.subscribe((expert) => {
			currentExpert = expert;
			// The settlement-distance switch/slider only exists in the expert-mode
			// panel — leaving expert mode always falls back to the legally-accurate
			// Bundesland-specific default scenario.
			if (!expert) settlementVariant.set("default");
			if (currentStoryStep < 0) updateLayers(currentExpert, currentViz);
		});

		const unsubViz = vizMode.subscribe((viz) => {
			currentViz = viz;
			if (currentStoryStep < 0) {
				updateLayers(currentExpert, currentViz);
				applyPitch(viz);
			}
		});

		const unsubRegion = selectedRegion.subscribe((region) => {
			if (!map || !sourcesReady) return;
			if (region) highlightRegion(region);
			else clearRegionHighlight();
		});

		const unsubStory = storyStep.subscribe((step) => {
			const prev = currentStoryStep;
			currentStoryStep = step;
			// Mobile: when the story ends (step goes from ≥0 to -1), the container
			// CSS-transitions from 100vh → 60vh over 0.85s.  Wait for that to finish,
			// then resize the canvas and fly to the proper Austria view.
			if (isMobile && step < 0 && prev >= 0) {
				setTimeout(() => {
					map.resize();
					map.flyTo({ center: AUSTRIA_CENTER, zoom: 6.0, duration: 800 });
				}, 920);
			}
			applyStoryVisibility(step);
		});

		const unsubBands = hiddenBands.subscribe(() => {
			if (map && map.isStyleLoaded() && currentStoryStep < 0) {
				updateLayers(currentExpert, currentViz);
			}
		});

		// Settlement-distance slider: swap the zones/centroids source data and
		// the active settlement-band slug, then recompute the region stats.
		let firstVariantEmit = true;
		const unsubSettlementVariant = settlementVariant.subscribe((variant) => {
			if (firstVariantEmit) {
				// Skip the initial value — addSources() already loaded it.
				firstVariantEmit = false;
				return;
			}
			if (!map || !sourcesReady) return;
			(map.getSource("possible-zones") as maplibregl.GeoJSONSource)?.setData(possibleZonesUrl(variant));
			(map.getSource("zone-centroids") as maplibregl.GeoJSONSource)?.setData(zoneCentroidsUrl(variant));
			if (currentStoryStep < 0) updateLayers(currentExpert, currentViz);
			if (get(selectedRegion)) map.once("idle", computeRegionStats);
		});

		return () => {
			unsubExpert();
			unsubViz();
			unsubRegion();
			unsubStory();
			unsubBands();
			unsubSettlementVariant();
			// Reset per-map state so the next map instance starts clean
			activatedSlugs.clear();
			expertMode.set(false);
			detailLayersReady.set(false);
			emptyBands.set(new Set());
			map.remove();
		};
	});
</script>

<div bind:this={mapContainer} class="w-full h-full"></div>

<style>
	/* Keep MapLibre built-in controls at the same 1rem edge margin as all UI panels */
	:global(.maplibregl-ctrl-top-right .maplibregl-ctrl)    { margin: 1rem 1rem 0 0; }
	:global(.maplibregl-ctrl-bottom-right .maplibregl-ctrl) { margin: 0 1rem 1rem 0; }
	:global(.maplibregl-ctrl-bottom-left .maplibregl-ctrl)  { margin: 0 0 1rem 1rem; }
</style>
