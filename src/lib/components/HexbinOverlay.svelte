<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { mapInstance, vizMode } from '$lib/stores/windStore';

	let canvasEl: HTMLCanvasElement;
	let deck: any     = null;
	let mapRef: any   = null;
	let disposeViz: (() => void) | null = null;

	const COLOR_RANGE = [
		[219, 234, 254],
		[147, 197, 253],
		[ 96, 165, 250],
		[ 59, 130, 246],
		[ 37,  99, 235],
		[ 30,  58, 138],
	];

	async function init(map: any) {
		mapRef = map;

		const [{ Deck }, { HexagonLayer }, geo] = await Promise.all([
			import('@deck.gl/core'),
			import('@deck.gl/aggregation-layers'),
			fetch('/data/zone_centroids').then(r => r.json()),
		]);

		const features: any[] = geo.features;

		// Size canvas to match map container (DPR-aware)
		function resizeCanvas() {
			const p = canvasEl.parentElement!;
			canvasEl.width  = p.offsetWidth  * devicePixelRatio;
			canvasEl.height = p.offsetHeight * devicePixelRatio;
			canvasEl.style.width  = p.offsetWidth  + 'px';
			canvasEl.style.height = p.offsetHeight + 'px';
		}
		resizeCanvas();
		const ro = new ResizeObserver(resizeCanvas);
		ro.observe(canvasEl.parentElement!);

		function viewState() {
			const c = map.getCenter();
			return {
				longitude:  c.lng,
				latitude:   c.lat,
				zoom:       map.getZoom(),
				bearing:    map.getBearing(),
				pitch:      map.getPitch(),
			};
		}

		deck = new Deck({
			canvas:          canvasEl,
			controller:      false,
			useDevicePixels: devicePixelRatio,
			initialViewState: viewState(),
			layers:          [],
		});

		// Keep deck in sync on every map render frame
		function onMapRender() {
			deck?.setProps({ viewState: viewState() });
		}
		map.on('render', onMapRender);

		function makeLayer(visible: boolean) {
			if (!visible) return [];
			return [
				new HexagonLayer({
					id:                  'wind-hexbin',
					data:                features,
					getPosition:         (d: any) => d.geometry.coordinates,
					getColorWeight:      (d: any) => d.properties.pd ?? 0,
					colorAggregation:    'MEAN',
					getElevationWeight:  (d: any) => d.properties.a  ?? 0,
					elevationAggregation:'SUM',
					colorRange:          COLOR_RANGE,
					radius:              8000,
					elevationScale:      0.08,
					extruded:            true,
					coverage:            0.88,
					opacity:             0.88,
					pickable:            false,
					material:            false,
				}),
			];
		}

		disposeViz = vizMode.subscribe(v => {
			deck?.setProps({ layers: makeLayer(v === 'hexbin') });
		});

		// Cleanup
		const origDispose = disposeViz;
		disposeViz = () => {
			origDispose?.();
			map.off('render', onMapRender);
			ro.disconnect();
			deck?.finalize();
			deck = null;
		};
	}

	const unsubMap = mapInstance.subscribe(m => {
		if (m && !deck) init(m);
	});

	onDestroy(() => {
		unsubMap();
		disposeViz?.();
	});
</script>

<!--
  Absolutely-positioned canvas that sits on top of the MapLibre canvas.
  pointer-events:none so map interaction still works.
  z-index 3 puts it above DotGrid (z-index 2).
-->
<canvas
	bind:this={canvasEl}
	class="absolute inset-0 pointer-events-none"
	style="z-index: 3;"
></canvas>
