<!--
  Paired bar chart: endangered bird populations growing alongside wind turbine growth.
  Source: IG Windkraft, WWF, BirdLife, Nationalpark Donau-Auen, ORF NÖ
-->
<script lang="ts">
	const W = 420, H = 180;
	const PAD = { top: 16, right: 10, bottom: 44, left: 10 };
	const chartH = H - PAD.top - PAD.bottom;
	const baseY = PAD.top + chartH;

	const groupCount = 5; // turbines + 4 species
	const groupW = (W - PAD.left - PAD.right) / groupCount;
	const barW = groupW * 0.35;
	const barGap = groupW * 0.08;

	function groupX(i: number) {
		return PAD.left + (i + 0.5) * groupW;
	}

	// Turbine context bar (separate scale)
	const turbines = { before: 34, after: 1447, label: ['Windräder', 'in Österreich'], yearBefore: 1996 };
	const turbMax = 1500;
	function turbH(v: number) { return (v / turbMax) * chartH; }

	// Bird species (shared scale)
	const birdMax = 400;
	function birdH(v: number) { return Math.max((v / birdMax) * chartH, 2); }

	const species = [
		{ label: ['Brütende', 'Seeadler'],    before: 0,  after: 90,  yearBefore: 1996 },
		{ label: ['Brütende', 'Kaiseradler'], before: 0,  after: 50,  yearBefore: 1996 },
		{ label: ['Groß-', 'trappen'],        before: 60, after: 360, yearBefore: 2000 },
		{ label: ['Brütende', 'Rotmilane'],   before: 0,  after: 170, yearBefore: 1980 }
	];

	// Pre-compute all bar data to avoid {@const} at root level
	const turbX = groupX(0);
	const turbBeforeH = turbH(turbines.before);
	const turbAfterH  = turbH(turbines.after);

	const birdBars = species.map((sp, i) => ({
		...sp,
		gx: groupX(i + 1),
		beforeH: birdH(sp.before),
		afterH:  birdH(sp.after)
	}));
</script>

<svg viewBox="0 0 {W} {H}" class="w-full" style="font-family: inherit;">

	<!-- Baseline -->
	<line x1={PAD.left} y1={baseY} x2={W - PAD.right} y2={baseY} stroke="#e2e8f0" stroke-width="1"/>

	<!-- ── Turbine group ── -->
	<!-- before bar -->
	<rect
		x={turbX - barW - barGap / 2} y={baseY - turbBeforeH}
		width={barW} height={turbBeforeH}
		fill="#bfdbfe" rx="2"
	/>
	<!-- after bar -->
	<rect
		x={turbX + barGap / 2} y={baseY - turbAfterH}
		width={barW} height={turbAfterH}
		fill="#1e3689" rx="2"
	/>
	<!-- value labels -->
	<text x={turbX - barW / 2 - barGap / 2} y={baseY - turbBeforeH - 3} font-size="8" text-anchor="middle" fill="#64748b">{turbines.before}</text>
	<text x={turbX + barW / 2 + barGap / 2} y={baseY - turbAfterH - 3}  font-size="9" text-anchor="middle" fill="#1e3689" font-weight="600">{turbines.after}</text>
	<!-- year labels -->
	<text x={turbX - barW / 2 - barGap / 2} y={baseY + 10} font-size="8" text-anchor="middle" fill="#94a3b8">{turbines.yearBefore}</text>
	<text x={turbX + barW / 2 + barGap / 2} y={baseY + 10} font-size="8" text-anchor="middle" fill="#64748b">2025</text>
	<!-- species label -->
	{#each turbines.label as line, li}
		<text x={turbX} y={baseY + 22 + li * 10} font-size="8.5" text-anchor="middle" fill="#1e3689" font-weight="600">{line}</text>
	{/each}

	<!-- ── Bird species groups ── -->
	{#each birdBars as bar}
		<!-- before bar -->
		<rect
			x={bar.gx - barW - barGap / 2} y={baseY - bar.beforeH}
			width={barW} height={bar.beforeH}
			fill="#bbf7d0" rx="2"
		/>
		<!-- after bar -->
		<rect
			x={bar.gx + barGap / 2} y={baseY - bar.afterH}
			width={barW} height={bar.afterH}
			fill="#16a34a" rx="2"
		/>
		<!-- value labels -->
		{#if bar.before > 0}
			<text x={bar.gx - barW / 2 - barGap / 2} y={baseY - bar.beforeH - 3} font-size="8" text-anchor="middle" fill="#64748b">{bar.before}</text>
		{/if}
		<text x={bar.gx + barW / 2 + barGap / 2} y={baseY - bar.afterH - 3} font-size="9" text-anchor="middle" fill="#15803d" font-weight="600">{bar.after}</text>
		<!-- year labels -->
		<text x={bar.gx - barW / 2 - barGap / 2} y={baseY + 10} font-size="8" text-anchor="middle" fill="#94a3b8">{bar.yearBefore}</text>
		<text x={bar.gx + barW / 2 + barGap / 2} y={baseY + 10} font-size="8" text-anchor="middle" fill="#64748b">2025</text>
		<!-- species label -->
		{#each bar.label as line, li}
			<text x={bar.gx} y={baseY + 22 + li * 10} font-size="8.5" text-anchor="middle" fill="#374151">{line}</text>
		{/each}
	{/each}

	<!-- Source note -->
	<text x={W / 2} y={H - 1} font-size="8" text-anchor="middle" fill="#94a3b8">
		Quelle: IG Windkraft, WWF, BirdLife, Nationalpark Donau-Auen, ORF NÖ
	</text>
</svg>
