<!--
  Land use per energy unit (m² / MWh) – horizontal bar chart.
  Source: Our World in Data
-->
<script lang="ts">
	const entries = [
		{ label: 'Windrad (Fundament)', value: 0.3,  fill: '#009ee3' },
		{ label: 'Gaskraftwerk',        value: 0.7,  fill: '#94a3b8' },
		{ label: 'Freiflächen-PV',      value: 3.0,  fill: '#f59e0b' },
		{ label: 'Kohlekraftwerk',      value: 14.0, fill: '#64748b'  }
	];

	const W = 380, H = 140;
	const labelW = 130;
	const PAD = { top: 16, right: 80, bottom: 20, left: labelW + 8 };
	const barAreaW = W - PAD.left - PAD.right;
	const rowH = (H - PAD.top - PAD.bottom) / entries.length;
	const barH = rowH * 0.55;
	const maxVal = 14;

	function bw(v: number) { return (v / maxVal) * barAreaW; }
</script>

<svg viewBox="0 0 {W} {H}" class="w-full" style="font-family: inherit;">

	<!-- Title unit -->
	<text x={PAD.left} y={PAD.top - 4} font-size="9" fill="#94a3b8">m² Fläche je erzeugter MWh</text>

	{#each entries as entry, i}
		{@const y = PAD.top + i * rowH + (rowH - barH) / 2}
		<!-- Label -->
		<text x={labelW} y={y + barH / 2 + 4} font-size="10" text-anchor="end" fill="#374151">{entry.label}</text>
		<!-- Bar -->
		<rect x={PAD.left} y={y} width={bw(entry.value)} height={barH} rx="3" fill={entry.fill} opacity="0.85"/>
		<!-- Value -->
		<text x={PAD.left + bw(entry.value) + 5} y={y + barH / 2 + 4} font-size="10" fill={entry.fill} font-weight="600">
			{entry.value} m²/MWh
		</text>
	{/each}

	<!-- Source -->
	<text x={W / 2} y={H - 2} font-size="8" text-anchor="middle" fill="#94a3b8">Quelle: Our World in Data</text>
</svg>
