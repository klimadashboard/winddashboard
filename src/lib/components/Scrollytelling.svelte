<script lang="ts">
	import { onMount } from "svelte";
	import { fly, fade, slide } from "svelte/transition";
	import type { Snippet } from "svelte";
	import { storyStep } from "$lib/stores/windStore";
	import RenewableGoalsChart from "./RenewableGoalsChart.svelte";
	import { AUSTRIA_HA } from "$lib/config/austria";
	import { loadRegionStats, type RegionStatsTable } from "$lib/data/regionStats";
	import { fmtNumber } from "$lib/format";

	// Erste Stelle der Gemeindekennziffer = Bundesland.
	const BUNDESLAND_BY_GKZ: Record<string, string> = {
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

	let { onComplete }: { onComplete: () => void } = $props();

	// ── State ─────────────────────────────────────────────────────────────────
	let scrollEl = $state<HTMLDivElement | null>(null);
	let step = $state(0);
	/**
	 * Unter `sm` führen ausschließlich die Knöpfe durch die Geschichte, der
	 * Scroll-Spacer ist dort abgeschaltet.
	 *
	 * Vorher lagen zwei Gesten übereinander: die Karte füllt den Bildschirm und
	 * will verschoben werden, gleichzeitig blätterte jede vertikale Wischbewegung
	 * die Geschichte weiter. Wer die Karte ansehen wollte, sprang ungewollt einen
	 * Schritt vor. Die Knöpfe gab es schon, sie waren nur nicht die einzige Art
	 * weiterzukommen. Am Schreibtisch bleibt Scrollen, dort gibt es keine
	 * konkurrierende Geste.
	 *
	 * 640 px ist Tailwinds `sm` — derselbe Wert, an dem die Knöpfe sichtbar und
	 * die Punkte unsichtbar werden.
	 */
	let buttonNav = $state(false);
	// Textkarte eingeklappt, um die ganze Karte zu sehen (slidePanel). Gilt nur
	// für den aktuellen Schritt: jeder Schrittwechsel klappt wieder auf.
	let panelCollapsed = $state(false);
	$effect(() => {
		step;
		panelCollapsed = false;
	});
	let exiting = $state(false);
	let dataReady = $state(false);

	// ── Live stats (fetched) ──────────────────────────────────────────────────
	let officialAreaHa = $state(0);
	let turbineCount = $state(0);
	// Jüngste gemessene Jahresproduktion (Energy-Charts), gemeldet vom Diagramm —
	// siehe `onLatest` in RenewableGoalsChart.svelte. Ersetzt die frühere
	// Hochrechnung aus der Nennleistung: sie stand in GWh über einem Diagramm in
	// TWh und lag zugleich rund 50 % über dem gemessenen Wert.
	let productionTwh = $state<number | null>(null);
	let productionYear = $state<number | null>(null);
	let zoningByBL = $state<Record<string, number>>({});
	let turbinesByBL = $state<Record<string, number>>({});
	// Band 38: Park-Hüllen um die bestehenden Anlagen außerhalb der amtlichen
	// Zonen. Ohne diese Zahlen liest sich der Zonierungsschritt für das
	// Burgenland falsch — dort sind 2.470 ha zoniert, aber 397 der 423
	// Anlagen stehen in den gut 11.300 ha daneben.
	// Gesamtfläche und Anlagenzahl der Hüllen standen bis 17.11.2026 im Kasten
	// „Bestehende Windparks“; der Text ist auf Wunsch der Redaktion gekürzt.
	let hullByBL = $state<Record<string, number>>({});

	// Potentialflächen step: absolute (ha, compared across states) vs. percent
	// of each state's own area. Absolute is the default — the % view is an
	// opt-in toggle, not the default.
	let potentialViewMode = $state<"absolute" | "percent">("absolute");

	// ── Konstanten aus dem Klassifikationsraster ──────────────────────────────
	// Stand abschichtung.tif, Schema clean-44-ohne-lsg-okt-2026,
	// erzeugt von scripts/create_classification_from_simplified.py. Nach jedem
	// neuen Rasterlauf hier aktualisieren — siehe PIPELINE.md §6.
	//
	// Code 9 (Wichtige Objekte) ist entfallen, 15 (Nicht-Wohn-Hüllen) und 16
	// (Gewässer) kamen mit widmung_v2 dazu. Code 10 (Freileitung) war in
	// widmung_v2 leer und ist seit clean-45 wieder belegt — jetzt ab 110 kV
	// statt erst ab 380 kV. Alle drei zählen zu "Sonstige".
	//
	// clean-44-ohne-lsg verschiebt die Naturzahl deutlich: Landschaftsschutz-
	// gebiete sind kein Ausschlusskriterium mehr und die OSM-Schutzgebiete sind
	// ganz entfallen, dafür zählen jetzt auch geschützte Landschaftsteile,
	// Naturdenkmäler, Biotope und Ruhegebiete des Umweltbundesamts mit. Netto
	// −92.620 ha bei Code 1. Weil die Klassifikation nach Priorität zuweist,
	// landen diese Flächen überwiegend in "Sonstige" (+78.762 ha), nicht im
	// Potenzial — das wächst nur um 8.209 ha.
	const SCHUTZ_HA = 915_085; // code 1
	const SIEDLUNG_HA = 4_569_390; // code 2
	const SONSTIGE_HA = 2_429_613; // codes 3–8, 10, 12, 13, 15, 16
	const WIND_HA = 41_399; // code 11, Wind zu gering
	const POTENTIAL_HA = 365_978; // code 14, raster-based

	// Vector-derived potential (used in the "final" headline)
	const POTENTIAL_VECTOR_HA = 365_949;

	// Colors for the persistent header bar — fixed left-to-right stacking
	// order: each category's segment appears once its step is reached and
	// stays for the rest of the story.
	const COLOR_SIEDLUNG = "#fb923c";
	const COLOR_SCHUTZ = "#4ade80";
	const COLOR_SONSTIGE = "#94a3b8";
	const COLOR_WIND = "#db2777";
	const COLOR_POTENTIAL = "#2563eb";
	const COLOR_ZONIERT = "#6d28d9";
	const COLOR_BESTAND_FLAECHE = "#0891b2";
	// Bestehende Anlagen: dieselbe dunkle Farbe wie die Punkte auf der Karte
	// (Map.svelte, Layer "turbines"). Bis 17.11.2026 gelb.
	const COLOR_TURBINE = "#1e293b";
	const COLOR_TURBINE_BAR = "#475569";

	// Each Bundesland's own total area in hectares — derived from the same
	// classification raster as AUSTRIA_HA (rasterized per state; see
	// scripts/compute_bundesland_areas.py), so the "% of own area" view stays
	// internally consistent with the rest of the pipeline. Cross-checked
	// against Statistik Austria ("Fläche und Benützungsarten", Stand 1.1.2025,
	// Bundesamt für Eich- und Vermessungswesen): every state is within ~1.2% of
	// the official figure (raster slightly undercounts everywhere) — no state
	// is an outlier.
	//
	// Der Fehlbetrag kommt nicht nur von Randpixeln: die Klassifikation weist
	// nach Priorität zu, und eine Zelle, auf die keine Regel passt, bleibt
	// Code 0. Verfügbare Splitter unter 10 ha fallen so aus der Zählung. Mit
	// clean-44-ohne-lsg sind das rund 19.000 ha mehr als zuvor, weil Flächen,
	// die nur wegen der OSM-Schutzgebiete ausgeschlossen waren, jetzt als
	// Splitter übrig bleiben. Für die Prozentbalken unkritisch — als
	// Flächenangabe für Dritte taugen diese Zahlen nicht.
	const BUNDESLAND_HA: Record<string, number> = {
		"Niederösterreich": 1_912_101,
		"Steiermark": 1_622_717,
		"Tirol": 1_249_113,
		"Oberösterreich": 1_192_281,
		"Kärnten": 945_832,
		"Salzburg": 706_233,
		"Burgenland": 395_084,
		"Vorarlberg": 256_866,
		"Wien": 41_445,
	};

	// ── Bundesland breakdown (vector data, sorted by potential area) ─────────
	// Stand clean-44-ohne-lsg (abschichtung.tif, 21.10.2026) — aus geodata/zone_stats.json.
	const BUNDESLAENDER = [
		{ name: "Niederösterreich", short: "NÖ", ha: 141_089 },
		{ name: "Burgenland", short: "B", ha: 69_439 },
		{ name: "Steiermark", short: "ST", ha: 47_409 },
		{ name: "Oberösterreich", short: "OÖ", ha: 37_167 },
		{ name: "Kärnten", short: "K", ha: 27_132 },
		{ name: "Salzburg", short: "S", ha: 19_605 },
		{ name: "Tirol", short: "T", ha: 18_840 },
		{ name: "Vorarlberg", short: "V", ha: 4_917 },
		{ name: "Wien", short: "W", ha: 253 },
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

	// Windräder stehen nicht in allen 9 Bundesländern — Salzburg, Tirol und
	// Vorarlberg haben aktuell keine. Zahl aus den Daten statt hartcodiert.
	const bundeslaenderMitWind = $derived(
		Object.values(turbinesByBL).filter((n) => n > 0).length,
	);

	function fmt(n: number, d = 0) {
		return fmtNumber(n, d);
	}

	// Anlagen je Bundesland — aus der vorberechneten Gemeindetabelle, deren
	// Zuordnung geometrisch gegen die amtlichen Gemeindegrenzen erfolgt ist.
	// Der frühere Weg über BEZIRK_TO_BUNDESLAND verlor die 51 Anlagen ohne
	// `bezirk`-Attribut, wodurch die Balken hier nicht zu den Zahlen auf den
	// Gemeindeseiten passten (NÖ 794 statt 801, Steiermark 112 statt 116).
	//
	// Seit die Standorte nur noch als Vektorkacheln kommen, gibt es gar keinen
	// Rückfall mehr: die Punktdatei liegt nicht mehr im Build. Lädt die Tabelle
	// nicht, bleiben die Balken leer — besser als falsche Zahlen.
	async function turbinesPerBundesland(
		table: RegionStatsTable | null,
	): Promise<Record<string, number>> {
		const out: Record<string, number> = {};
		if (!table) return out;
		for (const [gkz, entry] of Object.entries(table.regions)) {
			const bl = BUNDESLAND_BY_GKZ[gkz[0]];
			if (bl) out[bl] = (out[bl] ?? 0) + entry.turbines;
		}
		return out;
	}

	// ── Data loading ──────────────────────────────────────────────────────────
	async function loadData() {
		const [offGj, hullGj, statsTable] = await Promise.all([
			fetch("/data/official_zoning.json").then((r) => r.json()),
			fetch("/data/wka_bestand_ausserhalb_zonen.json").then((r) => r.json()),
			loadRegionStats(),
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

		const hullBL: Record<string, number> = {};
		for (const f of hullGj.features) {
			const bl: string = f.properties.bundesland ?? "";
			hullBL[bl] = (hullBL[bl] ?? 0) + (f.properties.area_ha ?? 0);
		}
		hullByBL = hullBL;

		// Gesamtzahl aus der Tabelle, nicht aus den Punkten: eine Kachelquelle
		// lässt sich nicht zählen. `turbineTotal` enthält auch die Anlagen ohne
		// Gemeindezuordnung, die Summe über `regions` nicht — deshalb nicht
		// einfach aufaddieren.
		turbineCount =
			statsTable?.turbineTotal ??
			Object.values(statsTable?.regions ?? {}).reduce((s, e) => s + e.turbines, 0);
		turbinesByBL = await turbinesPerBundesland(statsTable);
		dataReady = true;
	}

	function complete() {
		exiting = true;
		storyStep.set(-1);
		setTimeout(onComplete, 600);
	}

	/**
	 * Der einzige Weg, den Schritt zu wechseln — von Knöpfen, Punkten und
	 * Tastatur aus. Ohne Scroll-Navigation gibt es keinen Spacer, an dem sich
	 * `step` ablesen ließe, also wird er direkt gesetzt.
	 */
	function goTo(s: number) {
		const target = Math.max(0, Math.min(s, NUM_STEPS - 1));
		if (buttonNav) {
			if (target !== step) {
				step = target;
				storyStep.set(target);
			}
			return;
		}
		scrollEl?.scrollTo({ top: target * window.innerHeight, behavior: "smooth" });
	}

	function handleScroll() {
		if (buttonNav) return;
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
				goTo(Math.min(step + 1, NUM_STEPS - 1));
				break;
			case "ArrowUp":
			case "ArrowLeft":
			case "PageUp":
				e.preventDefault();
				goTo(Math.max(step - 1, 0));
				break;
			case "Home":
				e.preventDefault();
				goTo(0);
				break;
			case "End":
				e.preventDefault();
				goTo(NUM_STEPS - 1);
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

		// matchMedia statt eines resize-Listeners mit Breitenvergleich: der
		// Browser meldet nur den Wechsel über die Grenze, nicht jedes Pixel.
		const mq = window.matchMedia("(max-width: 639px)");
		const sync = () => {
			buttonNav = mq.matches;
			// Zurück am Schreibtisch: der Spacer steht noch dort, wo er beim
			// letzten Scrollen stand. Ohne Nachführen würde die nächste
			// Scrollbewegung zum zuletzt gescrollten Schritt zurückspringen.
			if (!buttonNav && scrollEl) {
				scrollEl.scrollTop = step * window.innerHeight;
			}
		};
		sync();
		mq.addEventListener("change", sync);

		// Dokument feststellen, solange die Geschichte den Bildschirm ausfüllt.
		// Bisher fing der Scroll-Spacer jede Wischbewegung ab; ohne ihn würde auf
		// dem Telefon stattdessen die Seite hinter dem Vollbild wegscrollen — der
		// Nutzer sieht nichts davon und findet die Seite nach dem Schließen an
		// einer anderen Stelle wieder.
		const prevOverflow = document.body.style.overflow;
		document.body.style.overflow = "hidden";

		return () => {
			mq.removeEventListener("change", sync);
			document.body.style.overflow = prevOverflow;
		};
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
		style="overflow-y:{buttonNav ? 'hidden' : 'scroll'}; z-index:0;"
	>
		<div style="height:{buttonNav ? 100 : NUM_STEPS * 100}vh;"></div>
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
			<!--
				Beschriftung, solange der Balken noch leer ist: ohne sie ist nicht
				erkennbar, dass er die Gesamtfläche Österreichs darstellt und sich
				Schritt für Schritt mit den Ausschlussgründen füllt.
			-->
			{#if step === 0}
				<p class="text-[10px] text-slate-400 mb-1.5">
					Die Gesamtfläche Österreichs — sie füllt sich Schritt für Schritt mit
					den Flächen, auf denen kein Windrad stehen kann.
				</p>
			{/if}
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
			<!--
				pb-48 hält unten Platz für den gesamten Navigationsblock frei —
				Schritt-Knöpfe, Zähler und Sprunglink zusammen. Ohne das lag er auf
				kurzen Telefonen mitten im Diagramm: beim Zonierungsschritt
				verdeckten Punkte und Sprunglink die Balken von Kärnten abwärts.

				max-h + overflow-y-auto statt overflow-hidden auf der Hülle: der
				längste Schritt braucht 697 px, ein iPhone SE bietet 667. Vorher
				wurde der Rest wortlos abgeschnitten und war nicht erreichbar.
			-->
			<div
				class="absolute inset-0 flex flex-col pb-48 sm:pb-4
					{align === 'center'
					? 'p-4 items-center justify-start sm:justify-center'
					: 'pt-[8%] pl-4 pr-16 sm:pr-4 items-start justify-start'}"
				transition:fade={{ duration: 300 }}
			>
				<!--
					Einklappen: die Textkarte deckt am Schreibtisch Vorarlberg und
					Nordtirol ab, auf dem Telefon ein gutes Stück der Karte. Nur bei
					den linken Karten (Schritte 1–7) — Titel und Schluss sind
					zentriert und haben keine Karte dahinter, die man sehen müsste.
					Beim Schrittwechsel klappt die Karte wieder auf (siehe $effect),
					sonst stünde man ohne Text im nächsten Schritt.
				-->
				{#if align === "left" && panelCollapsed}
					<button
						class="pointer-events-auto flex items-center gap-2 rounded-md bg-white/95 backdrop-blur-sm shadow-lg
							px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-white transition-colors
							focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-400"
						onclick={() => (panelCollapsed = false)}
						aria-expanded="false"
						in:fade={{ duration: 150 }}
					>
						<svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5" aria-hidden="true">
							<path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
						</svg>
						Text einblenden
					</button>
				{:else}
					<div
						class="relative bg-white/95 backdrop-blur-sm rounded-md w-full {maxWidth} shadow-lg pointer-events-auto
							max-h-full overflow-y-auto overscroll-contain"
						in:fly={{ y: 20, duration: 400, delay: 80 }}
						onwheel={(e) => scrollEl?.scrollBy({ top: e.deltaY })}
					>
						{#if align === "left"}
							<button
								class="absolute top-2 right-2 flex items-center justify-center w-7 h-7 rounded-md
									text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors
									focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-400"
								onclick={() => (panelCollapsed = true)}
								aria-expanded="true"
								aria-label="Text einklappen, um die ganze Karte zu sehen"
								title="Text einklappen"
							>
								<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5" aria-hidden="true">
									<path stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7" />
								</svg>
							</button>
						{/if}
						<div class={padding}>
							{@render inner()}
							<div class="mt-4">
								{@render revealBarHeader()}
							</div>
						</div>
					</div>
				{/if}
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
					Wo der Wind weht: Windpotenziale in Österreich
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
						onclick={() => goTo(1)}
						onwheel={(e) => scrollEl?.scrollBy({ top: e.deltaY })}
					>
						<!--
							Auf dem Telefon führt kein Scrollen mehr durch die Geschichte,
							also darf der Knopf auch nicht dazu auffordern. Das Mausrad-
							Symbol entfällt dort aus demselben Grund.
						-->
						{buttonNav ? "Los geht's" : "Scrolle, um mehr zu erfahren"}
						<svg
							class="w-4 h-5 {buttonNav ? 'hidden' : ''}"
							viewBox="0 0 16 24"
							fill="none"
						>
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
				<p class="text-sm sm:text-base leading-relaxed text-slate-700 mb-3">
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
				<p class="text-sm sm:text-base leading-relaxed text-slate-700 mb-3">
					Weitere <strong class="text-slate-900"
						>{fmt(SCHUTZ_HA)}&thinsp;ha</strong
					> entfallen auf Schutzgebiete — Nationalparks, Naturschutzgebiete,
					Europaschutzgebiete (Natura 2000), Geschützte Landschaftsteile,
					Sonstige Schutzgebiete (nur verordnete Kategorien) und Naturdenkmäler.
					Landschaftsschutzgebiete zählen nicht dazu.
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
				<p class="text-sm sm:text-base leading-relaxed text-slate-700 mb-3">
					Bestehende Infrastruktur (Straßen, Bahnen, Gebäude,
					Hochspannungsleitungen) sowie ungeeignetes Gelände (Hangneigung,
					Seehöhe, Gewässer) schließen weitere
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
				<p class="text-sm sm:text-base leading-relaxed text-slate-700 mb-3">
					Auf Basis des Global Wind Atlas wurden Standorte mit zu geringem
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
					<!--
						Erst ab Schritt 5: vorher gibt es das Windpotenzial weder auf der
						Karte noch im Balken. Eine Legende, die eine Kategorie nennt, die
						nirgends zu sehen ist, lässt Leute danach suchen.
					-->
					{#if step >= 5}
						<div class="flex items-center gap-1.5">
							<span
								class="w-2 h-2 rounded-sm"
								style="background:{COLOR_POTENTIAL};"
							></span>Windpotenzial
						</div>
					{/if}
				</div>
			{/snippet}
			{@render slidePanel(step4)}
		{/if}

		<!-- Step 5: Potenzialflächen nach Bundesland -->
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
						Potenzialflächen
					</p>
				</div>
				<p class="text-sm sm:text-base leading-relaxed text-slate-700 mb-3">
					Somit bleiben <strong class="text-slate-900"
						>~{fmt(POTENTIAL_VECTOR_HA)}&thinsp;ha</strong
					>
					in ganz Österreich als Potenzialflächen für Windkraft übrig — verteilt
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
				<!--
					Gekürzt, nicht gestrichen: der Satz "Folgende Bundesländer haben
					aktuell Windkraft-Eignungszonen ausgewiesen" wiederholte den
					ersten Satz wörtlich. Auf dem Telefon zählt jede Zeile — dieser
					Schritt ist der längste der Geschichte und hat mit den
					Bestandsflächen einen zweiten Flächentyp bekommen.
				-->
				<p class="text-sm sm:text-base leading-relaxed text-slate-700 mb-4">
					Fünf Bundesländer haben eigene Windkraftzonen ausgewiesen:
					Niederösterreich, Burgenland, Steiermark, Kärnten und Salzburg.
					Diese „Zonierungsflächen“ siehst du hier{#if dataReady}&nbsp;—
						aktuell <strong class="text-slate-900"
							>{fmt(Math.round(officialAreaHa))}&thinsp;ha</strong
						>{/if}. In Tirol, Vorarlberg und Wien gibt es keine; in
					Oberösterreich wird aktuell an einer Zonierung gearbeitet.
				</p>
				<!--
					Hier stand bis 17.11.2026 eine Datenstand-Zeile je Bundesland. Auf
					Wunsch der Redaktion entfallen: die Quellen und Stände der Zonierungen
					stehen in der Methodik. Der Satz zur Berechnung der Windpark-Hüllen
					steht jetzt im türkisen Kasten, zu dem er gehört.
				-->
				<!--
					Der zweite Flächentyp im selben Schritt. Ohne ihn war die Karte im
					Burgenland irreführend: dort sind rund 2.470 ha zoniert, aber 397
					der 423 Anlagen stehen außerhalb dieser Zonen. Wer nur die
					violetten Flächen sah, musste schließen, dass im Burgenland kaum
					Windkraft-Flächen existieren.

					Der Grund ist aber nicht, dass dort außerhalb der Zonen gebaut
					wurde: uns liegen für das Burgenland nur die *aktuellen*
					Eignungszonen vor, nicht die früheren, in denen diese Anlagen
					stehen. Der Text sagt das seit der Durchsicht vom 11.11.2026
					ausdrücklich — vorher las er sich wie ein Regelverstoß.
				-->
				<div
					class="rounded-lg px-3 py-2.5 mb-3"
					style="background:#ecfeff; border:1px solid #a5f3fc;"
				>
					<div class="flex items-center gap-2 mb-1.5">
						<span
							class="inline-block w-3 h-3 rounded-sm shrink-0"
							style="background:{COLOR_BESTAND_FLAECHE}; opacity:0.75; border:1px solid #0e7490;"
						></span>
						<p
							class="text-[10px] font-bold uppercase tracking-widest"
							style="color:#155e75;"
						>
							Bestehende Windparks
						</p>
					</div>
					<p class="text-xs sm:text-sm leading-relaxed text-slate-700">
						Manche Windräder liegen außerhalb der auf der Karte ersichtlichen
						Zonen der Bundesländer. Das kann daran liegen, dass sie vor der
						Zonierung gebaut wurden oder ihre Zone nicht mehr öffentlich
						zugänglich ist wie im Burgenland. Das Burgenland stellt nur die noch
						unbebauten Zonen öffentlich zur Verfügung, nicht die bereits
						bebauten. Deshalb wurden bestehende Windparks türkis umrandet. Diese
						Fläche haben wir berechnet (Windräder unter 750&thinsp;m Abstand plus
						200&thinsp;m Rand), sie ist kein amtlicher Plan.
					</p>
				</div>

				<!-- Bundesland bars: potential (light blue) + zoned (purple) overlay,
					 both as absolute ha scaled against the largest state (NÖ) — same
					 scale as step 5's "Absolut" view, no track background since
					 there's no 100%-of-something reference being shown. -->
				<div class="space-y-1.5">
					{#each BUNDESLAENDER as bl}
						{@const potPct = (bl.ha / BUNDESLAENDER[0].ha) * 100}
						{@const zonedHa = zoningByBL[bl.name] ?? 0}
						{@const zonedPct = (zonedHa / BUNDESLAENDER[0].ha) * 100}
						{@const hullHa = hullByBL[bl.name] ?? 0}
						{@const hullPct = (hullHa / BUNDESLAENDER[0].ha) * 100}
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
								<!--
									Hinter der zonierten Fläche angesetzt, nicht darüber: die
									beiden Flächentypen überschneiden sich geometrisch nicht
									(der Datenanbieter zieht die amtlichen Zonen von den
									Hüllen ab), deshalb ist die Aneinanderreihung korrekt und
									die Gesamtlänge die Summe beider.
								-->
								{#if hullHa > 0}
									<div
										class="absolute inset-y-0 rounded-sm"
										style="left:{zonedPct}%; width:{hullPct}%; background:{COLOR_BESTAND_FLAECHE}; opacity:0.8;"
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
					<div class="flex items-center gap-1">
						<span
							class="w-2.5 h-2.5 rounded-sm"
							style="background:{COLOR_BESTAND_FLAECHE}; opacity:0.8;"
						></span>
						Bestehende Parks (ha)
					</div>
				</div>
			{/snippet}
			{@render slidePanel(step6)}
		{/if}

		<!-- Step 7: Windräder heute (Bestand nach Bundesland) -->
		{#if step === 7}
			{#snippet turbineIcon()}
				<!--
					Windrad-Icon aus der Vorlage windpowerplant.svg (Redaktion, 17.11.2026).
					Die Vorlage ist eine Umrisszeichnung: eine Außenkontur plus fünf
					Innenkonturen (drei Blätter, Nabe, Turm), die zusammen wie Striche
					wirken. Hier steht nur die Außenkontur — damit ist die Anlage als
					gefüllte Silhouette gezeichnet.
				-->
				<svg viewBox="0 0 71 90" width="10" height="13" class="shrink-0" aria-hidden="true">
					<path fill={COLOR_TURBINE} d="M69.867 52.743L66.289 49.925C60.035 45.006 53.072 41.096 45.597 38.299L41.264 36.674C40.944 35.795 40.453 34.999 39.802 34.352L40.163 29.766C40.782 21.779 40.178 13.816 38.368 6.097L37.325 1.662C37.221 1.209 36.98 0.795 36.635 0.487C36.274 0.173 35.82 0 35.361 0C34.432 0 33.625 0.685 33.396 1.659L32.354 6.1C30.541 13.825 29.936 21.788 30.559 29.766L30.916 34.355C30.269 35.002 29.778 35.795 29.458 36.674L25.128 38.299C17.652 41.093 10.689 45.003 4.435 49.925L0.854 52.74C0.312 53.166 0 53.78 0 54.425C0 54.708 0.0619996 54.98 0.176 55.22C0.5 55.926 1.231 56.355 2.042 56.355C2.199 56.355 2.356 56.34 2.517 56.309L6.97 55.377C14.747 53.755 22.22 50.937 29.186 46.998L32.106 45.349L29.818 89.171C29.809 89.387 29.886 89.596 30.034 89.753C30.186 89.91 30.392 90 30.609 90H40.113C40.329 90 40.536 89.91 40.687 89.753C40.834 89.596 40.912 89.387 40.903 89.171L38.614 45.346L41.538 46.998C48.498 50.934 55.971 53.752 63.748 55.377L68.208 56.309C68.371 56.343 68.528 56.359 68.683 56.359C69.509 56.359 70.222 55.923 70.539 55.23C70.939 54.388 70.662 53.363 69.867 52.743Z" />
				</svg>
			{/snippet}
			{#snippet step7()}
				<div class="flex items-center gap-2 mb-3">
					<span
						class="inline-block w-3 h-3 rounded-full border-2 shrink-0"
						style="background:{COLOR_TURBINE}; border-color:#ffffff; box-shadow:0 0 0 1px #cbd5e1;"
					></span>
					<p
						class="text-[10px] font-bold uppercase tracking-widest"
						style="color:{COLOR_TURBINE};"
					>
						Windkraft heute
					</p>
				</div>
				{#if dataReady}
					<p class="text-sm sm:text-base leading-relaxed text-slate-700 mb-3">
						In den vergangenen Jahren hat Österreich seine Windenergie
						ausgebaut:
						<strong class="text-slate-900">{fmt(turbineCount)} Windräder</strong
						>
						sind bereits in Betrieb — verteilt auf aktuell {bundeslaenderMitWind}
						Bundesländer.
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
									style="width:{pct}%; background:{COLOR_TURBINE_BAR};"
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
					Erkunde die Windpotenziale
				</h2>
				{#if dataReady}
					<p class="text-sm sm:text-base leading-relaxed text-slate-700 mb-3 text-left">
						{#if productionTwh !== null}
							Österreichs Windräder haben zuletzt rund
							<strong class="text-slate-900"
								>{fmtNumber(productionTwh, 1)}&thinsp;TWh</strong
							>
							Strom pro Jahr erzeugt ({productionYear}).
						{:else}
							Österreichs Windräder erzeugen schon heute einen erheblichen Teil
							des Stroms.
						{/if}
						Für die Energiewende und den völligen Umstieg von fossiler auf
						erneuerbare Energie braucht es deutlich mehr.
					</p>
					<div class="text-left mb-5">
						<RenewableGoalsChart
							onLatest={(d) => {
								productionTwh = d.twh;
								productionYear = d.year;
							}}
						/>
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

		<!--
			Bottom nav: Schritt-Knöpfe, Punkte und Sprunglink.

			Auf dem Telefon führt reines Scrollen durch die Story schlecht: Die
			Karte liegt im Vollbild, jede Wischbewegung konkurriert mit dem
			Verschieben der Karte, und wie weit man wischen muss, ist nicht
			absehbar. Deshalb gibt es unter `sm` zwei ausdrückliche Knöpfe. Am
			Schreibtisch bleibt es beim Scrollen, dort funktioniert es.
		-->
		<div
			class="absolute bottom-20 sm:bottom-12 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 pointer-events-auto"
		>
			<div class="flex sm:hidden items-center gap-3 mb-1">
				<button
					onclick={() => goTo(Math.max(step - 1, 0))}
					disabled={step === 0}
					class="flex items-center justify-center rounded-full transition-opacity disabled:opacity-30 shadow-md"
					style="width:44px; height:44px; background:rgba(255,255,255,0.95); backdrop-filter:blur(4px);"
					aria-label="Vorheriger Schritt"
				>
					<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="#1d4ed8" stroke-width="2.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
					</svg>
				</button>
				<span class="text-xs font-semibold tabular-nums" style="color:#1d4ed8;">
					{step + 1} / {NUM_STEPS}
				</span>
				<button
					onclick={() =>
						step === NUM_STEPS - 1 ? complete() : goTo(Math.min(step + 1, NUM_STEPS - 1))}
					class="flex items-center justify-center rounded-full transition-opacity shadow-md"
					style="width:44px; height:44px; background:#1d4ed8;"
					aria-label={step === NUM_STEPS - 1 ? "Zur Karte" : "Nächster Schritt"}
				>
					<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="#ffffff" stroke-width="2.5">
						<path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
					</svg>
				</button>
			</div>
			<div class="hidden sm:flex gap-2">
				{#each Array(NUM_STEPS) as _, i (i)}
					<button
						class="rounded-full transition-all duration-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-400"
						style="width:{step === i
							? '20px'
							: '7px'}; height:7px; background:{step === i
							? '#1d4ed8'
							: 'rgba(0,0,0,0.2)'};"
						onclick={() => goTo(i)}
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
