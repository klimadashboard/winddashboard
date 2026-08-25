<script lang="ts">
	import { onMount } from "svelte";
	import { fly, fade, slide } from "svelte/transition";
	import type { Snippet } from "svelte";
	import { storyStep } from "$lib/stores/windStore";
	import RenewableGoalsChart from "./RenewableGoalsChart.svelte";
	import { AUSTRIA_HA } from "$lib/config/austria";
	import { BEZIRK_TO_BUNDESLAND } from "$lib/config/bezirke";

	let { onComplete }: { onComplete: () => void } = $props();

	// ── State ─────────────────────────────────────────────────────────────────
	let scrollEl = $state<HTMLDivElement | null>(null);
	let step = $state(0);
	let exiting = $state(false);
	let dataReady = $state(false);

	// ── Live stats (fetched) ──────────────────────────────────────────────────
	let officialAreaHa = $state(0);
	let turbineCount = $state(0);
	let turbineGWh = $state(0);
	let zoningByBL = $state<Record<string, number>>({});
	let turbinesByBL = $state<Record<string, number>>({});

	// Potentialflächen step: absolute (ha, compared across states) vs. percent
	// of each state's own area. Absolute is the default — the % view is an
	// opt-in toggle, not the default.
	let potentialViewMode = $state<"absolute" | "percent">("absolute");

	// ── Constants from raster analysis (osm_wka_distance_zones_widmung.tif,
	// "default" Bundesland-specific settlement-distance scenario). Verified
	// against a fresh run of create_classification_from_simplified.py —
	// see PIPELINE.md §6. ──────────────────────────────────────────────────
	const SCHUTZ_HA = 987_740; // code 1
	const SIEDLUNG_HA = 4_678_664; // code 2
	const SONSTIGE_HA = 2_280_513; // codes 3–10, 12–13 (infrastructure/terrain)
	const WIND_HA = 38_530; // code 11, Wind zu gering (<150 W/m²) — split out of "Sonstige"
	const POTENTIAL_HA = 355_378; // code 14, raster-based

	// Vector-derived potential (used in the "final" headline)
	const POTENTIAL_VECTOR_HA = 351_912;

	// Colors for the persistent header bar — fixed left-to-right stacking
	// order: each category's segment appears once its step is reached and
	// stays for the rest of the story.
	const COLOR_SIEDLUNG = "#fb923c";
	const COLOR_SCHUTZ = "#4ade80";
	const COLOR_SONSTIGE = "#94a3b8";
	const COLOR_WIND = "#db2777";
	const COLOR_POTENTIAL = "#2563eb";
	const COLOR_ZONIERT = "#6d28d9";

	// Each Bundesland's own total area in hectares — derived from the same
	// classification raster as AUSTRIA_HA (rasterized per state; see
	// scripts/compute_bundesland_areas.py), so the "% of own area" view stays
	// internally consistent with the rest of the pipeline. Cross-checked
	// against Statistik Austria ("Fläche und Benützungsarten", Stand 1.1.2025,
	// Bundesamt für Eich- und Vermessungswesen): every state is within ~1% of
	// the official figure (raster slightly undercounts everywhere due to
	// boundary pixels) — no state is an outlier.
	const BUNDESLAND_HA: Record<string, number> = {
		"Niederösterreich": 1_913_316,
		"Steiermark": 1_629_196,
		"Tirol": 1_252_069,
		"Oberösterreich": 1_193_705,
		"Kärnten": 948_875,
		"Salzburg": 709_212,
		"Burgenland": 395_412,
		"Vorarlberg": 257_781,
		"Wien": 41_467,
	};

	// ── Bundesland breakdown (vector data, sorted by potential area) ─────────
	const BUNDESLAENDER = [
		{ name: "Niederösterreich", short: "NÖ", ha: 152_967 },
		{ name: "Burgenland", short: "B", ha: 48_457 },
		{ name: "Steiermark", short: "ST", ha: 47_855 },
		{ name: "Oberösterreich", short: "OÖ", ha: 36_428 },
		{ name: "Tirol", short: "T", ha: 21_673 },
		{ name: "Kärnten", short: "K", ha: 19_613 },
		{ name: "Salzburg", short: "S", ha: 18_617 },
		{ name: "Vorarlberg", short: "V", ha: 4_358 },
		{ name: "Wien", short: "W", ha: 59 },
	];

	// 0 Titel · 1 Siedlung · 2 Schutz · 3 Sonstige · 4 Wind · 5 Potential ·
	// 6 Zonierung · 7 Windkraft heute · 8 CTA
	const NUM_STEPS = 9;

	// The persistent header bar's segments — cumulative, in fixed left-to-
	// right order. Each appears (and stays) once its step is reached, so the
	// bar keeps growing all the way through the rest of the story.
	const revealedSegments = $derived.by(() => {
		const segs: { key: string; ha: number; color: string }[] = [];
		if (step >= 1)
			segs.push({ key: "siedlung", ha: SIEDLUNG_HA, color: COLOR_SIEDLUNG });
		if (step >= 2)
			segs.push({ key: "schutz", ha: SCHUTZ_HA, color: COLOR_SCHUTZ });
		if (step >= 3)
			segs.push({ key: "sonstige", ha: SONSTIGE_HA, color: COLOR_SONSTIGE });
		if (step >= 4) segs.push({ key: "wind", ha: WIND_HA, color: COLOR_WIND });
		if (step >= 5)
			segs.push({ key: "potential", ha: POTENTIAL_HA, color: COLOR_POTENTIAL });
		return segs;
	});

	const maxTurbinesByBL = $derived(
		Math.max(1, ...Object.values(turbinesByBL)),
	);

	function fmt(n: number, d = 0) {
		return n.toLocaleString("de-AT", { maximumFractionDigits: d });
	}

	// ── Data loading ──────────────────────────────────────────────────────────
	async function loadData() {
		const [offGj, turbGj] = await Promise.all([
			fetch("/data/official_zoning").then((r) => r.json()),
			fetch("/data/existing_turbines").then((r) => r.json()),
		]);
		officialAreaHa = offGj.features.reduce(
			(s: number, f: any) => s + (f.properties.area_ha ?? 0),
			0,
		);
		const byBL: Record<string, number> = {};
		for (const f of offGj.features) {
			const bl: string = f.properties.bundesland ?? "";
			byBL[bl] = (byBL[bl] ?? 0) + (f.properties.area_ha ?? 0);
		}
		zoningByBL = byBL;
		turbineCount = turbGj.features.length;
		const turbinesByBLCount: Record<string, number> = {};
		for (const f of turbGj.features) {
			const bl = BEZIRK_TO_BUNDESLAND[f.properties.bezirk ?? ""];
			if (bl) turbinesByBLCount[bl] = (turbinesByBLCount[bl] ?? 0) + 1;
		}
		turbinesByBL = turbinesByBLCount;
		const totalKW: number = turbGj.features.reduce(
			(s: number, f: any) => s + (f.properties.power_kw ?? 0),
			0,
		);
		turbineGWh = Math.round((totalKW * 0.3 * 8760) / 1_000_000);
		dataReady = true;
	}

	function complete() {
		exiting = true;
		storyStep.set(-1);
		setTimeout(onComplete, 600);
	}

	function scrollTo(s: number) {
		scrollEl?.scrollTo({ top: s * window.innerHeight, behavior: "smooth" });
	}

	function handleScroll() {
		if (!scrollEl) return;
		const newStep = Math.min(
			Math.round(scrollEl.scrollTop / window.innerHeight),
			NUM_STEPS - 1,
		);
		if (newStep !== step) {
			step = newStep;
			storyStep.set(newStep);
		}
	}

	// Keyboard nav: the story otherwise only responds to scroll/wheel/touch and
	// the (small, hard-to-tab-to) pagination dots — arrow/space/page keys give
	// keyboard users the same step-by-step control, Escape matches the usual
	// "leave the overlay" convention for full-screen takeovers.
	function handleKeydown(e: KeyboardEvent) {
		switch (e.key) {
			case "ArrowDown":
			case "ArrowRight":
			case "PageDown":
			case " ":
				e.preventDefault();
				scrollTo(Math.min(step + 1, NUM_STEPS - 1));
				break;
			case "ArrowUp":
			case "ArrowLeft":
			case "PageUp":
				e.preventDefault();
				scrollTo(Math.max(step - 1, 0));
				break;
			case "Home":
				e.preventDefault();
				scrollTo(0);
				break;
			case "End":
				e.preventDefault();
				scrollTo(NUM_STEPS - 1);
				break;
			case "Escape":
				e.preventDefault();
				complete();
				break;
		}
	}

	onMount(() => {
		storyStep.set(0);
		loadData();
	});
</script>

<svelte:window onkeydown={handleKeydown} />

<div
	class="fixed inset-0 z-40 transition-opacity duration-500"
	style="opacity:{exiting ? 0 : 1}; pointer-events:{exiting ? 'none' : 'auto'};"
>
	<!-- ── Scroll spacer ── -->
	<div
		bind:this={scrollEl}
		onscroll={handleScroll}
		class="absolute inset-0"
		style="overflow-y:scroll; z-index:0;"
	>
		<div style="height:{NUM_STEPS * 100}vh;"></div>
	</div>

	<!-- ── Slide cards ── -->
	<div class="absolute inset-0 pointer-events-none" style="z-index:10;">
		<!--
			revealBarHeader: persistent area breakdown bar, shown at the bottom
			of every card's text container (not full-bleed — user feedback showed
			the earlier edge-to-edge placement at the top of the card read as
			decoration, not data people connected to the text). Rounded pill
			track; each category segment slides in from the left the step it's
			revealed on, then stays for the rest of the story (steps 5–8 keep the
			fully-grown bar, including the blue Potenzial segment from step 5
			on). From step 6 (Zonierungsflächen) a dotted line inside the blue
			segment marks how much of the Potenzial is actually zoned.
		-->
		{#snippet revealBarHeader()}
			<div
				class="w-full flex rounded-full overflow-hidden"
				style="height:0.5rem; background:#e2e8f0;"
			>
				{#each revealedSegments as seg (seg.key)}
					<div
						class="h-full relative"
						style="width:{(seg.ha / AUSTRIA_HA) *
							100}%; background:{seg.color};"
						in:slide={{ axis: "x", duration: 500 }}
					>
						{#if seg.key === "potential" && step >= 6 && officialAreaHa > 0}
							<div
								class="absolute inset-y-0"
								style="left:{Math.min(
									100,
									(officialAreaHa / POTENTIAL_HA) * 100,
								)}%; border-left:1.5px dotted #0f172a;"
							></div>
						{/if}
					</div>
				{/each}
			</div>
		{/snippet}

		<!--
			slidePanel: common white card shell shared by every step.
			  inner    — snippet with the card's body content
			  align    — 'left' (default) pins card top-left; 'center' centers it
			  maxWidth — Tailwind max-w-* class (default 'max-w-sm')
			  padding  — Tailwind p-* class (default 'p-6')

			  Margins: all panels use 1rem (p-4) from every screen edge — matching
			  the map control panel (top-4 left-4) and the MapLibre zoom margin.
			  Left-aligned panels get pr-16 on mobile to clear the top-right zoom
			  controls; center-aligned panels sit near the top on mobile so the map
			  stays visible below.
		-->
		{#snippet slidePanel(
			inner: Snippet,
			align: "left" | "center" = "left",
			maxWidth = "max-w-sm",
			padding = "p-6",
		)}
			<div
				class="absolute inset-0 flex flex-col
					{align === 'center'
					? 'p-4 items-center justify-start sm:justify-center'
					: 'pt-[8%] pl-4 pb-4 pr-16 sm:pr-4 items-start justify-start'}"
				transition:fade={{ duration: 300 }}
			>
				<div
					class="bg-white/95 backdrop-blur-sm rounded-md overflow-hidden w-full {maxWidth} shadow-lg pointer-events-auto"
					in:fly={{ y: 20, duration: 400, delay: 80 }}
					onwheel={(e) => scrollEl?.scrollBy({ top: e.deltaY })}
				>
					<div class={padding}>
						{@render inner()}
						<div class="mt-4">
							{@render revealBarHeader()}
						</div>
					</div>
				</div>
			</div>
		{/snippet}

		<!-- Step 0: Titel + Gesamtfläche -->
		{#if step === 0}
			{#snippet step0()}
				<p
					class="text-[10px] font-bold uppercase tracking-widest mb-2"
					style="color:#3b82f6;"
				>
					Windpotenzial Österreich
				</p>
				<h1
					class="font-extrabold text-xl leading-snug mb-3"
					style="color:#0f172a;"
				>
					Wo der Wind weht: Windpotentiale in Österreich
				</h1>
				<p class="text-sm text-slate-600 leading-relaxed mb-4">
					Österreich hat <strong class="text-slate-800"
						>{fmt(AUSTRIA_HA)}&thinsp;ha</strong
					> Fläche. Aber nicht überall darf man ein Windrad hinbauen.
				</p>

				<div class="mt-4 flex flex-col gap-2">
					<button
						class="w-full flex items-center justify-center gap-1.5 py-2.5 px-4 rounded-xl text-sm font-semibold text-white hover:opacity-90 transition-opacity"
						style="background:#1d4ed8;"
						onclick={() => scrollTo(1)}
						onwheel={(e) => scrollEl?.scrollBy({ top: e.deltaY })}
					>
						Scrolle, um mehr zu erfahren
						<svg class="w-4 h-5" viewBox="0 0 16 24" fill="none">
							<rect
								x="1"
								y="1"
								width="14"
								height="22"
								rx="7"
								stroke="currentColor"
								stroke-width="1.5"
							/>
							<circle cx="8" cy="7" r="1.6" fill="currentColor">
								<animate
									attributeName="cy"
									values="7;15;7"
									dur="1.6s"
									repeatCount="indefinite"
								/>
								<animate
									attributeName="opacity"
									values="1;0;0"
									dur="1.6s"
									repeatCount="indefinite"
								/>
							</circle>
						</svg>
					</button>
					<button
						class="w-full py-2 px-4 rounded-xl text-sm text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
						onclick={complete}
						onwheel={(e) => scrollEl?.scrollBy({ top: e.deltaY })}
					>
						Direkt zur interaktiven Karte springen
					</button>
				</div>
			{/snippet}
			{@render slidePanel(step0, "center", "max-w-md")}
		{/if}

		<!-- Step 1: Siedlungsabstand -->
		{#if step === 1}
			{#snippet step1()}
				<div class="flex items-center gap-2 mb-3">
					<span
						class="w-3 h-3 rounded-sm shrink-0"
						style="background:{COLOR_SIEDLUNG};"
					></span>
					<p
						class="text-[10px] font-bold uppercase tracking-widest"
						style="color:#ea580c;"
					>
						Siedlungsabstand
					</p>
				</div>
				<p class="text-sm leading-relaxed text-slate-700 mb-3">
					Je nach Bundesland gilt ein Mindestabstand von <strong
						class="text-slate-900">1 bis 1,2&thinsp;km</strong
					>
					zu Wohngebäuden und Siedlungen. Das schließt
					<strong class="text-slate-900">{fmt(SIEDLUNG_HA)}&thinsp;ha</strong> aus
					— mehr als die Hälfte des Landes.
				</p>
				<div class="flex justify-between">
					<span class="text-[9px] text-orange-600 font-medium"
						>− {fmt(SIEDLUNG_HA)}&thinsp;ha</span
					>
					<span class="text-[9px] text-slate-400"
						>von {fmt(AUSTRIA_HA)}&thinsp;ha</span
					>
				</div>
			{/snippet}
			{@render slidePanel(step1)}
		{/if}

		<!-- Step 2: Naturschutzgebiete -->
		{#if step === 2}
			{#snippet step2()}
				<div class="flex items-center gap-2 mb-3">
					<span
						class="w-3 h-3 rounded-sm shrink-0"
						style="background:{COLOR_SCHUTZ};"
					></span>
					<p
						class="text-[10px] font-bold uppercase tracking-widest"
						style="color:#16a34a;"
					>
						Naturschutzgebiete
					</p>
				</div>
				<p class="text-sm leading-relaxed text-slate-700 mb-3">
					Weitere <strong class="text-slate-900"
						>{fmt(SCHUTZ_HA)}&thinsp;ha</strong
					> entfallen auf Naturschutzgebiete — Nationalparks, Naturparks, Natura-2000-Gebiete
					und Ramsar-Feuchtgebiete. Diese Flächen sind für Windkraft ausgeschlossen.
				</p>
				<div class="flex justify-between">
					<span class="text-[9px] text-green-600 font-medium"
						>− {fmt(SCHUTZ_HA)}&thinsp;ha</span
					>
					<span class="text-[9px] text-slate-400"
						>von {fmt(AUSTRIA_HA)}&thinsp;ha</span
					>
				</div>
			{/snippet}
			{@render slidePanel(step2)}
		{/if}

		<!-- Step 3: Weitere Ausschlüsse (Infrastruktur, Gelände) -->
		{#if step === 3}
			{#snippet step3()}
				<div class="flex items-center gap-2 mb-3">
					<span
						class="w-3 h-3 rounded-sm shrink-0"
						style="background:{COLOR_SONSTIGE};"
					></span>
					<p
						class="text-[10px] font-bold uppercase tracking-widest"
						style="color:#64748b;"
					>
						Weitere Ausschlüsse
					</p>
				</div>
				<p class="text-sm leading-relaxed text-slate-700 mb-3">
					Bestehende Infrastruktur (Straßen, Freileitungen) und ungeeignetes
					Gelände (Hangneigung, Seehöhe) schließen weitere
					<strong class="text-slate-900">{fmt(SONSTIGE_HA)}&thinsp;ha</strong> aus.
				</p>
				<div class="flex justify-between">
					<span class="text-[9px] text-slate-500 font-medium"
						>− {fmt(SONSTIGE_HA)}&thinsp;ha</span
					>
					<span class="text-[9px] text-slate-400"
						>von {fmt(AUSTRIA_HA)}&thinsp;ha</span
					>
				</div>
			{/snippet}
			{@render slidePanel(step3)}
		{/if}

		<!-- Step 4: Zu wenig Wind -->
		{#if step === 4}
			{#snippet step4()}
				<div class="flex items-center gap-2 mb-3">
					<span
						class="w-3 h-3 rounded-sm shrink-0"
						style="background:{COLOR_WIND};"
					></span>
					<p
						class="text-[10px] font-bold uppercase tracking-widest"
						style="color:#9d174d;"
					>
						Zu wenig Wind
					</p>
				</div>
				<p class="text-sm leading-relaxed text-slate-700 mb-3">
					Auf Basis des European Wind Atlas wurden Standorte mit zu geringem
					Wind ausgeschlossen — weitere <strong class="text-slate-900"
						>{fmt(WIND_HA)}&thinsp;ha</strong
					>. Diese Daten dienen jedoch nur einer ersten Einschätzung: Für
					konkrete Windkraftprojekte sind immer eigene Windmessungen am Standort
					über einen Zeitraum von mindestens einem Jahr erforderlich.
				</p>
				<div class="flex justify-between mb-4">
					<span class="text-[9px] font-medium" style="color:#9d174d;"
						>− {fmt(WIND_HA)}&thinsp;ha</span
					>
					<span class="text-[9px] text-slate-400"
						>von {fmt(AUSTRIA_HA)}&thinsp;ha</span
					>
				</div>

				<!-- Legend: recap of every exclusion category + the Potenzial preview -->
				<div class="space-y-1 text-[10px] text-slate-500">
					<div class="flex items-center gap-1.5">
						<span
							class="w-2 h-2 rounded-sm"
							style="background:{COLOR_SIEDLUNG};"
						></span>Siedlungsabstand
					</div>
					<div class="flex items-center gap-1.5">
						<span class="w-2 h-2 rounded-sm" style="background:{COLOR_SCHUTZ};"
						></span>Naturschutzgebiete
					</div>
					<div class="flex items-center gap-1.5">
						<span
							class="w-2 h-2 rounded-sm"
							style="background:{COLOR_SONSTIGE};"
						></span>Infrastruktur, Gelände
					</div>
					<div class="flex items-center gap-1.5">
						<span class="w-2 h-2 rounded-sm" style="background:{COLOR_WIND};"
						></span>Wind zu gering
					</div>
					<div class="flex items-center gap-1.5">
						<span
							class="w-2 h-2 rounded-sm"
							style="background:{COLOR_POTENTIAL};"
						></span>Windpotenzial
					</div>
				</div>
			{/snippet}
			{@render slidePanel(step4)}
		{/if}

		<!-- Step 5: Potentialflächen nach Bundesland -->
		{#if step === 5}
			{#snippet step5()}
				<div class="flex items-center gap-2 mb-3">
					<span
						class="w-3 h-3 rounded-sm shrink-0"
						style="background:{COLOR_POTENTIAL};"
					></span>
					<p
						class="text-[10px] font-bold uppercase tracking-widest"
						style="color:#1d4ed8;"
					>
						Potentialflächen
					</p>
				</div>
				<p class="text-sm leading-relaxed text-slate-700 mb-3">
					Somit bleiben <strong class="text-slate-900"
						>~{fmt(POTENTIAL_VECTOR_HA)}&thinsp;ha</strong
					>
					in ganz Österreich als Potentialflächen für Windkraft übrig — verteilt
					auf alle 9 Bundesländer. Das sind ca.
					<strong class="text-slate-900"
						>{fmt((POTENTIAL_VECTOR_HA / AUSTRIA_HA) * 100, 1)}&thinsp;%</strong
					> der österreichischen Landesfläche.
				</p>

				<!-- Absolut (default) vs. Anteil an der Bundeslandfläche toggle -->
				<div class="flex items-center gap-1 mb-2">
					<button
						class="text-[9px] font-semibold px-2 py-1 rounded-full transition-colors cursor-pointer"
						style="background:{potentialViewMode === 'absolute'
							? COLOR_POTENTIAL
							: '#f1f5f9'}; color:{potentialViewMode === 'absolute'
							? '#fff'
							: '#64748b'};"
						onclick={() => (potentialViewMode = "absolute")}
					>
						Absolut
					</button>
					<button
						class="text-[9px] font-semibold px-2 py-1 rounded-full transition-colors cursor-pointer"
						style="background:{potentialViewMode === 'percent'
							? COLOR_POTENTIAL
							: '#f1f5f9'}; color:{potentialViewMode === 'percent'
							? '#fff'
							: '#64748b'};"
						onclick={() => (potentialViewMode = "percent")}
					>
						% der Fläche
					</button>
				</div>

				<!-- Bundesland bars: "Absolut" compares ha directly (scaled against
					 the largest state, NÖ), no track background since there's no
					 100%-of-something reference being shown. "% der Fläche" shows
					 each bar's fill as % of that state's own total area, with a
					 track background representing that state's full area. -->
				<div class="space-y-1.5">
					{#each BUNDESLAENDER as bl}
						{@const stateHa = BUNDESLAND_HA[bl.name] ?? bl.ha}
						{@const absPct = (bl.ha / BUNDESLAENDER[0].ha) * 100}
						{@const ownPct = (bl.ha / stateHa) * 100}
						{@const pct = potentialViewMode === "absolute" ? absPct : ownPct}
						<div class="flex items-center gap-2">
							<span class="w-6 text-[9px] text-slate-500 text-right shrink-0"
								>{bl.short}</span
							>
							<div
								class="flex-1 h-3 rounded-sm overflow-hidden {potentialViewMode ===
								'percent'
									? 'bg-slate-100'
									: ''}"
							>
								<div
									class="h-full rounded-sm transition-all duration-300"
									style="width:{pct}%; background:{COLOR_POTENTIAL}; opacity:0.85;"
								></div>
							</div>
							<span class="text-[9px] text-slate-500 w-24 shrink-0"
								>{fmt(bl.ha)}&thinsp;ha{#if potentialViewMode === "percent"}
									&nbsp;({fmt(ownPct, 1)}&thinsp;%){/if}</span
							>
						</div>
					{/each}
				</div>

				<!-- Legend -->
				<div class="flex items-center gap-1.5 mt-3 text-[9px] text-slate-500">
					<span
						class="w-2.5 h-2.5 rounded-sm"
						style="background:{COLOR_POTENTIAL}; opacity:0.85;"
					></span>
					{#if potentialViewMode === "absolute"}
						Potenzial (ha) — Vergleich zwischen Bundesländern
					{:else}
						Potenzial — % der jeweiligen Bundeslandfläche
					{/if}
				</div>
			{/snippet}
			{@render slidePanel(step5)}
		{/if}

		<!-- Step 6: Zonierungsflächen -->
		{#if step === 6}
			{#snippet step6()}
				<div class="flex items-center gap-2 mb-3">
					<span
						class="inline-block w-7 border-t-2 border-dashed shrink-0"
						style="border-color:{COLOR_ZONIERT};"
					></span>
					<p
						class="text-[10px] font-bold uppercase tracking-widest"
						style="color:#5b21b6;"
					>
						Zonierungsflächen
					</p>
				</div>
				<p class="text-sm leading-relaxed text-slate-700 mb-4">
					Einige Bundesländer haben für den Bau von Windrädern eigene
					Windkraft-Eignungszonen ausgewiesen. Hier seht ihr diese
					„Zonierungsflächen".
					{#if dataReady}
						Das sind aktuell <strong class="text-slate-900"
							>{fmt(Math.round(officialAreaHa))}&thinsp;ha</strong
						>.
					{/if}
					Folgende Bundesländer haben aktuell Windkraft-Eignungszonen
					ausgewiesen: Niederösterreich, Burgenland, Steiermark, Kärnten und
					Salzburg. In Tirol, Vorarlberg und Wien gibt es aktuell keine
					solchen Windkraft-Eignungszonen. In Oberösterreich wird momentan an
					einer solchen Zonierung gearbeitet und in der Steiermark wird die
					derzeitige Zonierung gerade überarbeitet.
				</p>

				<!-- Bundesland bars: potential (light blue) + zoned (purple) overlay,
					 both as absolute ha scaled against the largest state (NÖ) — same
					 scale as step 5's "Absolut" view, no track background since
					 there's no 100%-of-something reference being shown. -->
				<div class="space-y-1.5">
					{#each BUNDESLAENDER as bl}
						{@const potPct = (bl.ha / BUNDESLAENDER[0].ha) * 100}
						{@const zonedHa = zoningByBL[bl.name] ?? 0}
						{@const zonedPct = (zonedHa / BUNDESLAENDER[0].ha) * 100}
						<div class="flex items-center gap-2">
							<span class="w-6 text-[9px] text-slate-500 text-right shrink-0"
								>{bl.short}</span
							>
							<div class="flex-1 relative h-3 rounded-sm overflow-hidden">
								<!-- potential -->
								<div
									class="absolute inset-y-0 left-0 rounded-sm"
									style="width:{potPct}%; background:{COLOR_POTENTIAL}; opacity:0.25;"
								></div>
								<!-- zoned -->
								{#if zonedHa > 0}
									<div
										class="absolute inset-y-0 left-0 rounded-sm"
										style="width:{zonedPct}%; background:{COLOR_ZONIERT};"
									></div>
								{/if}
							</div>
							<span
								class="text-[9px] w-16 shrink-0 {zonedHa > 0
									? 'font-semibold'
									: 'text-slate-400'}"
								style={zonedHa > 0 ? "color:#5b21b6;" : ""}
							>
								{zonedHa > 0 ? fmt(Math.round(zonedHa)) + " ha" : "–"}
							</span>
						</div>
					{/each}
				</div>

				<!-- Legend -->
				<div class="flex gap-4 mt-3 text-[9px] text-slate-500">
					<div class="flex items-center gap-1">
						<span
							class="w-2.5 h-2.5 rounded-sm"
							style="background:{COLOR_POTENTIAL}; opacity:0.25;"
						></span>
						Potenzial (ha)
					</div>
					<div class="flex items-center gap-1">
						<span
							class="w-2.5 h-2.5 rounded-sm"
							style="background:{COLOR_ZONIERT};"
						></span>
						Zoniert (ha)
					</div>
				</div>
			{/snippet}
			{@render slidePanel(step6)}
		{/if}

		<!-- Step 7: Windräder heute (Bestand nach Bundesland) -->
		{#if step === 7}
			{#snippet turbineIcon()}
				<svg viewBox="0 0 16 16" width="11" height="11" class="shrink-0" fill="none">
					<line x1="8" y1="5" x2="8" y2="15" stroke="#ca8a04" stroke-width="1.4" stroke-linecap="round" />
					<circle cx="8" cy="5" r="1.1" fill="#ca8a04" />
					<line x1="8" y1="5" x2="12.5" y2="3" stroke="#eab308" stroke-width="1.6" stroke-linecap="round" />
					<line x1="8" y1="5" x2="3.8" y2="4" stroke="#eab308" stroke-width="1.6" stroke-linecap="round" />
					<line x1="8" y1="5" x2="8.8" y2="0.5" stroke="#eab308" stroke-width="1.6" stroke-linecap="round" />
				</svg>
			{/snippet}
			{#snippet step7()}
				<div class="flex items-center gap-2 mb-3">
					<span
						class="inline-block w-3 h-3 rounded-full border-2 shrink-0"
						style="background:#fef08a; border-color:#ca8a04;"
					></span>
					<p
						class="text-[10px] font-bold uppercase tracking-widest"
						style="color:#92400e;"
					>
						Windkraft heute
					</p>
				</div>
				{#if dataReady}
					<p class="text-sm leading-relaxed text-slate-700 mb-3">
						In den vergangenen Jahren hat Österreich seine Windenergie
						ausgebaut:
						<strong class="text-slate-900">{fmt(turbineCount)} Windräder</strong
						>
						sind bereits in Betrieb — verteilt auf alle Bundesländer.
					</p>
				{/if}

				<!-- Bundesland bars: existing-turbine count per state, scaled
					 against the state with the most turbines. -->
				<div class="space-y-1.5">
					{#each BUNDESLAENDER as bl}
						{@const count = turbinesByBL[bl.name] ?? 0}
						{@const pct = (count / maxTurbinesByBL) * 100}
						<div class="flex items-center gap-2">
							<span class="w-6 text-[9px] text-slate-500 text-right shrink-0"
								>{bl.short}</span
							>
							<div class="flex-1 h-3 rounded-sm overflow-hidden">
								<div
									class="h-full rounded-sm transition-all duration-300"
									style="width:{pct}%; background:#fde047;"
								></div>
							</div>
							{@render turbineIcon()}
							<span class="text-[9px] text-slate-500 w-6 shrink-0 text-right"
								>{count}</span
							>
						</div>
					{/each}
				</div>

				<!-- Legend -->
				<div class="flex items-center gap-1.5 mt-3 text-[9px] text-slate-500">
					{@render turbineIcon()}
					Bestehende Windräder je Bundesland
				</div>
			{/snippet}
			{@render slidePanel(step7)}
		{/if}

		<!-- Step 8: CTA + Windkraft-Ausbau bis 2040 -->
		{#if step === 8}
			{#snippet step8()}
				<div class="text-3xl mb-3">💨</div>
				<h2
					class="text-xl font-extrabold tracking-tight mb-2"
					style="color:#0f172a;"
				>
					Erkunde die Windpotentiale
				</h2>
				{#if dataReady}
					<p class="text-sm leading-relaxed text-slate-700 mb-3 text-left">
						Die bestehenden Windräder produzieren bereits rund
						<strong class="text-slate-900">{fmt(turbineGWh)}&thinsp;GWh</strong>
						Strom pro Jahr. Für die Energiewende und den völligen Umstieg von
						fossiler auf erneuerbare Energie braucht es deutlich mehr.
					</p>
					<div class="text-left mb-5">
						<RenewableGoalsChart />
					</div>
				{/if}
				<p class="text-sm text-slate-500 leading-relaxed mb-6">
					Suche nach deiner Gemeinde oder deinem Bezirk und finde heraus, wie
					groß das Windpotenzial in deiner Region ist.
				</p>
				<button
					onclick={complete}
					class="w-full py-3 px-6 rounded-xl font-semibold text-white text-sm hover:opacity-90 transition-opacity"
					style="background:#1d4ed8;"
				>
					Direkt zur interaktiven Karte →
				</button>
			{/snippet}
			{@render slidePanel(step8, "center", "max-w-sm", "p-8 text-center")}
		{/if}

		<!-- ── Bottom nav: pagination dots + skip link ── -->
		<div
			class="absolute bottom-12 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 pointer-events-auto"
		>
			<div class="flex gap-2">
				{#each Array(NUM_STEPS) as _, i (i)}
					<button
						class="rounded-full transition-all duration-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-400"
						style="width:{step === i
							? '20px'
							: '7px'}; height:7px; background:{step === i
							? '#1d4ed8'
							: 'rgba(0,0,0,0.2)'};"
						onclick={() => scrollTo(i)}
						onwheel={(e) => scrollEl?.scrollBy({ top: e.deltaY })}
						aria-label="Zu Schritt {i + 1}"
						aria-current={step === i ? "step" : undefined}
					></button>
				{/each}
			</div>
			{#if step >= 1 && step < NUM_STEPS - 1}
				<button
					onclick={complete}
					class="text-xs text-slate-500 hover:text-slate-800 transition-colors px-3 py-1 rounded-lg"
					style="background:rgba(255,255,255,0.85); backdrop-filter:blur(4px);"
					onwheel={(e) => scrollEl?.scrollBy({ top: e.deltaY })}
				>
					Direkt zur interaktiven Karte →
				</button>
			{/if}
		</div>
	</div>
	<!-- /visual layers -->
</div>
