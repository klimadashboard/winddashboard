import type { RequestHandler } from './$types';

/**
 * robots.txt als Route statt als statische Datei.
 *
 * Grund: die `Sitemap:`-Zeile muss laut Spezifikation eine absolute URL
 * enthalten. Eine statische Datei müsste die Domain hartkodieren und wäre in
 * Preview-Deployments und nach einem Domainwechsel still falsch; hier kommt sie
 * aus der Request-Origin.
 */
export const GET: RequestHandler = async ({ url, setHeaders }) => {
	const body = `# Windkraft Österreich – Potenzialatlas

User-agent: *
Allow: /

# Datenendpunkte: reine GeoJSON-Auslieferung für die Karte, kein Seiteninhalt.
# Crawler würden hier zweistellige Megabytebeträge ziehen, ohne dass etwas
# Indexierbares dabei herauskommt.
Disallow: /data/

Sitemap: ${url.origin}/sitemap.xml
`;
	setHeaders({
		'Content-Type': 'text/plain; charset=utf-8',
		'Cache-Control': 'public, max-age=3600, s-maxage=3600'
	});
	return new Response(body);
};
