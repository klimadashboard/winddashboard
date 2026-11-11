<script lang="ts">
	import { onMount } from "svelte";
	import { fmtNumber } from "$lib/format";

	interface DataPoint {
		year: number;
		twh: number;
	}

	/**
	 * `onLatest` meldet den jüngsten gemessenen Jahreswert nach oben.
	 *
	 * Der Satz über dem Diagramm nannte die heutige Produktion früher selbst —
	 * gerechnet aus der Nennleistung des Anlagenregisters mit 30 % Volllast. Das
	 * ergab 10,6 TWh, während die Linie darunter bei 7,0 TWh endete. Solange der
	 * Satz in GWh stand, fiel der Widerspruch nicht auf; in derselben Einheit
	 * stünden zwei verschiedene Zahlen direkt übereinander. Beide kommen jetzt
	 * aus dieser einen Reihe.
	 */
	let { onLatest }: { onLatest?: (d: DataPoint) => void } = $props();

	let data = $state<DataPoint[]>([]);
	let loading = $state(true);
	let error = $state(false);

	// Windkraft-Ausbauziel laut "Energiewelt 2040" (Österreichische Energieagentur).
	const GOAL_TWH = 52.5;
	const GOAL_YEAR = 2040;

	const W = 300;
	const H = 130;
	const PAD = { top: 10, right: 12, bottom: 24, left: 36 };
	const CHART_W = W - PAD.left - PAD.right;
	const CHART_H = H - PAD.top - PAD.bottom;
	const MIN_YEAR = 2015;
	const MAX_YEAR = GOAL_YEAR + 1;

	function xScale(year: number) {
		return PAD.left + ((year - MIN_YEAR) / (MAX_YEAR - MIN_YEAR)) * CHART_W;
	}

	const maxTwh = $derived(Math.max(GOAL_TWH, ...data.map((d) => d.twh), 5) * 1.1);

	function yScale(twh: number) {
		return PAD.top + CHART_H - (twh / maxTwh) * CHART_H;
	}

	const linePath = $derived(
		data.length
			? data
					.map(
						(d, i) =>
							`${i === 0 ? "M" : "L"}${xScale(d.year)},${yScale(d.twh)}`,
					)
					.join(" ")
			: "",
	);

	const areaPath = $derived(
		data.length
			? `M${xScale(data[0].year)},${PAD.top + CHART_H} ` +
					data.map((d) => `L${xScale(d.year)},${yScale(d.twh)}`).join(" ") +
					` L${xScale(data[data.length - 1].year)},${PAD.top + CHART_H} Z`
			: "",
	);

	// Y-axis ticks: 0, midpoint, goal
	const yTicks = [0, Math.round(GOAL_TWH / 2), Math.round(GOAL_TWH)];

	// X-axis ticks: every 5 years
	const xTicks = Array.from(
		{ length: Math.floor((MAX_YEAR - MIN_YEAR) / 5) + 1 },
		(_, i) => MIN_YEAR + i * 5,
	).filter((y) => y <= MAX_YEAR - 1);

	onMount(async () => {
		try {
			// `Jahresproduktion` ist eine gleitende Zwölfmonatssumme, täglich
			// fortgeschrieben. Am 31.12. (in der Reihe: 30.12. 23:00 UTC = 31.12.
			// 00:00 MEZ) entspricht sie genau dem Kalenderjahr — also holen wir
			// gezielt diesen einen Stichtag je Jahr statt der ganzen Tagesreihe.
			//
			// Vorher lief die Abfrage aufsteigend sortiert mit `limit=3000`. Die
			// Reihe beginnt 2014-12-31 und umfasst inzwischen 13.519 Tage, der
			// 3.000. Tag ist der 18.3.2023 — die Grenze schnitt also stillschweigend
			// alles ab 2023 weg. Das Diagramm endete bei 7,0 TWh (2023), während
			// Österreich 2025 tatsächlich 8,5 TWh erzeugt hat (gemeldet am
			// 11.11.2026). Der Stichtagsfilter macht die Abfrage zugleich winzig:
			// elf Zeilen statt 850 kB.
			const base = "https://base.klimadashboard.org";
			const prodRes = await fetch(
				`${base}/items/ee_produktion?filter[Country][_eq]=AT&filter[Type][_contains]=windkraft&filter[Jahresproduktion][_nnull]=true&filter[month(DateTime)][_eq]=12&filter[day(DateTime)][_eq]=30&fields=DateTime,Jahresproduktion&sort=DateTime&limit=200`,
			);
			const prodJson = await prodRes.json();

			// Ein Wert je Kalenderjahr. Der Stichtag kommt je Jahr mehrfach vor
			// (mehrere `Type`-Werte enthalten "windkraft"), die Werte sind dabei
			// identisch — die Map entdoppelt. Das laufende Jahr kann gar nicht
			// vorkommen, solange sein 31.12. nicht erreicht ist; der Vergleich
			// bleibt als Schutz gegen vorausdatierte Zeilen stehen.
			const currentYear = new Date().getFullYear();
			const byYear = new Map<number, number>();
			for (const item of prodJson.data ?? []) {
				const yr = new Date(item.DateTime).getFullYear();
				if (yr >= currentYear) continue;
				const val = parseFloat(item.Jahresproduktion);
				if (!isNaN(val)) byYear.set(yr, val);
			}
			data = Array.from(byYear.entries())
				.sort((a, b) => a[0] - b[0])
				.map(([year, twh]) => ({ year, twh }));
			if (data.length) onLatest?.(data[data.length - 1]);
		} catch {
			error = true;
		} finally {
			loading = false;
		}
	});
</script>

<div class="w-full">
	{#if loading}
		<div class="flex items-center justify-center h-20 text-xs text-slate-400">
			Lade Daten…
		</div>
	{:else if error}
		<div class="text-xs text-slate-400">
			Daten konnten nicht geladen werden.
		</div>
	{:else}
		<svg viewBox="0 0 {W} {H}" class="w-full" style="max-height:{H}px;">
			<!-- area fill -->
			<path d={areaPath} fill="#2563eb" fill-opacity="0.15" />

			<!-- y-axis gridlines + labels -->
			{#each yTicks as tick}
				<line
					x1={PAD.left}
					y1={yScale(tick)}
					x2={PAD.left + CHART_W}
					y2={yScale(tick)}
					stroke="#e2e8f0"
					stroke-width="1"
				/>
				<text
					x={PAD.left - 4}
					y={yScale(tick)}
					text-anchor="end"
					dominant-baseline="middle"
					font-size="8"
					fill="#94a3b8">{tick}</text
				>
			{/each}

			<!-- y-axis unit -->
			<text
				x={PAD.left}
				y={PAD.top - 2}
				text-anchor="middle"
				font-size="7.5"
				fill="#94a3b8">TWh</text
			>

			<!-- x-axis ticks -->
			{#each xTicks as yr}
				<text
					x={xScale(yr)}
					y={H - 4}
					text-anchor="middle"
					font-size="8"
					fill="#94a3b8">{yr}</text
				>
			{/each}

			<!-- production line -->
			<path
				d={linePath}
				fill="none"
				stroke="#2563eb"
				stroke-width="2"
				stroke-linejoin="round"
			/>

			<!-- latest data point pulse -->
			{#if data.length}
				{@const last = data[data.length - 1]}
				<circle
					cx={xScale(last.year)}
					cy={yScale(last.twh)}
					r="3.5"
					fill="#2563eb"
				/>
			{/if}

			<!-- Dashed projection from the latest production value to the goal —
				 shows the gap to close rather than a flat reference line. -->
			{#if data.length}
				{@const last = data[data.length - 1]}
				<line
					x1={xScale(last.year)}
					y1={yScale(last.twh)}
					x2={xScale(GOAL_YEAR)}
					y2={yScale(GOAL_TWH)}
					stroke="#2563eb"
					stroke-width="1.5"
					stroke-dasharray="4 3"
				/>
				<circle
					cx={xScale(GOAL_YEAR)}
					cy={yScale(GOAL_TWH)}
					r="3"
					fill="#fff"
					stroke="#2563eb"
					stroke-width="1.5"
				/>
				<text
					x={xScale(GOAL_YEAR)}
					y={yScale(GOAL_TWH) - 6}
					text-anchor="end"
					font-size="7.5"
					fill="#2563eb"
					font-weight="600">{GOAL_YEAR}: {fmtNumber(GOAL_TWH, 1)} TWh</text
				>
			{/if}

			<!-- axes -->
			<line
				x1={PAD.left}
				y1={PAD.top}
				x2={PAD.left}
				y2={PAD.top + CHART_H}
				stroke="#cbd5e1"
				stroke-width="1"
			/>
			<line
				x1={PAD.left}
				y1={PAD.top + CHART_H}
				x2={PAD.left + CHART_W}
				y2={PAD.top + CHART_H}
				stroke="#cbd5e1"
				stroke-width="1"
			/>
		</svg>
		<p class="text-[9px] text-slate-400 mt-0.5">
			Jahresproduktion Windenergie AT in TWh · Quelle: E-Control. Ausbauziel
			{GOAL_YEAR}: {fmtNumber(GOAL_TWH, 1)}&nbsp;TWh laut
			<a
				href="https://www.unsereenergiewelt2040.at/energie/die-wichtigsten-zahlen-im-ueberblick"
				target="_blank"
				rel="noopener"
				class="underline hover:text-slate-600"
			>„Energiewelt 2040“</a
			>, Österreichische Energieagentur.
		</p>
	{/if}
</div>
