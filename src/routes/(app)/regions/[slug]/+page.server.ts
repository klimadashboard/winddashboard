import { error, redirect } from '@sveltejs/kit';
import { statsForRegion } from '$lib/data/regionStats';
import { regionStatsTable } from '$lib/server/regionStatsTable';
import type { Region, ZoneStats } from '$lib/stores/windStore';
import type { EntryGenerator, PageServerLoad } from './$types';

/**
 * Alle Regionsseiten werden beim Build vorgerendert: als fertiges HTML plus
 * `__data.json` für die Navigation im Browser.
 *
 * Warum: Auf Cloudflare Workers (Free) darf eine Anfrage 10 ms CPU brauchen.
 * Ein warmes Rendern braucht ~1 ms, aber bei wenig Verkehr trifft fast jede
 * Anfrage eine frisch gestartete Worker-Instanz — gemessen 8 ms im Median und
 * bis 26 ms. Vorgerenderte Seiten liefert Cloudflare als statische Dateien aus:
 * kein Worker, keine CPU, kein Tageslimit, kostenlos und am schnellsten.
 *
 * `prerender = 'auto'`: Die Liste aus `entries` wird vorgerendert, alles andere
 * (alte UUID-Links, Tippfehler, neu angelegte Regionen bis zum nächsten Build)
 * rendert weiterhin der Server zur Laufzeit.
 *
 * Folge: Ändert sich eine Region in Directus oder die Kennzahlentabelle,
 * braucht es einen neuen Build. Beides ändert sich nur mit neuen Lieferungen.
 */
export const ssr = true;
export const prerender = 'auto';

const API = 'https://base.klimadashboard.org/items/regions';
const FIELDS = 'id,name,slug,code,layer,layer_label,postcodes,center,outline,parents';

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/** Alle Slugs Österreichs (Gemeinden, Bezirke, Bundesländer) zum Vorrendern. */
export const entries: EntryGenerator = async () => {
	const params = new URLSearchParams({
		'filter[country][_eq]': 'AT',
		'filter[layer][_in]': 'municipality,district,state',
		fields: 'slug',
		limit: '-1'
	});
	const res = await fetch(`${API}?${params}`);
	// Lieber laut scheitern als stillschweigend ohne Regionsseiten bauen.
	if (!res.ok) throw new Error(`Regions-API für prerender: HTTP ${res.status}`);
	const rows = ((await res.json()).data ?? []) as Array<{ slug: string | null }>;
	const slugs = [...new Set(rows.map((r) => r.slug).filter((s): s is string => !!s))];
	if (slugs.length < 2000) throw new Error(`Regions-API lieferte nur ${slugs.length} Slugs`);
	return slugs.map((slug) => ({ slug }));
};

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

export const load: PageServerLoad = async ({
	params,
	fetch
}): Promise<{ region: Region; stats: ZoneStats | null }> => {
	const key = params.slug;

	// Alte UUID-Links bleiben gültig und werden dauerhaft auf den Slug
	// umgeleitet. Ohne die Umleitung wären geteilte Links tot und Suchmaschinen
	// hätten zwei URLs für denselben Inhalt.
	if (UUID.test(key)) {
		const byId = pickRegion(await fetchBy(fetch, 'id', key));
		if (byId?.slug) redirect(301, `/regions/${byId.slug}`);
		error(404, 'Diese Region gibt es nicht.');
	}

	const region = pickRegion(await fetchBy(fetch, 'slug', key));
	// Unbekannte Region als echten 404 melden, nicht als leere Seite mit Status
	// 200: sonst indexieren Suchmaschinen beliebig viele URL-Varianten als
	// vermeintlich gültige Seiten, die alle denselben Startseiteninhalt zeigen.
	if (!region) error(404, 'Diese Region gibt es nicht.');

	// Kennzahlen gleich mit, damit der Einleitungstext im HTML steht. Ohne das
	// indexieren Suchmaschinen auf jeder Gemeindeseite den Platzhalter
	// "Daten werden geladen …" statt der eigentlichen Aussage.
	const stats = statsForRegion(region, regionStatsTable);

	return { region, stats };
};
