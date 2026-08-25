<!--
  Simplified Merit-Order chart.
  Cheaper renewables enter first; the most expensive plant still needed sets the price for all.
-->
<script lang="ts">
	const W = 380, H = 180;
	const PAD = { top: 20, right: 20, bottom: 44, left: 44 };
	const chartW = W - PAD.left - PAD.right;
	const chartH = H - PAD.top - PAD.bottom;
	const baseY = PAD.top + chartH;

	// Each segment: cumulative demand share (0–100), cost level (0–100)
	const segments = [
		{ label: 'Erneuerbare\n(Wind/Sonne/Wasser)', widthPct: 42, cost: 18,  fill: '#009ee3', labelColor: '#fff' },
		{ label: 'Atom',    widthPct: 14, cost: 42,  fill: '#94a3b8', labelColor: '#fff' },
		{ label: 'Kohle',   widthPct: 18, cost: 65,  fill: '#64748b', labelColor: '#fff' },
		{ label: 'Gas',     widthPct: 26, cost: 100, fill: '#dc2626', labelColor: '#fff' }
	];

	// Compute x positions
	let cumX = 0;
	const bars = segments.map(s => {
		const x = PAD.left + (cumX / 100) * chartW;
		const w = (s.widthPct / 100) * chartW;
		const h = (s.cost / 100) * chartH;
		cumX += s.widthPct;
		return { ...s, x, w, h };
	});

	// Price line = top of Gas bar
	const priceY = baseY - bars[bars.length - 1].h;
</script>

<svg viewBox="0 0 {W} {H}" class="w-full" style="font-family: inherit;">

	<!-- Y-axis label -->
	<text
		x="6" y={PAD.top + chartH / 2}
		font-size="10" fill="#64748b" text-anchor="middle"
		transform="rotate(-90, 6, {PAD.top + chartH / 2})"
	>Preis (Kosten)</text>

	<!-- X-axis label -->
	<text x={PAD.left + chartW / 2} y={H - 4} font-size="10" fill="#64748b" text-anchor="middle">
		Strombedarf →
	</text>

	<!-- Grid lines -->
	{#each [25, 50, 75] as pct}
		<line
			x1={PAD.left} y1={baseY - (pct / 100) * chartH}
			x2={PAD.left + chartW} y2={baseY - (pct / 100) * chartH}
			stroke="#e2e8f0" stroke-width="1"
		/>
	{/each}

	<!-- Bars -->
	{#each bars as bar}
		<rect
			x={bar.x} y={baseY - bar.h}
			width={bar.w} height={bar.h}
			fill={bar.fill} opacity="0.9"
		/>
		<!-- Label inside or below bar -->
		{#each bar.label.split('\n') as line, li}
			<text
				x={bar.x + bar.w / 2}
				y={bar.h > 30 ? baseY - bar.h + 14 + li * 12 : baseY + 16 + li * 11}
				font-size={bar.h > 30 ? '9' : '8.5'}
				text-anchor="middle"
				fill={bar.h > 30 ? bar.labelColor : '#374151'}
			>{line}</text>
		{/each}
	{/each}

	<!-- Price-setting line (dashed, at top of Gas bar) -->
	<line
		x1={PAD.left} y1={priceY}
		x2={PAD.left + chartW + 20} y2={priceY}
		stroke="#dc2626" stroke-width="1.5" stroke-dasharray="6 4" opacity="0.7"
	/>
	<!-- Dot on Gas bar -->
	<circle cx={PAD.left + chartW} cy={priceY} r="5" fill="#dc2626"/>

	<!-- Price label -->
	<text x={PAD.left + chartW + 8} y={priceY + 4} font-size="8.5" fill="#dc2626" font-weight="600">
		→ Marktpreis
	</text>
	<text x={PAD.left + chartW + 8} y={priceY + 14} font-size="8" fill="#dc2626" opacity="0.8">
		für alle
	</text>

	<!-- Axes -->
	<line x1={PAD.left} y1={PAD.top} x2={PAD.left} y2={baseY} stroke="#cbd5e1" stroke-width="1.5"/>
	<line x1={PAD.left} y1={baseY} x2={PAD.left + chartW} y2={baseY} stroke="#cbd5e1" stroke-width="1.5"/>
</svg>
