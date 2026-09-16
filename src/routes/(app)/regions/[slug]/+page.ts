import { error, redirect } from '@sveltejs/kit';
import { statsForRegion, type RegionStatsTable } from '$lib/data/regionStats';
import type { Region, ZoneStats } from '$lib/stores/windStore';

// SSR an, damit Titel, Beschreibung, Social-Karte und der eigentliche
// Gemeindetext schon im ausgelieferten HTML stehen. Die Karte selbst bleibt
// clientseitig (im Layout hinter `browser` abgeschirmt).
export const ssr = true;
export const prerender = false;

const API = 'https://base.klimadashboard.org/items/regions';
const FIELDS = 'id,name,slug,code,layer,layer_label,postcodes,center,outline,parents';

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/**
 * Genau ein Slug in Österreich ist doppelt vergeben: `wien` gibt es als Gemeinde
 * (GKZ 90001) und als Bezirk (GKZ 900, im Datensatz mit angehängtem Leerzeichen
 * im Namen). Beide meinen dieselbe Stadt. Damit dieselbe URL immer denselben
 * Datensatz liefert, gewinnt die Gemeinde — sonst hinge es an der Sortierreihen-
 * folge der API, welche Seite ausgeliefert wird.
 */
function pickRegion(rows: Region[]): Region | null {
	if (rows.length <= 1) return rows[0] ?? null;
	return rows.find((r) => r.layer === 'municipality') ?? rows[0];
}

async function fetchBy(
	fetcher: typeof fetch,
	field: 'slug' | 'id',
	value: string
): Promise<Region[]> {
	const params = new URLSearchParams({
		'filter[country][_eq]': 'AT',
		[`filter[${field}][_eq]`]: value,
		fields: FIELDS,
		limit: '5'
	});
	const res = await fetcher(`${API}?${params}`);
	if (!res.ok) return [];
	const json = await res.json();
	return (json.data as Region[]) ?? [];
}

export async function load({
	params,
	fetch
}): Promise<{ region: Region; stats: ZoneStats | null }> {
	const key = params.slug;

	// Alte UUID-Links bleiben gültig und werden dauerhaft auf den Slug
	// umgeleitet. Ohne die Umleitung wären geteilte Links tot und Suchmaschinen
	// hätten zwei URLs für denselben Inhalt.
	if (UUID.test(key)) {
		const byId = pickRegion(await fetchBy(fetch, 'id', key));
		if (byId?.slug) throw redirect(301, `/regions/${byId.slug}`);
		throw error(404, 'Diese Region gibt es nicht.');
	}

	const region = pickRegion(await fetchBy(fetch, 'slug', key));
	// Unbekannte Region als echten 404 melden, nicht als leere Seite mit Status
	// 200: sonst indexieren Suchmaschinen beliebig viele URL-Varianten als
	// vermeintlich gültige Seiten, die alle denselben Startseiteninhalt zeigen.
	if (!region) throw error(404, 'Diese Region gibt es nicht.');

	// Kennzahlen gleich mitladen, damit der Einleitungstext serverseitig steht.
	// Ohne das indexieren Suchmaschinen auf jeder der 2.116 Gemeindeseiten den
	// Platzhalter "Daten werden geladen …" statt der eigentlichen Aussage.
	// Schlägt es fehl, bleibt es beim Ladezustand — der Client holt es ohnehin.
	let stats: ZoneStats | null = null;
	try {
		const statsRes = await fetch('/data/region_stats.json');
		if (statsRes.ok) {
			stats = statsForRegion(region, (await statsRes.json()) as RegionStatsTable);
		}
	} catch {
		stats = null;
	}

	return { region, stats };
}
