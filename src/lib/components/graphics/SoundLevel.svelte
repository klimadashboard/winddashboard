<!--
  Sound level comparison: street traffic vs. wind turbine at 1.2 km vs. fridge
-->
<svg viewBox="0 0 360 120" class="w-full" style="font-family: inherit;">

	<!-- Column backgrounds -->
	<rect x="0"   y="0" width="120" height="112" rx="10" fill="#fee2e2" opacity="0.5"/>
	<rect x="122" y="0" width="116" height="112" rx="10" fill="#dbeafe" opacity="0.5"/>
	<rect x="240" y="0" width="120" height="112" rx="10" fill="#dcfce7" opacity="0.5"/>

	<!-- ── Column 1: Street traffic 80 dB ── -->
	<!-- Car icon (simplified) -->
	<g transform="translate(28, 14)">
		<rect x="4" y="8" width="28" height="12" rx="3" fill="#ef4444"/>
		<rect x="8" y="4" width="18" height="10" rx="2" fill="#fca5a5"/>
		<circle cx="9"  cy="21" r="4" fill="#374151"/>
		<circle cx="27" cy="21" r="4" fill="#374151"/>
		<circle cx="9"  cy="21" r="2" fill="#9ca3af"/>
		<circle cx="27" cy="21" r="2" fill="#9ca3af"/>
	</g>
	<!-- Sound waves -->
	<g transform="translate(72, 18)" fill="none" stroke="#ef4444" stroke-width="1.5">
		<path d="M0,8 Q5,0 5,8 Q5,16 0,16" stroke-opacity="0.8"/>
		<path d="M7,5 Q14,-2 14,8 Q14,18 7,19" stroke-opacity="0.5"/>
	</g>
	<text x="60" y="58" font-size="26" font-weight="800" text-anchor="middle" fill="#dc2626">80 dB</text>
	<text x="60" y="74" font-size="10" text-anchor="middle" fill="#7f1d1d">Straßenverkehr</text>
	<text x="60" y="88" font-size="9" text-anchor="middle" fill="#991b1b" opacity="0.8">(Vorbeifahrt)</text>

	<!-- ── Column 2: Wind turbine 35-40 dB ── -->
	<!-- Turbine icon -->
	<g transform="translate(158, 10)">
		<!-- Tower -->
		<rect x="17" y="14" width="5" height="16" rx="1" fill="#475569"/>
		<!-- Hub -->
		<circle cx="19.5" cy="14" r="3" fill="#334155"/>
		<!-- Blades -->
		<line x1="19.5" y1="14" x2="19.5" y2="0"  stroke="#94a3b8" stroke-width="2.5" stroke-linecap="round"/>
		<line x1="19.5" y1="14" x2="32"   y2="21"  stroke="#94a3b8" stroke-width="2.5" stroke-linecap="round"/>
		<line x1="19.5" y1="14" x2="7"    y2="21"  stroke="#94a3b8" stroke-width="2.5" stroke-linecap="round"/>
	</g>
	<!-- Distance indicator -->
	<line x1="130" y1="40" x2="230" y2="40" stroke="#93c5fd" stroke-width="1" stroke-dasharray="3 2"/>
	<text x="180" y="37" font-size="8" text-anchor="middle" fill="#3b82f6">1,2 km</text>
	<text x="180" y="62" font-size="22" font-weight="800" text-anchor="middle" fill="#1e3689">35–40 dB</text>
	<text x="180" y="78" font-size="10" text-anchor="middle" fill="#1e3a5f">Windrad (1,2 km Abstand)</text>
	<text x="180" y="92" font-size="9" text-anchor="middle" fill="#1e40af" opacity="0.8">bei Volllast</text>

	<!-- ── Column 3: Fridge 30 dB ── -->
	<!-- Fridge icon -->
	<g transform="translate(274, 10)">
		<rect x="4" y="2" width="24" height="28" rx="3" fill="#6ee7b7"/>
		<rect x="4" y="2" width="24" height="10" rx="3" fill="#34d399"/>
		<line x1="28" y1="12" x2="4"  y2="12" stroke="white" stroke-width="1"/>
		<rect x="6"  y="5" width="4" height="5" rx="1" fill="#fff" opacity="0.6"/>
		<rect x="6"  y="16" width="4" height="12" rx="1" fill="#fff" opacity="0.4"/>
	</g>
	<text x="300" y="58" font-size="26" font-weight="800" text-anchor="middle" fill="#059669">30 dB</text>
	<text x="300" y="74" font-size="10" text-anchor="middle" fill="#065f46">Kühlschrank</text>
	<text x="300" y="88" font-size="9" text-anchor="middle" fill="#047857" opacity="0.8">(Betriebsgeräusch)</text>

	<!-- Source -->
	<text x="180" y="114" font-size="8" text-anchor="middle" fill="#94a3b8">Quelle: ÖVE/ÖNORM EN 61400-11</text>
</svg>
