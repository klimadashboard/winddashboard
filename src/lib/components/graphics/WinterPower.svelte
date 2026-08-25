<!--
  Monthly bar chart – wind generation is highest in winter.
  Relative values from seasonal wind patterns (2/3 in winter half-year).
-->
<script lang="ts">
	const months = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'];
	// Relative wind generation index (0–100)
	const values = [100, 92, 70, 50, 38, 28, 26, 32, 48, 68, 88, 96];
	const isWinter = [true, true, true, false, false, false, false, false, false, true, true, true];

	const W = 360, H = 160;
	const PAD = { top: 20, right: 10, bottom: 36, left: 8 };
	const chartW = W - PAD.left - PAD.right;
	const chartH = H - PAD.top - PAD.bottom;

	const barW = chartW / months.length;
	const gap = barW * 0.18;

	function barX(i: number) { return PAD.left + i * barW + gap / 2; }
	function barH(v: number) { return (v / 100) * chartH; }
	function barY(v: number) { return PAD.top + chartH - barH(v); }
</script>

<svg viewBox="0 0 {W} {H}" class="w-full" style="font-family: inherit;">
	<!-- Y-axis label -->
	<text x={PAD.left} y={PAD.top - 6} font-size="9" fill="#94a3b8" text-anchor="start">Erzeugung (relativ)</text>

	<!-- Bars -->
	{#each values as v, i}
		<rect
			x={barX(i)}
			y={barY(v)}
			width={barW - gap}
			height={barH(v)}
			rx="2"
			fill={isWinter[i] ? '#1e3689' : '#93c5fd'}
		/>
	{/each}

	<!-- Month labels -->
	{#each months as m, i}
		<text
			x={barX(i) + (barW - gap) / 2}
			y={H - PAD.bottom + 12}
			font-size="9"
			text-anchor="middle"
			fill={isWinter[i] ? '#1e3689' : '#64748b'}
			font-weight={isWinter[i] ? '600' : '400'}
		>{m}</text>
	{/each}

	<!-- Winter bracket -->
	<line x1={barX(0)} y1={H - PAD.bottom + 24} x2={barX(2) + barW - gap} y2={H - PAD.bottom + 24} stroke="#1e3689" stroke-width="1.5"/>
	<line x1={barX(9)} y1={H - PAD.bottom + 24} x2={barX(11) + barW - gap} y2={H - PAD.bottom + 24} stroke="#1e3689" stroke-width="1.5"/>

	<!-- Annotation -->
	<text x={W / 2} y={H - 2} font-size="9.5" text-anchor="middle" fill="#1e3689" font-weight="600">
		2/3 des Windstroms im Winterhalbjahr
	</text>
</svg>
