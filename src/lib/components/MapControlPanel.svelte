<script lang="ts">
	import { onMount } from "svelte";
	import {
		expertMode,
		vizMode,
		hiddenBands,
		hiddenVectorLayers,
		emptyBands,
		settlementVariant,
		zoneStats,
	} from "$lib/stores/windStore";
	import type { VizMode, VectorLayerKey } from "$lib/stores/windStore";
	import { LEGEND_CODES, GROUP_LABELS } from "$lib/config/legend";
	import { BAND_DEFS, BAND_GROUPS, GROUP_ORDER, SETTLEMENT_VARIANTS } from "$lib/config/bands";
	import { AUSTRIA_HA } from "$lib/config/austria";
	import { fmtNumber as fmt } from "$lib/format";
	import type { BandGroup } from "$lib/config/bands";

	const vizOptions: { value: VizMode; label: string }[] = [
		{ value: "zones", label: "Potenzialzonen" },
		{ value: "heatmap", label: "Heatmap" },
		{ value: "hexbin", label: "Hexbin 3D" },
		{ value: "dots", label: "Windgitter" },
	];

	const groups = ["suitable", "exclusion", "terrain", "wind"] as const;
	type Group = (typeof groups)[number];

	function hexToRgba(hex: string): string {
		const r = parseInt(hex.slice(1, 3), 16);
		const g = parseInt(hex.slice(3, 5), 16);
		const b = parseInt(hex.slice(5, 7), 16);
		const a = hex.length >= 9 ? parseInt(hex.slice(7, 9), 16) / 255 : 1;
		return `rgba(${r},${g},${b},${a.toFixed(2)})`;
	}

	function codesForGroup(group: Group) {
		return LEGEND_CODES.filter((c) => c.group === group);
	}

	function bandsForGroup(group: BandGroup) {
		return BAND_DEFS.filter((d) => d.group === group);
	}
	function isGroupAllHidden(group: BandGroup) {
		return bandsForGroup(group).every((d) => $hiddenBands.has(d.band));
	}
	function isGroupPartial(group: BandGroup) {
		const bands = bandsForGroup(group);
		const n = bands.filter((d) => $hiddenBands.has(d.band)).length;
		return n > 0 && n < bands.length;
	}
	function toggleGroup(group: BandGroup) {
		hiddenBands.update((s) => {
			const next = new Set(s);
			const bands = bandsForGroup(group);
			if (bands.every((d) => next.has(d.band))) {
				bands.forEach((d) => next.delete(d.band));
			} else {
				bands.forEach((d) => next.add(d.band));
			}
			return next;
		});
	}
	const VECTOR_ROWS: { key: VectorLayerKey; label: string; swatch: string; round?: boolean }[] = [
		{ key: "zones", label: "Windkraftzonen", swatch: "background:#7c3aed;border:1.5px dashed #6d28d9;" },
		{ key: "exclusion", label: "Ausschlusszonen (Stmk.)", swatch: "background:repeating-linear-gradient(-45deg, #475569 0 1.5px, transparent 1.5px 4px);border:1px solid #475569;" },
		{ key: "hulls", label: "Bestehende Windparks", swatch: "background:#0891b2;opacity:0.75;border:1px solid #0e7490;" },
		{ key: "turbines", label: "Bestehende Anlagen", swatch: "background:#1e293b;border:1.5px solid white;box-shadow:0 0 0 1px #cbd5e1;", round: true },
	];

	function toggleVector(key: VectorLayerKey) {
		hiddenVectorLayers.update((s) => {
			const next = new Set(s);
			if (next.has(key)) next.delete(key);
			else next.add(key);
			return next;
		});
	}

	function toggleBand(bandId: number) {
		hiddenBands.update((s) => {
			const next = new Set(s);
			if (next.has(bandId)) next.delete(bandId);
			else next.add(bandId);
			return next;
		});
	}
	function hexToRgbStr(hex: string) {
		const r = parseInt(hex.slice(1, 3), 16);
		const g = parseInt(hex.slice(3, 5), 16);
		const b = parseInt(hex.slice(5, 7), 16);
		const a =
			hex.length >= 9 ? (parseInt(hex.slice(7, 9), 16) / 255).toFixed(2) : "1";
		return `rgba(${r},${g},${b},${a})`;
	}

	// ── Siedlungsabstands-Varianten (Dropdown in der Detailansicht) ──
	// Namen und Beschreibung kommen aus dem Manifest; nur der Default heißt hier
	// „Gesetzliche Abstände“ statt „Länderregel“ (Entscheidung 19.11.2026).
	const VARIANT_TEXT: Record<string, { label: string; note: string }> = {
		default: { label: "Gesetzliche Abstände", note: "1,2 km in Niederösterreich und im Burgenland, sonst 1 km" },
		"1km": { label: "1 km überall", note: "1 km in ganz Österreich" },
		"1d2km": { label: "1,2 km überall", note: "1,2 km in ganz Österreich" },
	};
	function variantText(key: string) {
		const v = SETTLEMENT_VARIANTS.find((d) => d.key === key);
		return VARIANT_TEXT[key] ?? { label: v?.label ?? key, note: v?.description ?? "" };
	}
	// Immer eine Nachkommastelle („5,0 %“), sonst springt die Zeile beim Umschalten.
	const pct = (ha: number) => ((ha / AUSTRIA_HA) * 100).toFixed(1).replace(".", ",");
	const variantTotals = $derived.by(() => {
		const st = $zoneStats;
		if (!st) return null;
		return $settlementVariant === "default" ? st : (st.variants?.[$settlementVariant] ?? null);
	});

	// Closed by default; onMount opens on desktop
	let panelOpen = $state(false);
	onMount(() => {
		panelOpen = window.innerWidth >= 768;
	});
</script>

<div
	class="rounded-2xl flex flex-col text-xs overflow-hidden"
	style="background: white; border: 1px solid #e2e8f0; box-shadow: 0 2px 18px rgba(0,0,0,0.08); width: 188px;"
>
	<!-- ── Collapsed header (shown when closed) ── -->
	{#if !panelOpen}
		<button
			onclick={() => (panelOpen = true)}
			class="flex items-center gap-2 px-3 py-2.5 w-full text-left transition-colors hover:bg-slate-50"
		>
			<svg
				class="w-3.5 h-3.5 flex-shrink-0 opacity-40"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
				stroke-width="2"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
				/>
			</svg>
			<span class="flex-1 font-semibold" style="color: var(--text-dark);"
				>Legende</span
			>
			<svg
				class="w-3.5 h-3.5 flex-shrink-0 opacity-30"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
				stroke-width="2"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M19 9l-7 7-7-7"
				/>
			</svg>
		</button>
		<div class="border-t border-slate-100"></div>
	{/if}

	<!-- ── Legend content (shown when open) ── -->
	{#if panelOpen}
		{#if !$expertMode}
			<!-- Simple legend -->
			<div class="px-3 py-2.5 flex flex-col gap-2" style="color: #4b5563;">
				<span class="flex items-center gap-2">
					<span
						class="w-3 h-3 rounded-sm flex-shrink-0"
						style="background: #2563eb; opacity: 0.85;"
					></span>
					Windpotenzial
				</span>
				<!-- Divider between zone types and infrastructure -->
				<div class="border-t border-slate-100 -mx-3"></div>
				<span class="flex items-center gap-2">
					<span
						class="w-3 h-3 rounded-sm flex-shrink-0 inline-block"
						style="background: #7c3aed; border: 1.5px dashed #6d28d9;"
					></span>
					Offiz. Windkraftzone
				</span>
				<!--
					Die Ausschlusszonen (Steiermark) stehen nur in der Detail-Legende:
					auf der Karte erscheinen sie erst mit der Detailansicht.
				-->
				<!--
					Bestandsfläche statt "Eignungszone": die Fläche ist keine Ausweisung
					des Landes, sondern die Hülle um bestehende Anlagen. Sie steht
					unter der Eignungszone in der Legende, weil beide Flächen auf der
					Karte nebeneinander liegen und sonst verwechselt werden.
				-->
				<span class="flex items-center gap-2">
					<span
						class="w-3 h-3 rounded-sm flex-shrink-0 inline-block"
						style="background: #0891b2; opacity: 0.75; border: 1px solid #0e7490;"
					></span>
					Bestehender Windpark
				</span>
				<span class="flex items-center gap-2">
					<span
						class="w-3 h-3 rounded-full flex-shrink-0 inline-block"
						style="background: #1e293b; border: 1.5px solid white; box-shadow: 0 0 0 1px #cbd5e1;"
					></span>
					Bestehende Anlage
				</span>
			</div>
		{:else}
			<!-- Expert legend: grouped toggleable bands -->
			<div
				class="overflow-y-auto px-3 pt-3 pb-4 space-y-3"
				style="max-height: calc(50vh - 80px);"
			>
				<!--
					Siedlungsabstand als Variante: tauscht in der Karte die
					Potenzialflächen und die Ebene „Siedlungsabstand“. Story, Texte
					und Gemeindezahlen rechnen immer mit den gesetzlichen Abständen.
				-->
				{#if SETTLEMENT_VARIANTS.length > 1}
					<div>
						<label
							for="settlement-variant"
							class="block font-bold uppercase mb-1.5"
							style="font-size:9px;letter-spacing:0.12em;color:var(--blue-sky);"
						>
							Siedlungsabstand
						</label>
						<select
							id="settlement-variant"
							class="w-full rounded-md border border-slate-200 bg-white px-1.5 py-1 cursor-pointer"
							style="font-size:11px;color:#1f2937;"
							bind:value={$settlementVariant}
						>
							{#each SETTLEMENT_VARIANTS as v}
								<option value={v.key}>{variantText(v.key).label}</option>
							{/each}
						</select>
						<p class="mt-1 leading-snug" style="font-size:10px;color:#64748b;">
							{variantText($settlementVariant).note}.
							{#if variantTotals}
								<br /><span style="color:#1f2937;"
									>{fmt(variantTotals.count)} Flächen, {fmt(variantTotals.totalHa)}&thinsp;ha
									({pct(variantTotals.totalHa)}&thinsp;%)</span
								>
							{/if}
						</p>
					</div>
				{/if}

				{#each GROUP_ORDER as group}
					{@const gBands = bandsForGroup(group)}
					{@const gMeta = BAND_GROUPS[group]}
					{@const allHidden = isGroupAllHidden(group)}
					{@const partial = isGroupPartial(group)}
					<div>
						<!-- Group header -->
						<button
							class="flex items-center gap-2 w-full mb-1.5 cursor-pointer"
							onclick={() => toggleGroup(group)}
						>
							<span
								class="w-3 h-3 rounded-sm flex-shrink-0 border border-black/10"
								style="background:{allHidden
									? '#e2e8f0'
									: partial
										? 'linear-gradient(135deg,' +
											gMeta.color +
											' 50%,#e2e8f0 50%)'
										: gMeta.color};"
							></span>
							<span
								class="font-bold uppercase flex-1 text-left"
								style="font-size:9px;letter-spacing:0.12em;color:{allHidden
									? '#94a3b8'
									: gMeta.color};">{gMeta.label}</span
							>
						</button>
						<!-- Per-band rows -->
						<div class="space-y-1 pl-1">
							{#each gBands as def}
								{@const hidden = $hiddenBands.has(def.band)}
								{@const empty = !hidden && $emptyBands.has(def.band)}
								<button
									class="flex items-start gap-2 w-full text-left cursor-pointer transition-opacity duration-300"
									style="opacity:{empty ? 0.45 : 1};"
									onclick={() => toggleBand(def.band)}
								>
									<span
										class="w-3 h-3 rounded-sm flex-shrink-0 mt-0.5 border border-black/10"
										style="background:{hidden
											? '#e2e8f0'
											: hexToRgbStr(def.color)};"
									></span>
									<span
										class="leading-tight"
										style="font-size:11px;color:{hidden
											? '#94a3b8'
											: '#4b5563'};">{def.label}</span
									>
								</button>
							{/each}
						</div>
					</div>
				{/each}

				<!--
					Vektorebenen: per Klick ein- und ausblendbar, wie die Bänder darüber.
					Der Zustand liegt in hiddenVectorLayers (windStore), Map.svelte setzt
					daraus die Sichtbarkeit.
				-->
				<div>
					<div
						class="font-bold uppercase mb-1.5"
						style="font-size:9px;letter-spacing:0.12em;color:var(--blue-sky);"
					>
						Vektorebenen
					</div>
					<div class="space-y-1">
						{#each VECTOR_ROWS as row}
							{@const hidden = $hiddenVectorLayers.has(row.key)}
							<button
								class="flex items-center gap-2 w-full text-left cursor-pointer"
								onclick={() => toggleVector(row.key)}
								aria-pressed={!hidden}
							>
								<span
									class="w-3 h-3 flex-shrink-0 {row.round ? 'rounded-full' : 'rounded-sm'}"
									style="display:inline-block;{hidden ? 'background:#e2e8f0;border:1px solid #cbd5e1;' : row.swatch}"
								></span>
								<span style="font-size:11px;color:{hidden ? '#94a3b8' : '#4b5563'};">{row.label}</span>
							</button>
						{/each}
					</div>
				</div>
			</div>
		{/if}

		<!-- ── Divider ── -->
		<div class="border-t border-slate-100"></div>
	{/if}

	<!-- ── Details toggle row (always visible) ── -->
	<div class="flex items-center">
		<button
			onclick={() => expertMode.update((v) => !v)}
			class="flex items-center gap-2 px-3 py-2.5 flex-1 text-left transition-colors hover:bg-slate-50"
		>
			<svg
				class="w-3.5 h-3.5 flex-shrink-0 opacity-40"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
				stroke-width="2"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
				/>
			</svg>
			<span class="flex-1 font-semibold" style="color: var(--text-dark);"
				>Detailansicht</span
			>
			<!-- Pill toggle -->
			<span
				class="relative inline-flex flex-shrink-0 h-4 w-7 rounded-full transition-colors duration-200"
				style="background: {$expertMode ? 'var(--blue-dark)' : '#cbd5e1'};"
			>
				<span
					class="absolute top-0.5 h-3 w-3 rounded-full bg-white shadow transition-transform duration-200"
					style="transform: translateX({$expertMode ? '14px' : '2px'});"
				></span>
			</span>
		</button>

		<!-- Collapse button (only when panel is open) -->
		{#if panelOpen}
			<button
				onclick={() => (panelOpen = false)}
				class="px-2 py-2.5 transition-colors hover:bg-slate-50 border-l border-slate-100"
				title="Legende schließen"
				aria-label="Legende schließen"
			>
				<svg
					class="w-3.5 h-3.5 opacity-30"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
					stroke-width="2"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M5 15l7-7 7 7"
					/>
				</svg>
			</button>
		{/if}
	</div>
</div>
