import type { Handle } from '@sveltejs/kit';

/**
 * Seiten im CDN zwischenspeichern.
 *
 * Ohne das rendert Vercel jede Seite bei jedem Aufruf neu, und jede
 * Gemeindeseite fragt dabei die Regions-API (base.klimadashboard.org) ab.
 * Der Inhalt hängt nur an der URL und am Deployment, nicht am Besucher; ein
 * neues Deployment leert den CDN-Cache. Eine Stunde frisch, danach liefert
 * das CDN noch einen Tag lang die alte Fassung sofort aus und rendert im
 * Hintergrund neu.
 *
 * Antworten, die ihre Cache-Regeln selbst setzen (Kachel-Proxy, Sitemap),
 * und Fehlerseiten bleiben unberührt.
 */
const PAGE_CACHE = 'public, max-age=0, s-maxage=3600, stale-while-revalidate=86400';

export const handle: Handle = async ({ event, resolve }) => {
	const response = await resolve(event);
	if (
		event.request.method === 'GET' &&
		response.status === 200 &&
		!response.headers.has('cache-control')
	) {
		response.headers.set('cache-control', PAGE_CACHE);
	}
	return response;
};
