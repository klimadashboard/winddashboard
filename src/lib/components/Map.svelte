<script lang="ts">
	import { onMount, onDestroy } from "svelte";
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
		mapZoom,
		centerBundesland,
	} from "$lib/stores/windStore";
	import type { VizMode } from "$lib/stores/windStore";
	import { BAND_DEFS, bandLayerId, EXCLUSION_BANDS_SOURCE, EXCLUSION_BANDS_TILES } from "$lib/config/bands";
	import type { BandGroup, BandDef } from "$lib/config/bands";
	import {
		CARTO_BASEMAP,
		CARTO_LABELS_STYLE,
		CARTO_RASTER_CONTEXT,
		AUSTRIA_CENTER,
		AUSTRIA_ZOOM,
		AUSTRIA_BOUNDS,
		CLASSIFICATION_TILES,
		CLASSIFICATION_TILES_MIN_ZOOM,
		CLASSIFICATION_TILES_MAX_ZOOM,
		POSSIBLE_ZONES_TILES,
		POSSIBLE_ZONES_LAYER,
		POSSIBLE_ZONES_MIN_ZOOM,
		POSSIBLE_ZONES_MAX_ZOOM,
	} from "$lib/config/tiles";
	import type { Region } from "$lib/stores/windStore";
	import {
		loadRegionStats,
		statsForRegion,
		boundsForRegion,
	} from "$lib/data/regionStats";
	import type { RegionStatsTable } from "$lib/data/regionStats";

	export interface HoverInfo {
		zone?: Record<string, unknown>;
		official?: Record<string, unknown>;
		hull?: Record<string, unknown>;
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

	// Matches nothing — the resting state of the selected-region highlight layers.
	const NO_REGION_FILTER = ["==", ["get", "AGS"], "\u0000"] as const;

	// Aufräumen läuft über onDestroy, nicht über den Rückgabewert von onMount:
	// die Mount-Funktion ist `async`, Svelte bekommt also ein Promise statt einer
	// Funktion und ruft den Rückgabewert nie auf. Ohne das blieben fünf
	// Store-Abos und die MapLibre-Instanz samt WebGL-Kontext liegen — sichtbar,
	// sobald jemand zur Methodik-Seite und zurück navigiert, denn die liegt
	// außerhalb der (app)-Gruppe und zerstört die Karte.
	let cleanup: (() => void) | null = null;
	onDestroy(() => {
		cleanup?.();
		cleanup = null;
	});

	onMount(async () => {
		// Dynamic import keeps maplibre-gl out of SSR bundle
		const { default: maplibregl } = await import("maplibre-gl");
		await import("maplibre-gl/dist/maplibre-gl.css");

		const isMobile = () => window.innerWidth < 768;

		/**
		 * Passt den Ausschnitt auf Österreich ein und lässt dabei den Platz frei,
		 * den Überlagerungen verdecken.
		 *
		 * Vorher stand hier ein fester Mittelpunkt auf Breitengrad 50 — rund 280 km
		 * nördlich von Österreich, etwa an der bayerisch-tschechischen Grenze.
		 * Damit sollte Österreich unter die Story-Karte rutschen, die auf dem
		 * Telefon die obere Hälfte einnimmt; der Preis war ein Kartenstart mitten
		 * in Bayern, und weil Mittelpunkt und Zoom fest waren, schnitt der
		 * Ausschnitt je nach Seitenverhältnis West- oder Ostösterreich ab.
		 *
		 * Gerechnet wird gegen die tatsächliche Leinwandgröße, nicht gegen
		 * `window.innerHeight`: beim Erzeugen der Karte steht die Containerhöhe
		 * noch nicht fest, und MapLibre verwirft ein Einpassen, dessen Ränder
		 * nicht in die Leinwand passen ("Map cannot fit within canvas").
		 */
		function fitAustria(duration = 0) {
			const { width, height } = map.getCanvas().getBoundingClientRect();
			if (width < 50 || height < 50) return;

			let padding: { top: number; bottom: number; left: number; right: number };
			if (isMobile()) {
				const storyActive = get(storyStep) >= 0;
				padding = {
					// 52 % deckt die Story-Karte der meisten Schritte ab. Bei den
					// längsten Schritten (Zonierung) ist die Karte höher und
					// verdeckt Österreich teilweise — dort ist die Karte ohnehin
					// Hintergrund und der Text die Hauptsache.
					top: storyActive ? Math.round(height * 0.52) : 24,
					// Platz für Attributionszeile und, während der Story, die
					// Schritt-Navigation darüber.
					bottom: storyActive ? 120 : 76,
					left: 16,
					right: 16,
				};
			} else {
				padding = { top: 40, bottom: 40, left: 40, right: 40 };
			}

			// Ränder so stutzen, dass in beiden Achsen mindestens ein Drittel der
			// Leinwand für die Karte übrig bleibt — sonst lehnt MapLibre ab und
			// lässt die Kamera einfach stehen, was als leere Karte erscheint.
			const maxV = height / 3, maxH = width / 3;
			const scaleV = (padding.top + padding.bottom) > maxV * 2
				? (maxV * 2) / (padding.top + padding.bottom) : 1;
			const scaleH = (padding.left + padding.right) > maxH * 2
				? (maxH * 2) / (padding.left + padding.right) : 1;
			padding = {
				top: Math.floor(padding.top * scaleV),
				bottom: Math.floor(padding.bottom * scaleV),
				left: Math.floor(padding.left * scaleH),
				right: Math.floor(padding.right * scaleH),
			};

			map.fitBounds(AUSTRIA_BOUNDS, { padding, duration, maxZoom: 9 });
		}

		const map = new maplibregl.Map({
			container: mapContainer,
			style: CARTO_BASEMAP,
			center: AUSTRIA_CENTER,
			zoom: AUSTRIA_ZOOM,
			minZoom: isMobile() ? 4.5 : 6,
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
			map.addSource("exclusion-schutz", { type: "geojson", data: "/data/exclusion_schutz.json" });
			map.addSource("exclusion-siedlung", { type: "geojson", data: "/data/exclusion_siedlung.json" });
			map.addSource("exclusion-sonstige", { type: "geojson", data: "/data/exclusion_sonstige.json" });
			map.addSource("exclusion-wind", { type: "geojson", data: "/data/exclusion_wind.json" });

			// Vektorkacheln statt GeoJSON: die 15-MB-Datei wurde bei jedem Aufruf
			// vollständig geladen, jetzt kommt nur der sichtbare Ausschnitt.
			// `promoteId` auf zone_id, damit setFeatureState über Kachelgrenzen
			// hinweg dieselbe Fläche trifft — mit generierten IDs bekäme dieselbe
			// Zone in jeder Kachel eine andere und der Hover würde zerreißen.
			map.addSource("possible-zones", {
				type: "vector",
				tiles: [POSSIBLE_ZONES_TILES],
				minzoom: POSSIBLE_ZONES_MIN_ZOOM,
				maxzoom: POSSIBLE_ZONES_MAX_ZOOM,
				promoteId: { [POSSIBLE_ZONES_LAYER]: "zone_id" },
				attribution: "© Klimadashboard",
			});

			map.addSource("official-zones", {
				type: "geojson",
				data: "/data/official_zoning.json",
				generateId: true,
			});

			// Band 38 der Lieferung: die Park-Hüllen um die bestehenden Windräder,
			// soweit sie AUSSERHALB der amtlichen Zonen liegen. Ohne diesen Layer
			// sah das Burgenland aus wie ein Land fast ohne Windkraft-Flächen —
			// dort stehen 397 von 423 Anlagen außerhalb der ausgewiesenen Zonen.
			map.addSource("wka-hulls", {
				type: "geojson",
				data: "/data/wka_bestand_ausserhalb_zonen.json",
				generateId: true,
			});

			map.addSource("turbines", {
				type: "geojson",
				data: "/data/existing_turbines.json",
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
				data: "/data/zone_centroids.json",
			});

			map.addSource("municipalities", {
				type: "vector",
				url: "https://tiles.klimadashboard.org/data/municipalities-at.json",
				promoteId: { "municipalities": "AGS" },
			});

			// Semi-transparent street/building context layer (sits above data fills,
			// below labels). Uses the no-labels raster so text stays solely from the
			// German GL label fetch.
			map.addSource("carto-context", {
				type: "raster",
				tiles: [CARTO_RASTER_CONTEXT],
				tileSize: 256,
				// Keine eigene Attribution: der Basemap-Style nennt CARTO bereits,
				// sonst stand "© CARTO" zweimal in derselben Zeile.
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
				const res = await fetch("/data/austria_outline.json");
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

			// ── Detail band layers — ein Layer je Band, unter den Zonenfüllungen ──
			for (const def of BAND_DEFS) {
				const r = parseInt(def.color.slice(1,3),16);
				const g = parseInt(def.color.slice(3,5),16);
				const b2 = parseInt(def.color.slice(5,7),16);
				const slug = def.slug;
				map.addLayer({ id: bandLayerId(slug), type: "fill", source: EXCLUSION_BANDS_SOURCE, "source-layer": slug, paint: { "fill-color": `rgb(${r},${g},${b2})`, "fill-opacity": 0 } }, B);
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
				"source-layer": POSSIBLE_ZONES_LAYER,
				paint: { "fill-color": "#2563eb", "fill-opacity": ["case", ["boolean", ["feature-state", "hover"], false], 0.72, 0.48] },
			}, B);

			map.addLayer({
				id: "possible-zones-border",
				type: "line",
				source: "possible-zones",
				"source-layer": POSSIBLE_ZONES_LAYER,
				paint: { "line-color": "#1d4ed8", "line-width": 1.5, "line-blur": 0, "line-opacity": 0.55 },
			}, B);

			// Added after possible-zones-fill/border (same beforeId=B) so official
			// zones render visually above them. fill-opacity is fully opaque (1) —
			// at the old 0.12 the blue underneath (0.48/0.72) still showed through
			// and read as "on top" even though this layer is stacked above it.
			// Deep purple (was amber) — pairs better with the blue potential zones.
			// Bestandsflächen: deutlich andere Handschrift als die amtlichen Zonen —
			// Teal statt Violett, durchgezogene statt gestrichelter Kante und nur
			// halb deckend. Sie sind kein Rechtsakt, sondern eine Beobachtung, und
			// dürfen nicht wie eine Ausweisung des Landes gelesen werden.
			map.addLayer({ id: "wka-hulls-fill",    type: "fill", source: "wka-hulls", paint: { "fill-color": "#0891b2", "fill-opacity": 0.4 } }, B);
			// Kante zoomabhängig: in der Übersicht sind die Hüllen nur wenige Pixel
			// groß und lebten allein von der Füllung, im Detail trägt die Kante die
			// Unterscheidung zur gestrichelten violetten Zonengrenze.
			map.addLayer({ id: "wka-hulls-outline", type: "line", source: "wka-hulls", paint: { "line-color": "#0e7490", "line-width": ["interpolate", ["linear"], ["zoom"], 5, 1, 9, 2], "line-opacity": 0.9 } }, B);

			map.addLayer({ id: "official-zones-fill",    type: "fill", source: "official-zones", paint: { "fill-color": "#7c3aed", "fill-opacity": 1 } }, B);
			map.addLayer({ id: "official-zones-outline", type: "line", source: "official-zones", paint: { "line-color": "#6d28d9", "line-width": 1.5, "line-dasharray": [4, 2], "line-opacity": 0.8 } }, B);

			// minzoom 4.5 statt 7, also gleich dem Mindestzoom der Karte: die
			// Übersicht landet je nach Bildschirmgröße zwischen Zoom 4,7 und 7,4.
			// Mit minzoom 7 stand "Bestehende Anlage" in der Legende, ohne dass
			// auf der Karte eine einzige zu sehen war — gemessen: 0 gerenderte
			// Anlagen bei Zoom 4,99. Der Radius beginnt klein, damit die 1.396
			// Anlagen in der Übersicht als feine Punkte lesbar bleiben.
			map.addLayer({
				id: "turbines",
				type: "circle",
				source: "turbines",
				minzoom: 4.5,
				paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 4.5, 1.2, 7, 2, 10, 3.5, 13, 5], "circle-color": "#1e3a8a", "circle-stroke-color": "#ffffff", "circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 4.5, 0.3, 8, 1], "circle-opacity": 0.85 },
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

			// Selected-region outline (Gemeinde, Bezirk, Bundesland) — drawn from
			// the municipalities vector tiles, filtered by GKZ prefix.
			//
			// NOT from the `outline` geometry of the regions API. Those polygons
			// used to be uniformly offset by ~208 m west and ~78 m north (MGI →
			// WGS84 without the datum shift) — that is what made the Rußbach zone
			// look as if it reached into Hausleiten. Corrected in Directus on
			// 2026-09-09 (flow: manual/wip/fix-at-outlines), so the API geometry is
			// now accurate; the tileset stays the source here because it carries
			// the full-resolution boundary, while `outline` is simplified to ~200
			// vertices for transport.
			//
			// A Bezirk highlights as the bundle of its municipalities, since the
			// tileset carries municipality features only.
			map.addLayer({
				id: "region-highlight-fill",
				type: "fill",
				source: "municipalities",
				"source-layer": "municipalities",
				filter: NO_REGION_FILTER,
				paint: { "fill-color": "#1d4ed8", "fill-opacity": 0.06 },
			}, B);
			map.addLayer({
				id: "region-highlight-outline",
				type: "line",
				source: "municipalities",
				"source-layer": "municipalities",
				filter: NO_REGION_FILTER,
				paint: {
					"line-color": "#1d4ed8",
					"line-width": 2.5,
					"line-opacity": 0.9,
				},
			}, B);

			// Invisible hit layers — float above everything; opacity 0 so invisible
			map.addLayer({ id: "possible-zones-hit", type: "fill", source: "possible-zones", "source-layer": POSSIBLE_ZONES_LAYER, paint: { "fill-opacity": 0 } });
			map.addLayer({ id: "official-zones-hit",  type: "fill", source: "official-zones",  paint: { "fill-opacity": 0 } });
			map.addLayer({ id: "wka-hulls-hit",       type: "fill", source: "wka-hulls",       paint: { "fill-opacity": 0 } });
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

			// Detail band layers — opacity-based show/hide.
			if (get(detailLayersReady)) {
				if (expert) {
					try { activateBandLayers(); } catch(e) {
						console.warn('[bands] activateBandLayers failed, resetting:', e);
						activatedSlugs.clear(); // allow retry on next toggle
					}
				}
				const hidden = get(hiddenBands);
				for (const def of BAND_DEFS) {
					const activeSlug = def.slug;
					const baseOpacity = (parseInt(def.color.slice(7,9),16) / 255) * 0.6;
					const showThisBand = expert && !hidden.has(def.band);
					{
						const slug = def.slug;
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

		// True once addSources() has run inside the "load" handler — map.isStyleLoaded()
		// can report true before our custom sources (e.g. "municipalities") exist, so it
		// is not a reliable readiness check on its own.
		let sourcesReady = false;
		// The precomputed per-Gemeinde table (geodata/region_stats.json).
		let statsTable: RegionStatsTable | null = null;

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

		// The GKZ is hierarchical: 1st digit = Bundesland, first 3 = Bezirk. So a
		// Bezirk or Bundesland is exactly the set of municipalities whose GKZ starts
		// with its code, and a prefix comparison selects them all.
		function setRegionHighlight(region: Region | null) {
			const code = region ? String(region.code ?? "").trim() : "";
			const filter: maplibregl.FilterSpecification = !code
				? NO_REGION_FILTER
				: region!.layer === "municipality"
					? ["==", ["get", "AGS"], code]
					: ["==", ["slice", ["get", "AGS"], 0, code.length], code];
			for (const id of ["region-highlight-fill", "region-highlight-outline"]) {
				if (map.getLayer(id)) map.setFilter(id, filter);
			}
		}

		function highlightRegion(region: Region) {
			if (!sourcesReady) return;
			setRegionHighlight(region);

			// Fit to the official bounds from the stats table, falling back to the
			// region's own `outline` (see regionStats.ts on why the table leads).
			const bounds = boundsForRegion(region, statsTable) ?? outlineBounds(region);
			if (bounds) map.fitBounds(bounds, { padding: fitPadding(), duration: 1200 });
		}

		// Einpass-Rand, abhängig von der Kartengröße. Feste 160 px waren auf
		// kleinen Karten mehr als die halbe Höhe: MapLibre bricht dann mit
		// "Map cannot fit within canvas with the given bounds, padding, and/or
		// offset" ab und lässt die Kamera stehen — auf dem Telefon sprang die
		// Karte damit bei einer Suche überhaupt nicht zur gewählten Gemeinde.
		function fitPadding(): number {
			const { width, height } = map.getCanvas().getBoundingClientRect();
			return Math.max(24, Math.min(160, Math.floor(Math.min(width, height) * 0.18)));
		}

		function outlineBounds(region: Region): [number, number, number, number] | null {
			if (!region.outline) return null;
			const coords: [number, number][] =
				region.outline.type === "Polygon"
					? (region.outline.coordinates[0] as [number, number][])
					: region.outline.coordinates.flatMap((poly) => poly[0] as [number, number][]);
			let minLon = Infinity, minLat = Infinity, maxLon = -Infinity, maxLat = -Infinity;
			for (const [lon, lat] of coords) {
				if (lon < minLon) minLon = lon;
				if (lat < minLat) minLat = lat;
				if (lon > maxLon) maxLon = lon;
				if (lat > maxLat) maxLat = lat;
			}
			return Number.isFinite(minLon) ? [minLon, minLat, maxLon, maxLat] : null;
		}

		function clearRegionHighlight() {
			if (!sourcesReady) return;
			setRegionHighlight(null);
			regionStats.set(null);
		}

		// Looks the region's figures up in the precomputed table instead of
		// querying the map. See src/lib/data/regionStats.ts for why.
		function publishRegionStats(region: Region | null) {
			if (!region) { regionStats.set(null); return; }
			regionStats.set(statsForRegion(region, statsTable));
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
			const zoneLayers = ["possible-zones-fill", "official-zones-fill", "wka-hulls-fill", "turbines"];

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
					const hull = zoneFeatures.find((f) => f.layer.id === "wka-hulls-fill");
					const turbine = zoneFeatures.find((f) => f.layer.id === "turbines");
					if (zone) {
						if (hoveredZoneId !== null)
							map.setFeatureState(
								{ source: "possible-zones", sourceLayer: POSSIBLE_ZONES_LAYER, id: hoveredZoneId },
								{ hover: false },
							);
						hoveredZoneId = zone.id as number;
						map.setFeatureState(
							{ source: "possible-zones", sourceLayer: POSSIBLE_ZONES_LAYER, id: hoveredZoneId },
							{ hover: true },
						);
					}
					onHover({
						zone: zone?.properties ?? undefined,
						official: official?.properties ?? undefined,
						hull: hull?.properties ?? undefined,
						turbine: turbine?.properties ?? undefined,
						x: e.point.x,
						y: e.point.y,
					});
				} else {
					// Clear zone hover
					if (hoveredZoneId !== null) {
						map.setFeatureState(
							{ source: "possible-zones", sourceLayer: POSSIBLE_ZONES_LAYER, id: hoveredZoneId },
							{ hover: false },
						);
						hoveredZoneId = null;
					}

					// Band hover in expert mode — collect ALL bands at cursor
					if (currentExpert && get(detailLayersReady)) {
						const hidden = get(hiddenBands);
						const visibleBandLayers = BAND_DEFS
							.filter(d => !hidden.has(d.band))
							.map(d => bandLayerId(d.slug));
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
				const fields = "id,name,slug,code,layer,layer_label,postcodes,center,outline,parents";
				const res = await fetch(
					`https://base.klimadashboard.org/items/regions?filter[country][_eq]=AT&filter[code][_eq]=${encodeURIComponent(ags)}&fields=${fields}&limit=1`,
				);
				const json = await res.json();
				const region = json.data?.[0] as Region | undefined;
				if (!region) return;
				selectedRegion.set(region);
				goto("/regions/" + region.slug, { noScroll: true });
			});

			map.on("mouseleave", () => {
				map.getCanvas().style.cursor = "";
				if (hoveredZoneId !== null) {
					map.setFeatureState(
						{ source: "possible-zones", sourceLayer: POSSIBLE_ZONES_LAYER, id: hoveredZoneId },
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
		// setPaintProperty works fine from the tile cache. Tracked per-slug so a
		// band that is switched on later still gets its one-time activation.
		let activatedSlugs = new Set<string>();

		function activateBandLayers() {
			const hidden = get(hiddenBands);
			for (const def of BAND_DEFS) {
				const slug = def.slug;
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
		// Aus dem Store initialisiert, nicht mit 0: der Store steht auf Nicht-Ebenen
		// bereits auf -1, und ein hartes 0 hätte beim ersten Abo einen Übergang
		// "Story beendet" vorgetäuscht, den es nie gab. Auf dem Telefon löste das
		// den Rückflug zur Österreich-Übersicht aus und überschrieb damit das
		// Einpassen auf die gesuchte Gemeinde.
		let currentStoryStep: number = get(storyStep);

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
				["official-zones-fill", "official-zones-outline", "wka-hulls-fill", "wka-hulls-outline", "turbines"].forEach(
					(id) => show(id, true),
				);
				if (map.getLayer("turbines")) {
					map.setLayerZoomRange("turbines", 4.5, 24);
					map.setPaintProperty("turbines", "circle-radius", [
						"interpolate", ["linear"], ["zoom"], 4.5, 1.2, 7, 2, 10, 3.5, 13, 5,
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

			// Official zoning und Bestandsflächen: step 6+. Beide gehören in denselben
			// Schritt — die Aussage "hier darf gebaut werden" ist ohne "und hier steht
			// schon etwas, ohne dass es ausgewiesen wurde" unvollständig.
			show("official-zones-fill",    step >= 6);
			show("official-zones-outline", step >= 6);
			show("wka-hulls-fill",         step >= 6);
			show("wka-hulls-outline",      step >= 6);
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
					const id = bandLayerId(def.slug);
					if (map.getLayer(id)) map.setPaintProperty(id, 'fill-opacity', 0);
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
			// Erst hier einpassen: jetzt steht die Containergröße fest.
			else fitAustria();
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
			const visibleLayers = BAND_DEFS
				.filter(d => !hidden.has(d.band))
				.map(d => bandLayerId(d.slug))
				.filter(id => map.getLayer(id));
			if (visibleLayers.length === 0) return;
			const features = map.queryRenderedFeatures(undefined, { layers: visibleLayers });
			const present = new Set(features.map(f => f.properties?.band_id as number));
			emptyBands.set(new Set(BAND_DEFS.filter(d => !present.has(d.band)).map(d => d.band)));
		});

		const unsubExpert = expertMode.subscribe((expert) => {
			currentExpert = expert;
			if (currentStoryStep < 0) updateLayers(currentExpert, currentViz);
		});

		const unsubViz = vizMode.subscribe((viz) => {
			currentViz = viz;
			if (currentStoryStep < 0) {
				updateLayers(currentExpert, currentViz);
				applyPitch(viz);
			}
		});

		// Not inside the "load" handler: the region figures come from a JSON
		// table, not from the map, and must resolve even if the style is slow
		// or fails. Otherwise a region page can sit on "Daten werden geladen …".
		loadRegionStats().then((table) => {
			statsTable = table;
			publishRegionStats(get(selectedRegion));
		});

		const unsubRegion = selectedRegion.subscribe((region) => {
			// Stats first, and unconditionally: they come from the precomputed
			// table, not from the map, so they must not wait for style/source
			// readiness. On a direct load of /regions/[id] the region arrives
			// before the map is ready, and the old map-gated path left the
			// Inspector stuck on "Daten werden geladen …" for good.
			publishRegionStats(region);
			if (!map || !sourcesReady) return;
			if (region) highlightRegion(region);
			else clearRegionHighlight();
		});

		const unsubStory = storyStep.subscribe((step) => {
			const prev = currentStoryStep;
			currentStoryStep = step;
			// Mobile: when the story ends (step goes from ≥0 to -1), the container
			// CSS-transitions from 100vh → 60vh over 0.85s.  Wait for that to finish,
			// then resize the canvas and fly to the proper Austria view. Greift nur
			// nach einer tatsächlich gelaufenen Story — siehe currentStoryStep oben.
			if (isMobile() && step < 0 && prev >= 0) {
				setTimeout(() => {
					map.resize();
					// Nach dem Ende der Story ist die Karte nur noch 60vh hoch und
					// die Story-Karte weg — neu einpassen statt fester Zoomwert.
					if (!get(selectedRegion)) fitAustria(800);
				}, 920);
			}
			applyStoryVisibility(step);
		});

		const unsubBands = hiddenBands.subscribe(() => {
			if (map && map.isStyleLoaded() && currentStoryStep < 0) {
				updateLayers(currentExpert, currentViz);
			}
		});

		cleanup = () => {
			unsubExpert();
			unsubViz();
			unsubRegion();
			unsubStory();
			unsubBands();
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
