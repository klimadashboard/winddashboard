<!--
  Infrasound comparison: 3.5h car ride = 27 years standing 300 m from a wind turbine
-->
<svg viewBox="0 0 360 110" class="w-full" style="font-family: inherit;">

	<!-- Left side: Car -->
	<rect x="8" y="8" width="150" height="94" rx="12" fill="#fef9c3" opacity="0.6"/>

	<!-- Car icon -->
	<g transform="translate(24, 18)">
		<rect x="4" y="9" width="34" height="14" rx="3" fill="#f59e0b"/>
		<rect x="10" y="4" width="22" height="11" rx="2" fill="#fde68a"/>
		<circle cx="10" cy="24" r="5" fill="#374151"/>
		<circle cx="32" cy="24" r="5" fill="#374151"/>
		<circle cx="10" cy="24" r="2.5" fill="#9ca3af"/>
		<circle cx="32" cy="24" r="2.5" fill="#9ca3af"/>
	</g>
	<!-- Sound waves from car -->
	<g fill="none" stroke="#f59e0b" stroke-width="1.5" transform="translate(72, 22)">
		<path d="M0,7 Q4,0 4,7 Q4,14 0,14" opacity="0.9"/>
		<path d="M6,4 Q12,-1 12,7 Q12,15 6,18" opacity="0.6"/>
		<path d="M13,2 Q21,-2 21,7 Q21,16 13,20" opacity="0.35"/>
	</g>

	<text x="83" y="64" font-size="28" font-weight="800" text-anchor="middle" fill="#d97706">3,5 h</text>
	<text x="83" y="80" font-size="11" text-anchor="middle" fill="#92400e">Autofahrt</text>
	<text x="83" y="94" font-size="9" text-anchor="middle" fill="#b45309" opacity="0.8">Infraschall-Belastung</text>

	<!-- Equals sign -->
	<text x="180" y="60" font-size="30" font-weight="300" text-anchor="middle" fill="#94a3b8">=</text>

	<!-- Right side: Wind turbine at 300m -->
	<rect x="202" y="8" width="150" height="94" rx="12" fill="#dbeafe" opacity="0.5"/>

	<!-- Turbine icon -->
	<g transform="translate(216, 16)">
		<rect x="17" y="16" width="5" height="18" rx="1" fill="#64748b"/>
		<circle cx="19.5" cy="16" r="3.5" fill="#334155"/>
		<line x1="19.5" y1="16" x2="19.5" y2="0"  stroke="#94a3b8" stroke-width="3" stroke-linecap="round"/>
		<line x1="19.5" y1="16" x2="33"   y2="24"  stroke="#94a3b8" stroke-width="3" stroke-linecap="round"/>
		<line x1="19.5" y1="16" x2="6"    y2="24"  stroke="#94a3b8" stroke-width="3" stroke-linecap="round"/>
	</g>

	<!-- 300m distance line + person -->
	<line x1="254" y1="46" x2="330" y2="46" stroke="#93c5fd" stroke-width="1.5" stroke-dasharray="4 3"/>
	<text x="292" y="43" font-size="8.5" text-anchor="middle" fill="#3b82f6">300 m</text>
	<!-- Person icon -->
	<g transform="translate(326, 30)">
		<circle cx="6" cy="4"  r="4" fill="#475569"/>
		<line x1="6" y1="8"  x2="6" y2="20" stroke="#475569" stroke-width="2.5"/>
		<line x1="6" y1="12" x2="1" y2="17" stroke="#475569" stroke-width="2"/>
		<line x1="6" y1="12" x2="11" y2="17" stroke="#475569" stroke-width="2"/>
		<line x1="6" y1="20" x2="1" y2="28" stroke="#475569" stroke-width="2"/>
		<line x1="6" y1="20" x2="11" y2="28" stroke="#475569" stroke-width="2"/>
	</g>

	<text x="277" y="68" font-size="24" font-weight="800" text-anchor="middle" fill="#1e3689">27 Jahre</text>
	<text x="277" y="83" font-size="11" text-anchor="middle" fill="#1e3a5f">Windrad (300 m Abstand)</text>
	<text x="277" y="97" font-size="9" text-anchor="middle" fill="#1d4ed8" opacity="0.8">gleiche Infraschall-Belastung</text>

	<!-- Source -->
	<text x="180" y="108" font-size="7.5" text-anchor="middle" fill="#94a3b8">Studie zit. in: Österreichische Ärztekammer-Stellungnahme</text>
</svg>
