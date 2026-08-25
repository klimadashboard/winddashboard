<!--
  Repowering Windpark Japons: 7 old (2 MW) → 3 new (5–7 MW) turbines
  Source: EVN
-->
<svg viewBox="0 0 360 160" class="w-full" style="font-family: inherit;">

	<!-- Left: Before -->
	<rect x="4" y="4" width="164" height="148" rx="12" fill="#f1f5f9" opacity="0.8"/>
	<text x="86" y="20" font-size="11" font-weight="700" text-anchor="middle" fill="#475569">Vorher</text>

	<!-- 7 small turbines -->
	{#each Array.from({length: 7}, (_, i) => i) as i}
		{@const col = i % 4}
		{@const row = Math.floor(i / 4)}
		{@const tx = 18 + col * 38}
		{@const ty = 30 + row * 48}
		<!-- tower -->
		<rect x={tx + 8} y={ty + 14} width="3" height="18" rx="1" fill="#94a3b8"/>
		<!-- hub -->
		<circle cx={tx + 9.5} cy={ty + 14} r="2.5" fill="#64748b"/>
		<!-- blades -->
		<line x1={tx+9.5} y1={ty+14} x2={tx+9.5} y2={ty+2}  stroke="#cbd5e1" stroke-width="2" stroke-linecap="round"/>
		<line x1={tx+9.5} y1={ty+14} x2={tx+20}  y2={ty+20} stroke="#cbd5e1" stroke-width="2" stroke-linecap="round"/>
		<line x1={tx+9.5} y1={ty+14} x2={tx-1}   y2={ty+20} stroke="#cbd5e1" stroke-width="2" stroke-linecap="round"/>
	{/each}

	<!-- Household count -->
	<text x="86" y="108" font-size="22" font-weight="800" text-anchor="middle" fill="#64748b">6.000</text>
	<text x="86" y="122" font-size="10" text-anchor="middle" fill="#94a3b8">Haushalte</text>
	<text x="86" y="136" font-size="9.5" text-anchor="middle" fill="#94a3b8">7 × 2 MW</text>

	<!-- Arrow -->
	<text x="180" y="86" font-size="26" font-weight="300" text-anchor="middle" fill="#009ee3">→</text>
	<text x="180" y="102" font-size="8" text-anchor="middle" fill="#64748b">Repowering</text>
	<text x="180" y="113" font-size="8" text-anchor="middle" fill="#64748b">2021</text>

	<!-- Right: After -->
	<rect x="196" y="4" width="160" height="148" rx="12" fill="#dbeafe" opacity="0.5"/>
	<text x="276" y="20" font-size="11" font-weight="700" text-anchor="middle" fill="#1e3689">Nachher</text>

	<!-- 3 large turbines -->
	{#each Array.from({length: 3}, (_, i) => i) as i}
		{@const tx = 210 + i * 50}
		{@const ty = 28}
		<!-- tower -->
		<rect x={tx + 13} y={ty + 24} width="5" height="30" rx="1" fill="#475569"/>
		<!-- hub -->
		<circle cx={tx + 15.5} cy={ty + 24} r="4" fill="#334155"/>
		<!-- blades -->
		<line x1={tx+15.5} y1={ty+24} x2={tx+15.5} y2={ty}    stroke="#64748b" stroke-width="3.5" stroke-linecap="round"/>
		<line x1={tx+15.5} y1={ty+24} x2={tx+36}   y2={ty+36} stroke="#64748b" stroke-width="3.5" stroke-linecap="round"/>
		<line x1={tx+15.5} y1={ty+24} x2={tx-5}    y2={ty+36} stroke="#64748b" stroke-width="3.5" stroke-linecap="round"/>
	{/each}

	<!-- Household count -->
	<text x="276" y="108" font-size="22" font-weight="800" text-anchor="middle" fill="#1e3689">10.000</text>
	<text x="276" y="122" font-size="10" text-anchor="middle" fill="#1e3a5f">Haushalte</text>
	<text x="276" y="136" font-size="9.5" text-anchor="middle" fill="#1e40af">3 × 5–7 MW</text>

	<!-- Source -->
	<text x="180" y="158" font-size="8" text-anchor="middle" fill="#94a3b8">Quelle: EVN – Windpark Japons, Bezirk Horn, 2021</text>
</svg>
