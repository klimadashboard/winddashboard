<!--
  Stylised wind turbine with height annotations.
  Scale: ~0.85 px per metre. Ground at y=240.
  Total height 275 m → top at y = 240 - 233 = 7.
-->
<script lang="ts">
	// ground Y
	const GY = 242;
	// px per metre
	const S = 0.85;

	function ym(m: number) { return GY - m * S; }

	// Turbine geometry
	const cx = 110; // tower centre
	const hubY = ym(190); // nacelle/hub height
	const bladeR = 85 * S; // rotor radius in px

	// Blade endpoints (hub at cx, hubY)
	const blades = [
		[cx, hubY - bladeR],                            // up
		[cx + bladeR * Math.sin(2.094), hubY - bladeR * Math.cos(2.094)], // 120°
		[cx + bladeR * Math.sin(4.189), hubY - bladeR * Math.cos(4.189)]  // 240°
	];

	// Height levels
	const levels = [
		{ m: 30,  label: 'Baumspitzen 30 m',                    color: '#16a34a', dash: false },
		{ m: 50,  label: 'Biologische Hauptaktivität bis 50 m', color: '#dc2626', dash: true  },
		{ m: 105, label: 'Flügelunterkante 105 m',              color: '#dc2626', dash: true  },
		{ m: 190, label: 'Nabenhöhe 190 m',                     color: '#64748b', dash: true  },
		{ m: 275, label: 'Gesamthöhe 275 m',                    color: '#64748b', dash: true  }
	];
</script>

<svg viewBox="0 0 420 270" class="w-full" style="font-family: inherit;">

	<!-- Sky background -->
	<rect width="420" height="270" fill="#f8faff"/>

	<!-- Forest silhouette at 30 m -->
	{#each Array.from({length: 9}, (_, i) => i) as i}
		{@const tx = 16 + i * 22}
		{@const ty = ym(30)}
		<polygon points="{tx},{GY} {tx + 11},{ty} {tx + 22},{GY}" fill="#15803d" opacity="0.8"/>
		<rect x={tx + 7} y={GY - 8} width="8" height="10" fill="#14532d" opacity="0.6"/>
	{/each}
	<rect x="0" y={GY} width="420" height="30" fill="#d1fae5" opacity="0.3"/>

	<!-- Tower (tapered) -->
	<polygon
		points="{cx - 7},{GY} {cx + 7},{GY} {cx + 4},{hubY} {cx - 4},{hubY}"
		fill="#94a3b8"
	/>

	<!-- Blades -->
	{#each blades as [bx, by]}
		<line x1={cx} y1={hubY} x2={bx} y2={by}
			stroke="#cbd5e1" stroke-width="4" stroke-linecap="round"/>
	{/each}

	<!-- Hub -->
	<circle cx={cx} cy={hubY} r="5" fill="#475569"/>
	<circle cx={cx} cy={hubY} r="2.5" fill="#1e3689"/>

	<!-- Height marker lines + labels -->
	{#each levels as { m, label, color, dash }}
		{@const y = ym(m)}
		<line
			x1={cx + 10} y1={y} x2={160} y2={y}
			stroke={color}
			stroke-width={m <= 50 ? 1.5 : 1}
			stroke-dasharray={dash ? '5 3' : 'none'}
		/>
		<!-- Tick on tower -->
		<line x1={cx - 4} y1={y} x2={cx + 4} y2={y} stroke={color} stroke-width="1.5"/>
		<text x="164" y={y + 4} font-size="10.5" fill={color} font-weight={m <= 50 ? '600' : '400'}>{label}</text>
	{/each}

	<!-- Gap annotation between 50 m and 105 m -->
	<line x1="146" y1={ym(50)} x2="146" y2={ym(105)} stroke="#f59e0b" stroke-width="2"/>
	<line x1="142" y1={ym(50)}  x2="150" y2={ym(50)}  stroke="#f59e0b" stroke-width="1.5"/>
	<line x1="142" y1={ym(105)} x2="150" y2={ym(105)} stroke="#f59e0b" stroke-width="1.5"/>
	<text x="151" y={ym(50) + (ym(105) - ym(50)) / 2 + 4} font-size="9" fill="#d97706" font-weight="600">55 m</text>
	<text x="151" y={ym(50) + (ym(105) - ym(50)) / 2 + 14} font-size="9" fill="#d97706">Abstand</text>
</svg>
