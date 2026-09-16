import type { RequestHandler } from './$types';

/**
 * Sitemap über alle Gemeinde- und Bezirksseiten.
 *
 * Die Gemeindeseiten sind der eigentliche Suchmaschinen-Einstieg — jemand sucht
 * "Windkraft <Gemeindename>", nicht "Potenzialatlas". Ohne Sitemap findet ein
 * Crawler sie praktisch nicht: sie sind nirgends verlinkt, sondern nur über die
 * Suche erreichbar, und die läuft über JavaScript.
 *
 * Die Liste kommt zur Laufzeit aus der Regions-API und wird eine Stunde
 * gecacht — die Regionen ändern sich selten, aber ein fixes Einbacken zur
 * Bauzeit würde bei jedem Gemeindezusammenschluss stillschweigend veralten.
 */

const REGIONS_API = 'https://base.klimadashboard.org/items/regions';
const CACHE_SECONDS = 3600;

interface RegionRow {
	slug: string;
	layer: string;
}

function escapeXml(value: string): string {
	return value.replace(/[<>&'"]/g, (c) =>
		({ '<': '&lt;', '>': '&gt;', '&': '&amp;', "'": '&apos;', '"': '&quot;' })[c] as string
	);
}

async function fetchRegions(fetcher: typeof fetch): Promise<RegionRow[]> {
	const params = new URLSearchParams({
		'filter[country][_eq]': 'AT',
		'filter[layer][_in]': 'municipality,district',
		fields: 'slug,layer',
		limit: '-1'
	});
	const res = await fetcher(`${REGIONS_API}?${params}`);
	if (!res.ok) return [];
	const json = await res.json();
	return (json.data as RegionRow[]) ?? [];
}

export const GET: RequestHandler = async ({ url, fetch, setHeaders }) => {
	const origin = url.origin;
	const today = new Date().toISOString().slice(0, 10);

	// Feste Seiten zuerst, dann die Regionen. Bezirke bekommen eine etwas
	// höhere Priorität als Gemeinden, weil sie mehr Fläche abdecken.
	const entries: Array<{ loc: string; priority: string; changefreq: string }> = [
		{ loc: `${origin}/`, priority: '1.0', changefreq: 'weekly' },
		{ loc: `${origin}/methodik`, priority: '0.6', changefreq: 'monthly' }
	];

	// Ein Slug ist doppelt vergeben (`wien` als Gemeinde und als Bezirk) — in der
	// Sitemap darf dieselbe URL nur einmal stehen.
	const seen = new Set<string>();
	for (const region of await fetchRegions(fetch)) {
		if (!region.slug || seen.has(region.slug)) continue;
		seen.add(region.slug);
		entries.push({
			loc: `${origin}/regions/${region.slug}`,
			priority: region.layer === 'district' ? '0.7' : '0.5',
			changefreq: 'monthly'
		});
	}

	const body =
		'<?xml version="1.0" encoding="UTF-8"?>\n' +
		'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
		entries
			.map(
				(e) =>
					`\t<url>\n` +
					`\t\t<loc>${escapeXml(e.loc)}</loc>\n` +
					`\t\t<lastmod>${today}</lastmod>\n` +
					`\t\t<changefreq>${e.changefreq}</changefreq>\n` +
					`\t\t<priority>${e.priority}</priority>\n` +
					`\t</url>`
			)
			.join('\n') +
		'\n</urlset>\n';

	setHeaders({
		'Content-Type': 'application/xml; charset=utf-8',
		'Cache-Control': `public, max-age=${CACHE_SECONDS}, s-maxage=${CACHE_SECONDS}`
	});
	return new Response(body);
};
