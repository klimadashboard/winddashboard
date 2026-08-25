import type { Region, ZoneStats, OfficialZoneType } from '$lib/stores/windStore';

export interface RegionIntroContent {
	paragraphs: string[];
	bullets?: string[];
	// Notes shown after the bullet list (or after the paragraphs, if there are no bullets) —
	// used for legal/context remarks that apply regardless of the specific case above.
	afterBullets?: string[];
}

// State region IDs from base.klimadashboard.org/items/regions (layer=state)
export const STATE = {
	BURGENLAND:       '2bc3faed-7cb4-492c-9097-145a0f8f1f01',
	NIEDERÖSTERREICH: '39b741d5-c7ca-4ff2-9c5c-c0709daea62c',
	STEIERMARK:       '63bf6c1a-cb90-40f9-913e-daba7431fd56',
	WIEN:             '76888a3b-ce35-482c-88e6-79cff27be8c5',
	KÄRNTEN:          '9297c491-c419-4ca5-a10f-4d7b93998909',
	OBERÖSTERREICH:   '9cde29fb-d189-4461-b766-5dfd3de56303',
	TIROL:            'a4bafe0a-f71b-40a0-8d1d-1baa8af05692',
	SALZBURG:         'b9b8feef-4d7d-4c23-ac21-60377d96ead0',
	VORARLBERG:       'fc5cfc23-3b75-4b7a-9d50-6e4ec018bd1a',
} as const;

const DETAIL_BULLETS = [
	'detaillierte Windmessung',
	'möglicher Anschluss ans Stromnetz',
	'Zufahrtsmöglichkeiten',
	'Pachtverträge mit Grundstückseigentümer:innen',
	'Naturverträglichkeit',
];

// Niederösterreich's 1,2-km-Mindestabstand gilt erst seit 2004 — ältere Windräder
// können daher außerhalb der heutigen Zonen/Potenzialflächen liegen. Also shown
// as a standalone map notice (see NoeMindestabstandNotice.svelte) whenever the
// viewport is zoomed into NÖ, independent of whether a region is selected.
export const NÖ_TURBINE_LEGACY_NOTE =
	'Der Mindestabstand von 1,2 km für Windräder gilt in Niederösterreich erst seit 2004. Daher können auf dieser Karte Windräder teilweise außerhalb der ausgewiesenen Zonen oder Potenzialflächen liegen, sofern sie bereits vor 2004 entsprechend gewidmet oder genehmigt wurden.';

const STEIERMARK_REVISION_NOTE =
	'Aktuell werden die Windkraft-Zonen in der Steiermark von der Landesregierung überarbeitet – es werden voraussichtlich sowohl neue Vorrang- und Eignungszonen als auch neue Ausschlusszonen hinzukommen.';

const KÄRNTEN_LEGAL_NOTE =
	'Kärnten hat aktuell weniger als 0,1 % der Landesfläche als Beschleunigungsgebiete ausgewiesen; über 99,9 % sind Ausschlusszonen. Weil die ausgewiesenen Beschleunigungsgebiete die gesetzlichen Ausbauziele nicht erreichen, sind Windräder jedoch grundsätzlich auch außerhalb dieser Zonen möglich (§ 4a UVP-G).';

function fmt(n: number): string {
	return n.toLocaleString('de-AT');
}

export function getStateId(region: Region): string | null {
	return region.parents?.find(p => p.layer === 'state')?.id
		?? (region.layer === 'state' ? region.id : null);
}

// ── State-specific text generators ───────────────────────────────────────────

function introNÖ(name: string, s: ZoneStats): RegionIntroContent {
	const hasZone = s.officialZoneCount > 0;
	const hasPotential = s.count > 0;
	const hasTurbines = s.turbineCount > 0;

	if (hasZone && hasTurbines) {
		return {
			paragraphs: [
				`In ${name} befindet sich eine Windkraftzone, in der bereits Windräder errichtet wurden. Bestehende Anlagen könnten in Zukunft modernisiert und durch leistungsstärkere Windräder ersetzt werden.`,
			],
			afterBullets: [NÖ_TURBINE_LEGACY_NOTE],
		};
	}
	if (hasZone) {
		return {
			paragraphs: [
				`In ${name} befindet sich eine Windkraftzone. Das bedeutet, dass das Land Niederösterreich diese Flächen grundsätzlich für Windkraft vorgesehen hat.`,
			],
		};
	}
	if (hasTurbines) {
		return {
			paragraphs: [
				`In ${name} befinden sich bereits Windräder. Bestehende Anlagen könnten in Zukunft modernisiert und durch leistungsstärkere Windräder ersetzt werden.`,
			],
			afterBullets: [NÖ_TURBINE_LEGACY_NOTE],
		};
	}
	if (!hasPotential) {
		return {
			paragraphs: [
				`In ${name} befindet sich derzeit keine Windkraftzone. Das Land Niederösterreich hat in dieser Gemeinde aktuell keine Flächen für Windkraft vorgesehen. Falls das Land Niederösterreich die Windkraft-Zonierung in den nächsten Jahren überarbeitet, könnte sich dies jedoch ändern.`,
			],
		};
	}
	return {
		paragraphs: [
			`In ${name} befindet sich derzeit keine Windkraftzone. Das Land Niederösterreich hat hier aktuell keine Flächen für Windkraft vorgesehen. Falls das Land Niederösterreich die Windkraft-Zonierung in den nächsten Jahren überarbeitet, könnte sich dies jedoch ändern. Laut Potenzialkarte besteht in ${name} grundsätzlich Potenzial für Windkraft.`,
		],
	};
}

function introPotentialOnly(name: string, hasPotential: boolean): RegionIntroContent {
	if (!hasPotential) {
		return {
			paragraphs: [
				`In ${name} besteht laut Potenzialkarte grundsätzlich wenig Potenzial für Windkraft. Ob hier nicht doch ein Windrad errichtet werden kann, hängt jedoch von der Detailprüfung ab:`,
			],
			bullets: DETAIL_BULLETS,
		};
	}
	return {
		paragraphs: [
			`In ${name} besteht laut Potenzialkarte grundsätzlich Potenzial für Windkraft. Ob hier tatsächlich ein Windrad errichtet werden kann, hängt jedoch von der Detailprüfung ab:`,
		],
		bullets: DETAIL_BULLETS,
	};
}

function introTirol(name: string, s: ZoneStats): RegionIntroContent {
	return introPotentialOnly(name, s.count > 0);
}

function introVorarlberg(name: string, s: ZoneStats): RegionIntroContent {
	return introPotentialOnly(name, s.count > 0);
}

function introOÖ(name: string, s: ZoneStats): RegionIntroContent {
	return {
		...introPotentialOnly(name, s.count > 0),
		afterBullets: [
			'Das Land Oberösterreich arbeitet aktuell an einer überörtlichen Raumplanung mit dem Ziel, drei verschiedene Zonen für Windkraft auszuweisen: Beschleunigungsgebiete, neutrale Gebiete und Ausschlussgebiete.',
		],
	};
}

function introSteiermark(name: string, s: ZoneStats): RegionIntroContent {
	const hasPotential = s.count > 0;
	const hasTurbines = s.turbineCount > 0;
	const zoneType: OfficialZoneType = s.officialZoneType;

	if (hasTurbines && (zoneType === 'vorrang' || zoneType === 'eignung')) {
		return {
			paragraphs: [
				`In ${name} befindet sich eine Windkraftzone, in der bereits Windräder errichtet wurden. Bestehende Anlagen könnten in Zukunft modernisiert und durch leistungsstärkere Windräder ersetzt werden.`,
			],
			afterBullets: [STEIERMARK_REVISION_NOTE],
		};
	}
	if (zoneType === 'vorrang') {
		return {
			paragraphs: [
				`In ${name} befindet sich eine sogenannte „Vorrangzone". Diese Flächen sind vom Land Steiermark vorrangig für die Errichtung von Windkraftanlagen vorgesehen. Das bedeutet, dass diese Zone als besonders geeignet gilt und daher vorrangig für die Entwicklung von Windparks vorgesehen ist.`,
			],
			afterBullets: [STEIERMARK_REVISION_NOTE],
		};
	}
	if (zoneType === 'eignung') {
		return {
			paragraphs: [
				`In ${name} befindet sich eine sogenannte „Eignungszone". Das bedeutet, dass das Land Steiermark diese Flächen grundsätzlich für Windkraft vorgesehen hat.`,
			],
			afterBullets: [STEIERMARK_REVISION_NOTE],
		};
	}
	if (zoneType === 'ausschluss' && !hasPotential) {
		return {
			paragraphs: [
				`In ${name} befindet sich eine Ausschlusszone. Das bedeutet, dass das Land Steiermark diese Flächen für Windkraft ausgeschlossen hat. Falls die Landesregierung die Windkraft-Zonierung in den nächsten Jahren überarbeitet, könnte sich dies jedoch ändern.`,
			],
			afterBullets: [STEIERMARK_REVISION_NOTE],
		};
	}
	if (zoneType === 'ausschluss') {
		return {
			paragraphs: [
				`${name} befindet sich derzeit in einer Ausschlusszone. Das bedeutet, dass das Land Steiermark diese Flächen für Windkraft ausgeschlossen hat. Falls die Landesregierung die Windkraft-Zonierung in den nächsten Jahren überarbeitet, könnte sich dies jedoch ändern. Laut Potenzialkarte besteht in ${name} grundsätzlich Potenzial für Windkraft.`,
			],
			afterBullets: [STEIERMARK_REVISION_NOTE],
		};
	}
	// No official zone (neutral)
	if (hasTurbines) {
		return {
			paragraphs: [
				`In ${name} befinden sich bereits Windräder. Bestehende Anlagen könnten in Zukunft modernisiert und durch leistungsstärkere Windräder ersetzt werden.`,
			],
			afterBullets: [STEIERMARK_REVISION_NOTE],
		};
	}
	const detailIntro = 'Ob hier ein Windrad errichtet werden kann, hängt von der Detailprüfung ab:';
	if (!hasPotential) {
		return {
			paragraphs: [
				`In ${name} befindet sich keine vom Land vorgesehene Fläche für den Windkraftausbau (sogenannte „Vorrang- oder Eignungszonen"). Das Land schließt den Bau für Windräder hier aber auch nicht aus.`,
				detailIntro,
			],
			bullets: DETAIL_BULLETS,
			afterBullets: [STEIERMARK_REVISION_NOTE],
		};
	}
	return {
		paragraphs: [
			`In ${name} befindet sich keine vom Land vorgesehene Fläche für den Windkraftausbau (sogenannte „Vorrang- oder Eignungszonen"). Das Land schließt den Bau für Windräder hier aber auch nicht aus. Laut Potenzialkarte besteht in ${name} grundsätzlich Potenzial für Windkraft.`,
			detailIntro,
		],
		bullets: DETAIL_BULLETS,
		afterBullets: [STEIERMARK_REVISION_NOTE],
	};
}

function introKärnten(name: string, s: ZoneStats): RegionIntroContent {
	const hasPotential = s.count > 0;
	const hasTurbines = s.turbineCount > 0;
	const zoneType: OfficialZoneType = s.officialZoneType;

	if (zoneType === 'positive' && hasTurbines) {
		return {
			paragraphs: [
				`In ${name} befindet sich eine der insgesamt 4 „Beschleunigungsgebiete" für Windkraft in Kärnten, in dem bereits Windräder errichtet wurden. Bestehende Anlagen könnten in Zukunft modernisiert und durch leistungsstärkere Windräder ersetzt oder neue, moderne Anlagen dazugebaut werden.`,
			],
			afterBullets: [KÄRNTEN_LEGAL_NOTE],
		};
	}
	if (zoneType === 'positive') {
		return {
			paragraphs: [
				`In ${name} befindet sich eine der insgesamt 4 „Beschleunigungsgebiete" für Windkraft in Kärnten. Diese machen weniger als 0,1 % der Landesfläche aus. 99,9 % der Kärntner Landesfläche sind Wind-Ausschlusszonen. Die Beschleunigungsgebiete sind vom Land Kärnten für die Errichtung von Windkraftanlagen vorgesehen. Das bedeutet, dass diese Zone als besonders geeignet gilt und daher für die Entwicklung von Windrädern vorgesehen ist.`,
			],
		};
	}
	if (zoneType === 'ausschluss' && !hasPotential) {
		return {
			paragraphs: [
				`${name} befindet sich derzeit in einer Ausschlusszone. Das bedeutet, dass das Land Kärnten diese Flächen für Windkraft ausgeschlossen hat. Falls das Land Kärnten die Windkraft-Zonierung in den nächsten Jahren überarbeitet, könnte sich dies jedoch ändern.`,
			],
			afterBullets: [KÄRNTEN_LEGAL_NOTE],
		};
	}
	if (zoneType === 'ausschluss') {
		return {
			paragraphs: [
				`${name} befindet sich derzeit in einer Ausschlusszone. Das bedeutet, dass das Land Kärnten diese Flächen für Windkraft ausgeschlossen hat. Falls das Land Kärnten die Windkraft-Zonierung in den nächsten Jahren überarbeitet, könnte sich dies jedoch ändern. Laut Potenzialkarte besteht in ${name} grundsätzlich Potenzial für Windkraft.`,
			],
			afterBullets: [KÄRNTEN_LEGAL_NOTE],
		};
	}
	// No zone data yet — fall through to generic default
	return genericDefault(name, s);
}

function introBurgenland(name: string, s: ZoneStats): RegionIntroContent {
	const hasZone = s.officialZoneCount > 0;
	const hasPotential = s.count > 0;
	const hasTurbines = s.turbineCount > 0;

	if (hasZone && hasTurbines) {
		return {
			paragraphs: [
				`In ${name} befindet sich eine Windkraftzone, in der bereits Windräder errichtet wurden. Bestehende Anlagen könnten in Zukunft modernisiert und durch leistungsstärkere Windräder ersetzt werden.`,
			],
		};
	}
	if (hasZone) {
		return {
			paragraphs: [
				`In ${name} befindet sich eine Windkraftzone. Das bedeutet, dass das Land Burgenland diese Flächen grundsätzlich für Windkraft vorgesehen hat.`,
			],
		};
	}
	if (hasTurbines) {
		return {
			paragraphs: [
				`In ${name} befinden sich bereits Windräder. Bestehende Anlagen könnten in Zukunft modernisiert und durch leistungsstärkere Windräder ersetzt werden.`,
			],
		};
	}
	if (!hasPotential) {
		return {
			paragraphs: [
				`In ${name} befindet sich derzeit keine Windkraftzone. Das Land Burgenland hat in dieser Gemeinde aktuell keine Flächen für Windkraft vorgesehen. Falls die Landesregierung die Windkraft-Zonierung in den nächsten Jahren überarbeitet, könnte sich dies ändern.`,
			],
		};
	}
	return {
		paragraphs: [
			`In ${name} befindet sich derzeit keine Windkraftzone. Das Land Burgenland hat hier aktuell keine Flächen für Windkraft vorgesehen. Falls die Landesregierung die Windkraft-Zonierung in den nächsten Jahren überarbeitet, könnte sich dies jedoch ändern. Laut Potenzialkarte besteht in ${name} grundsätzlich Potenzial für Windkraft.`,
		],
	};
}

function introSalzburg(name: string, s: ZoneStats): RegionIntroContent {
	const hasZone = s.officialZoneCount > 0;
	const hasPotential = s.count > 0;

	if (hasZone) {
		return {
			paragraphs: [
				`In ${name} befindet sich eine sogenannte Windkraft-„Vorrangzone". Die Errichtung von Windrädern soll gemäß der Raumordnung des Landes Salzburg bevorzugt in dieser Fläche stattfinden.`,
			],
		};
	}
	const detailIntro = 'Ein Windrad kann hier also unter Umständen möglich sein, abhängig von der Detailprüfung:';
	if (!hasPotential) {
		return {
			paragraphs: [
				`In ${name} befindet sich aktuell keine Windkraft-„Vorrangzone". Das bedeutet, dass das Land Salzburg diese Flächen weder aktiv eingeplant, noch kategorisch ausgeschlossen hat. ${detailIntro}`,
			],
			bullets: DETAIL_BULLETS,
		};
	}
	return {
		paragraphs: [
			`In ${name} befindet sich aktuell keine Windkraft-„Vorrangzone". Das bedeutet, dass das Land Salzburg diese Flächen weder aktiv eingeplant, noch kategorisch ausgeschlossen hat. Laut Potenzialkarte besteht in ${name} grundsätzlich Potenzial für Windkraft. ${detailIntro}`,
		],
		bullets: DETAIL_BULLETS,
	};
}

// ── Generic fallback (used by Wien, and by states with no zone data yet) ────

function genericDefault(name: string, s: ZoneStats): RegionIntroContent {
	if (s.count === 0) {
		return {
			paragraphs: [
				`In ${name} konnten nach den aktuellen Ausschlusskriterien keine potenziellen Windeignungsflächen identifiziert werden.`,
			],
		};
	}
	const parts: string[] = [
		`In ${name} gibt es ${fmt(s.count)} potenzielle Windeignungsflächen mit insgesamt ${fmt(s.totalAreaHa)} Hektar.`,
	];
	if (s.turbineCount > 0) {
		parts.push(`Bereits ${fmt(s.turbineCount)} ${s.turbineCount === 1 ? 'Windrad ist' : 'Windräder sind'} hier in Betrieb.`);
	}
	return { paragraphs: [parts.join(' ')] };
}

// ── Public API ────────────────────────────────────────────────────────────────

export function getRegionIntro(region: Region, stats: ZoneStats | null): RegionIntroContent {
	if (!stats) {
		return { paragraphs: [`Daten für ${region.name} werden geladen …`] };
	}

	const stateId = getStateId(region);

	if (stateId === STATE.NIEDERÖSTERREICH) return introNÖ(region.name, stats);
	if (stateId === STATE.TIROL)            return introTirol(region.name, stats);
	if (stateId === STATE.STEIERMARK)       return introSteiermark(region.name, stats);
	if (stateId === STATE.KÄRNTEN)          return introKärnten(region.name, stats);
	if (stateId === STATE.BURGENLAND)       return introBurgenland(region.name, stats);
	if (stateId === STATE.SALZBURG)         return introSalzburg(region.name, stats);
	if (stateId === STATE.VORARLBERG)       return introVorarlberg(region.name, stats);
	if (stateId === STATE.OBERÖSTERREICH)   return introOÖ(region.name, stats);

	return genericDefault(region.name, stats);
}
