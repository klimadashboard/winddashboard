<script lang="ts">
	import { onMount } from 'svelte';
	import { mapInstance } from '$lib/stores/windStore';

	let canvas: HTMLCanvasElement;
	let animFrame: number;

	const BOUNDS   = { west: 9.5, east: 17.2, south: 46.2, north: 49.1 };
	const LNG_STEP = 0.018;
	const LAT_STEP = 0.013;

	// Wave-bucket batching: dots sorted into longitude bands.
	// Each band shares one wave value → N_BUCKETS sine evals + 2×N_BUCKETS fill calls per frame.
	const N_BUCKETS = 24;

	interface Dot {
		lng:    number;
		lat:    number;
		phase:  number;
		bucket: number;
		hasWind: boolean;
	}

	let dots: Dot[] = [];
	let mapRef: import('maplibre-gl').Map | null = null;
	let isPanning = false;

	// Cached CSS-px positions (rebuilt on move/zoom/resize; live-updated when panning)
	let px: Float32Array = new Float32Array(0);
	let py: Float32Array = new Float32Array(0);

	// buckets[b][0] = no-wind dot indices, [1] = wind dot indices
	let buckets: Uint32Array[][] = [];

	// Austria clip path (CSS px, rebuilt on move/zoom/resize)
	let clipPath: Path2D | null = null;
	let outlineRings: [number, number][][] = [];

	// ── Austria outline ────────────────────────────────────────────────────────
	async function loadOutline() {
		try {
			const feat = await fetch('/data/austria_outline').then(r => r.json()) as
				GeoJSON.Feature<GeoJSON.Polygon | GeoJSON.MultiPolygon>;
			const geo = feat.geometry;
			outlineRings = geo.type === 'Polygon'
				? [geo.coordinates[0] as [number, number][]]
				: geo.coordinates.map(p => p[0] as [number, number][]);
			rebuildClipPath();
		} catch (e) {
			console.warn('[DotGrid] outline load failed:', e);
		}
	}

	function rebuildClipPath() {
		if (!outlineRings.length || !mapRef) { clipPath = null; return; }
		const path = new Path2D();
		for (const ring of outlineRings) {
			let first = true;
			for (const coord of ring) {
				const pt = mapRef.project(coord);
				if (first) { path.moveTo(pt.x, pt.y); first = false; }
				else        { path.lineTo(pt.x, pt.y); }
			}
			path.closePath();
		}
		clipPath = path;
	}

	// ── Grid ──────────────────────────────────────────────────────────────────
	function buildGrid() {
		dots = [];
		const lngSpan = BOUNDS.east - BOUNDS.west;
		for (let lat = BOUNDS.south; lat <= BOUNDS.north; lat += LAT_STEP) {
			for (let lng = BOUNDS.west; lng <= BOUNDS.east; lng += LNG_STEP) {
				const phase  = (lng - BOUNDS.west) / lngSpan;
				const bucket = Math.min(Math.floor(phase * N_BUCKETS), N_BUCKETS - 1);
				dots.push({ lng, lat, phase, bucket, hasWind: false });
			}
		}
		px = new Float32Array(dots.length);
		py = new Float32Array(dots.length);
		rebuildBuckets();
	}

	function rebuildBuckets() {
		const tmp: number[][][] = Array.from({ length: N_BUCKETS }, () => [[], []]);
		for (let i = 0; i < dots.length; i++) {
			const d = dots[i];
			tmp[d.bucket][d.hasWind ? 1 : 0].push(i);
		}
		buckets = tmp.map(b => [new Uint32Array(b[0]), new Uint32Array(b[1])]);
	}

	// ── Projection cache ──────────────────────────────────────────────────────
	function projectAll() {
		if (!mapRef) return;
		for (let i = 0; i < dots.length; i++) {
			const pt = mapRef.project([dots[i].lng, dots[i].lat]);
			px[i] = pt.x;
			py[i] = pt.y;
		}
	}

	// ── Wind classification ────────────────────────────────────────────────────
	let classifyTimer: ReturnType<typeof setTimeout>;
	function scheduleClassify() {
		clearTimeout(classifyTimer);
		classifyTimer = setTimeout(classifyDots, 150);
	}
	function classifyDots() {
		if (!mapRef) return;
		for (let i = 0; i < dots.length; i++) {
			dots[i].hasWind = mapRef.queryRenderedFeatures(
				[Math.round(px[i]), Math.round(py[i])],
				{ layers: ['possible-zones-hit'] }
			).length > 0;
		}
		rebuildBuckets();
	}

	// ── Canvas resize ─────────────────────────────────────────────────────────
	function resize() {
		if (!canvas) return;
		const p = canvas.parentElement!;
		canvas.width  = p.offsetWidth  * devicePixelRatio;
		canvas.height = p.offsetHeight * devicePixelRatio;
		canvas.getContext('2d')!.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
	}

	// ── Map event handlers ────────────────────────────────────────────────────
	function onMoveStart() { isPanning = true; }
	function onMoveEnd()   {
		isPanning = false;
		projectAll();
		rebuildClipPath();
		scheduleClassify();
	}
	function onIdle() { classifyDots(); }

	// ── Draw loop ─────────────────────────────────────────────────────────────
	function draw() {
		if (!canvas || !mapRef) { animFrame = requestAnimationFrame(draw); return; }

		// Keep projection live during smooth panning
		if (isPanning) { projectAll(); rebuildClipPath(); }

		const ctx = canvas.getContext('2d')!;
		const w   = canvas.offsetWidth;
		const h   = canvas.offsetHeight;
		ctx.clearRect(0, 0, w, h);

		ctx.save();
		if (clipPath) ctx.clip(clipPath, 'evenodd');

		const t    = Date.now() / 1000;
		const freq = (2 * Math.PI) / 3;
		const span = 3 * Math.PI;

		for (let b = 0; b < N_BUCKETS; b++) {
			const phase = (b + 0.5) / N_BUCKETS;
			const wave  = 0.5 + 0.5 * Math.sin(t * freq - phase * span);

			// No-wind dots — static grey
			const nwIdx = buckets[b][0];
			if (nwIdx.length) {
				ctx.fillStyle = `rgba(148,163,184,${(0.08 + 0.10 * wave).toFixed(2)})`;
				ctx.beginPath();
				for (let k = 0; k < nwIdx.length; k++) {
					const i = nwIdx[k];
					const x = px[i], y = py[i];
					if (x < -4 || x > w + 4 || y < -4 || y > h + 4) continue;
					ctx.rect(x - 1, y - 1, 2, 2);
				}
				ctx.fill();
			}

			// Wind dots — pulse from grey-ish blue → blue-500 (59,130,246)
			// Interpolate colour: blue-200 (191,219,254) at wave=0 → blue-500 (59,130,246) at wave=1
			const wIdx = buckets[b][1];
			if (wIdx.length) {
				const r = Math.round(191 - 132 * wave);
				const g = Math.round(219 -  89 * wave);
				const bC = Math.round(254 -   8 * wave);
				const a  = (0.70 + 0.20 * wave).toFixed(2);
				const s  = 2.0 + 0.4 * wave;
				ctx.fillStyle = `rgba(${r},${g},${bC},${a})`;
				ctx.beginPath();
				for (let k = 0; k < wIdx.length; k++) {
					const i = wIdx[k];
					const x = px[i], y = py[i];
					if (x < -4 || x > w + 4 || y < -4 || y > h + 4) continue;
					ctx.rect(x - s * 0.5, y - s * 0.5, s, s);
				}
				ctx.fill();
			}
		}

		ctx.restore();
		animFrame = requestAnimationFrame(draw);
	}

	// ── Lifecycle ─────────────────────────────────────────────────────────────
	onMount(() => {
		buildGrid();
		loadOutline();

		const ro = new ResizeObserver(() => {
			resize();
			projectAll();
			rebuildClipPath();
			scheduleClassify();
		});
		ro.observe(canvas.parentElement!);
		resize();

		const unsubMap = mapInstance.subscribe((m) => {
			if (mapRef) {
				mapRef.off('movestart', onMoveStart);
				mapRef.off('moveend',   onMoveEnd);
				mapRef.off('zoomend',   onMoveEnd);
				mapRef.off('idle',      onIdle);
			}
			mapRef = m;
			if (m) {
				m.on('movestart', onMoveStart);
				m.on('moveend',   onMoveEnd);
				m.on('zoomend',   onMoveEnd);
				m.on('idle',      onIdle);
				projectAll();
				rebuildClipPath();
				scheduleClassify();
			}
		});

		animFrame = requestAnimationFrame(draw);

		return () => {
			unsubMap();
			cancelAnimationFrame(animFrame);
			clearTimeout(classifyTimer);
			ro.disconnect();
			if (mapRef) {
				mapRef.off('movestart', onMoveStart);
				mapRef.off('moveend',   onMoveEnd);
				mapRef.off('zoomend',   onMoveEnd);
				mapRef.off('idle',      onIdle);
			}
		};
	});
</script>

<canvas
	bind:this={canvas}
	class="absolute inset-0 w-full h-full pointer-events-none"
	style="z-index: 2;"
></canvas>
