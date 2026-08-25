<script lang="ts">
	import { selectedRegion, regionStats } from '$lib/stores/windStore';
	import type { Region, ZoneStats } from '$lib/stores/windStore';

	const region = $derived($selectedRegion);
	const stats = $derived($regionStats);

	function summaryText(r: Region, s: ZoneStats | null): string {
		if (!s) return `Daten für ${r.name} werden geladen …`;
		if (s.count === 0) return `In ${r.name} wurden im sichtbaren Kartenausschnitt keine potenziellen Windeignungsflächen gefunden.`;
		const areas = s.totalAreaHa.toLocaleString('de-AT');
		const pd = s.meanPdWm2 > 0 ? ` mit einer mittleren Windleistungsdichte von ${s.meanPdWm2} W/m²` : '';
		const turbines = s.turbineCount > 0 ? ` Bereits ${s.turbineCount} Windanlage${s.turbineCount !== 1 ? 'n' : ''} ${s.turbineCount !== 1 ? 'stehen' : 'steht'} in diesem Gebiet.` : '';
		return `Im sichtbaren Ausschnitt von ${r.name} liegen ${s.count} potenzielle Windeignungsfläche${s.count !== 1 ? 'n' : ''} mit insgesamt ${areas} ha${pd}.${turbines}`;
	}

	const faqItems = [
		{ q: 'Was bedeutet Windpotenzial?', a: 'Das Windpotenzial beschreibt die verfügbare Windenergie an einem Standort, ausgedrückt als mittlere Leistungsdichte in Watt pro Quadratmeter (W/m²). Je höher der Wert, desto wirtschaftlicher der Betrieb einer Windkraftanlage.' },
		{ q: 'Was bedeutet der Schwellenwert von 300 W/m²?', a: 'Als wirtschaftliches Minimum gilt eine mittlere Windleistungsdichte von 300 W/m² in 150 m Nabenhöhe. Flächen mit geringerem Windpotenzial oder fehlenden Winddaten werden als ungeeignet ausgeschlossen.' },
		{ q: 'Welche Abstände und Ausschlussgründe gelten?', a: 'Mindestabstände zu Wohngebieten, Einzelgebäuden, Straßen (150 m), Eisenbahnen (150 m) und Freileitungen (150 m) sowie Schutzgebiete (Natura 2000, Nationalparks) schließen Flächen aus.' },
		{ q: 'Wie werden offizielle Eignungszonen ausgewiesen?', a: 'Offizielle Windkraft-Eignungszonen werden in sektoralen Raumordnungsprogrammen der Bundesländer festgelegt. Bisher hat Niederösterreich (NÖ LGBl. Nr. 47/2024) solche Zonen definiert.' },
		{ q: 'Welche Datengrundlagen werden verwendet?', a: 'Die Daten basieren auf dem Global Wind Atlas (Windpotenzial), dem österreichischen DGM 25 m (Gelände), OpenStreetMap (Infrastruktur) sowie Schutzgebietsdaten und offiziellen Verwaltungsgrenzen.' },
	];

	let openFaq: number | null = $state(null);
</script>

{#if region}
	<div class="bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden max-h-[60vh] flex flex-col">
		<!-- Header -->
		<div class="flex items-start justify-between px-5 py-4 border-b border-slate-100 flex-shrink-0">
			<div>
				<div class="flex items-center gap-2">
					<h2 class="font-semibold text-slate-900 text-base">{region.name}</h2>
					<span class="text-xs bg-slate-100 text-slate-500 rounded-full px-2 py-0.5">{region.layer_label}</span>
				</div>
				{#if stats !== null}
					<p class="text-xs text-slate-500 mt-1 leading-relaxed max-w-lg">{summaryText(region, stats)}</p>
				{:else}
					<p class="text-xs text-slate-400 mt-1 animate-pulse">Berechne Windpotenzial …</p>
				{/if}
			</div>
			<button
				onclick={() => selectedRegion.set(null)}
				class="ml-4 text-slate-400 hover:text-slate-600 transition-colors flex-shrink-0 mt-0.5"
				aria-label="Panel schließen"
			>
				<svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
					<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>

		<!-- Scrollable content -->
		<div class="overflow-y-auto flex-1">
			<!-- 3-Column explainer skeleton -->
			<div class="px-5 py-4 border-b border-slate-100">
				<h3 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Kurzübersicht</h3>
				<div class="grid grid-cols-3 gap-3">
					{#each [
						{ icon: '💨', label: 'Windpotenzial', color: 'blue' },
						{ icon: '📋', label: 'Regulierung', color: 'amber' },
						{ icon: '🏗️', label: 'Bestand', color: 'slate' }
					] as col}
						<div class="rounded-xl border border-slate-100 bg-slate-50 p-3">
							<div class="text-lg mb-1">{col.icon}</div>
							<div class="text-xs font-semibold text-slate-600 mb-2">{col.label}</div>
							<!-- Skeleton bars -->
							<div class="space-y-1.5">
								<div class="h-2 bg-slate-200 rounded animate-pulse w-full"></div>
								<div class="h-2 bg-slate-200 rounded animate-pulse w-4/5"></div>
								<div class="h-2 bg-slate-200 rounded animate-pulse w-3/5"></div>
							</div>
							<div class="mt-3 h-8 bg-slate-200 rounded-lg animate-pulse"></div>
						</div>
					{/each}
				</div>
			</div>

			<!-- FAQ section -->
			<div class="px-5 py-4">
				<h3 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">Häufige Fragen</h3>
				<div class="space-y-1">
					{#each faqItems as item, i}
						<div class="rounded-xl border border-slate-100 overflow-hidden">
							<button
								class="w-full flex items-center justify-between px-3 py-2.5 text-left hover:bg-slate-50 transition-colors"
								onclick={() => openFaq = openFaq === i ? null : i}
							>
								<span class="text-sm font-medium text-slate-700">{item.q}</span>
								<svg
									class="w-4 h-4 text-slate-400 flex-shrink-0 ml-2 transition-transform duration-200"
									class:rotate-180={openFaq === i}
									fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"
								>
									<path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
								</svg>
							</button>
							{#if openFaq === i}
								<div class="px-3 pb-3 text-xs text-slate-500 leading-relaxed border-t border-slate-50">
									{item.a}
								</div>
							{/if}
						</div>
					{/each}
				</div>
			</div>
		</div>
	</div>
{/if}
