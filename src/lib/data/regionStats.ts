import type { Region, ZoneStats, OfficialZoneType } from '$lib/stores/windStore';

/**
 * Gemeinde-Kennzahlen aus geodata/region_stats.json.
 *
 * Die Zahlen wurden früher zur Laufzeit aus der Karte gelesen — mit
 * `queryRenderedFeatures` über die **Bounding Box** des Gemeindeumrisses.
 * Eine Box ist keine Gemeinde: Hausleiten bekam so die Windkraftzone der
 * Nachbargemeinde Rußbach zugeschrieben, und Gemeinden ohne eine einzige
 * Anlage wurden als "hier stehen bereits Windräder" beschrieben, weil eine
 * grenzüberschreitende Potenzialfläche ihren Anlagenzähler mitbrachte.
 *
 * Stattdessen wird jetzt eine vorberechnete Tabelle nachgeschlagen. Sie
 * entsteht in `scripts/build_region_stats.py` durch Verschneidung mit den
 * amtlichen Gemeindegrenzen der Statistik Austria. Damit hängen die Texte
 * nicht mehr von Zoomstufe, Kartenausschnitt oder geladenen Kacheln ab.
 */

interface PotentialEntry {
	count: number;
	areaHa: number;
	pd: number;
}

interface RegionEntry {
	name: string;
	turbines: number;
	bounds: [number, number, number, number];
	official?: { count: number; type: string | null; areaHa: number };
	potential: PotentialEntry;
}

export interface RegionStatsTable {
	generated: string;
	boundarySource: string;
	minShareHa: number;
	regions: Record<string, RegionEntry>;
}

let cache: Promise<RegionStatsTable | null> | null = null;

export function loadRegionStats(): Promise<RegionStatsTable | null> {
	cache ??= fetch('/data/region_stats')
		.then((r) => (r.ok ? (r.json() as Promise<RegionStatsTable>) : null))
		.catch(() => null);
	return cache;
}

/**
 * Die Gemeindekennziffern, aus denen sich eine Region zusammensetzt.
 *
 * Die GKZ ist hierarchisch aufgebaut: die erste Stelle ist das Bundesland,
 * die ersten drei Stellen der politische Bezirk. Eine Region der Ebene
 * "district" umfasst damit alle GKZ mit ihrem Code als Präfix — deshalb
 * genügt ein Präfixvergleich, um Bezirke und Bundesländer zu aggregieren.
 */
function matchingGkz(region: Region, table: RegionStatsTable): string[] {
	const code = String(region.code ?? '').trim();
	if (!code) return [];
	const all = Object.keys(table.regions);

	if (region.layer === 'municipality') {
		return all.includes(code) ? [code] : [];
	}
	// Wien ist zugleich Gemeinde und Bundesland: die GKZ 900 existiert als
	// Gemeinde, die Bezirke 901–923 sind Zählbezirke ohne eigene GKZ-Zeile.
	// Der Präfixvergleich deckt beide Fälle ab.
	return all.filter((gkz) => gkz.startsWith(code));
}

function normalizeZoneType(raw: string | null | undefined): OfficialZoneType {
	if (raw === 'ausschluss') return 'ausschluss';
	if (raw === 'vorrang') return 'vorrang';
	if (raw === 'eignung') return 'eignung';
	if (raw) return 'positive';
	return null;
}

/**
 * Fasst die Kennzahlen einer Region zusammen. `null`, wenn die Region in der
 * Tabelle nicht vorkommt — dann bleibt der bisherige Ladezustand bestehen,
 * statt fälschlich "keine Flächen" zu behaupten.
 */
export function statsForRegion(
	region: Region,
	table: RegionStatsTable | null,
): ZoneStats | null {
	if (!table) return null;
	const gkz = matchingGkz(region, table);
	if (gkz.length === 0) return null;

	let count = 0;
	let totalAreaHa = 0;
	let pdWeighted = 0;
	let turbineCount = 0;
	let officialZoneCount = 0;
	const zoneTypes: OfficialZoneType[] = [];

	for (const id of gkz) {
		const entry = table.regions[id];
		if (!entry) continue;
		const p = entry.potential;
		if (p) {
			count += p.count;
			totalAreaHa += p.areaHa;
			pdWeighted += p.pd * p.areaHa;
		}
		turbineCount += entry.turbines;
		if (entry.official) {
			officialZoneCount += entry.official.count;
			zoneTypes.push(normalizeZoneType(entry.official.type));
		}
	}

	// Bei mehreren Gemeinden (Bezirk, Bundesland) gewinnt die konkretere
	// positive Ausweisung — eine Vorrangzone im Bezirk ist die relevantere
	// Aussage als eine Ausschlusszone in einer anderen Gemeinde desselben.
	const priority: OfficialZoneType[] = ['vorrang', 'eignung', 'positive', 'ausschluss'];
	const officialZoneType = priority.find((t) => zoneTypes.includes(t)) ?? null;

	return {
		count,
		totalAreaHa: Math.round(totalAreaHa),
		meanPdWm2: totalAreaHa > 0 ? Math.round(pdWeighted / totalAreaHa) : 0,
		turbineCount,
		officialZoneCount,
		officialZoneType,
	};
}

/**
 * Der korrekt verortete Umriss-Rahmen einer Region, aus denselben amtlichen
 * Grenzen. Die `outline`-Geometrie der Regions-API war bis 8.9.2026 einheitlich
 * rund 208 m nach Westen und 78 m nach Norden versetzt (MGI → WGS84 ohne
 * Datumstransformation); seit der Korrektur in Directus stimmt sie. Die Tabelle
 * bleibt trotzdem die Quelle: sie kommt aus derselben amtlichen Lieferung, ist
 * nicht für den Transport vereinfacht und liegt schon vor dem Kartenaufbau vor.
 */
export function boundsForRegion(
	region: Region,
	table: RegionStatsTable | null,
): [number, number, number, number] | null {
	if (!table) return null;
	const gkz = matchingGkz(region, table);
	if (gkz.length === 0) return null;

	let minLon = Infinity, minLat = Infinity, maxLon = -Infinity, maxLat = -Infinity;
	for (const id of gkz) {
		const b = table.regions[id]?.bounds;
		if (!b) continue;
		if (b[0] < minLon) minLon = b[0];
		if (b[1] < minLat) minLat = b[1];
		if (b[2] > maxLon) maxLon = b[2];
		if (b[3] > maxLat) maxLat = b[3];
	}
	return Number.isFinite(minLon) ? [minLon, minLat, maxLon, maxLat] : null;
}
