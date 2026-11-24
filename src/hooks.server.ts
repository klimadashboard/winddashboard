import type { Handle } from '@sveltejs/kit';
import { version } from '$app/environment';

/**
 * Seiten im CDN zwischenspeichern.
 *
 * Ohne das rendert jede Seite bei jedem Aufruf neu, und jede Gemeindeseite
 * fragt dabei die Regions-API (base.klimadashboard.org) ab. Der Inhalt hängt
 * nur an der URL und am Deployment, nicht am Besucher. Eine Stunde frisch.
 *
 * Vercel: liest `s-maxage` selbst und leert seinen Cache bei jedem
 * Deployment.
 *
 * Cloudflare Workers: Der Worker läuft vor dem CDN, gecacht wird über die
 * Cache-API. Der Schlüssel enthält die Build-Version — ein neues Deployment
 * löscht die alten JS-Dateien, und eine HTML-Seite aus dem alten Build würde
 * dann nicht mehr hydrieren. adapter-cloudflare legt zusätzlich jede Antwort
 * ohne private/no-cache/no-store unter der blanken URL ab (also ohne
 * Version); deshalb geht die Seite selbst mit `no-cache` hinaus und nur die
 * Kopie im versionierten Cache trägt `s-maxage`. Für Browser ist `no-cache`
 * dasselbe wie bisher `max-age=0`: vor Gebrauch nachfragen.
 *
 * Antworten, die ihre Cache-Regeln selbst setzen (Kachel-Proxy, Sitemap),
 * und Fehlerseiten bleiben unberührt.
 */
const PAGE_CACHE = 'public, max-age=0, s-maxage=3600, stale-while-revalidate=86400';
const EDGE_TTL = 'public, s-maxage=3600';
const BROWSER_ON_WORKERS = 'public, no-cache';

type CfPlatform = {
	caches?: { default?: Cache };
	context?: { waitUntil(p: Promise<unknown>): void };
};

export const handle: Handle = async ({ event, resolve }) => {
	const platform = event.platform as CfPlatform | undefined;
	const edgeCache = platform?.caches?.default;
	const isGet = event.request.method === 'GET';

	if (!edgeCache) {
		const response = await resolve(event);
		if (isGet && response.status === 200 && !response.headers.has('cache-control')) {
			response.headers.set('cache-control', PAGE_CACHE);
		}
		return response;
	}

	// ── Cloudflare Workers ──
	const url = new URL(event.url);
	url.searchParams.set('__v', version);
	const key = new Request(url.toString(), { method: 'GET' });

	if (isGet) {
		const hit = await edgeCache.match(key);
		if (hit) {
			const res = new Response(hit.body, hit);
			res.headers.set('cache-control', BROWSER_ON_WORKERS);
			return res;
		}
	}

	const response = await resolve(event);
	if (isGet && response.status === 200 && !response.headers.has('cache-control')) {
		const copy = new Response(response.clone().body, response);
		copy.headers.set('cache-control', EDGE_TTL);
		platform?.context?.waitUntil(edgeCache.put(key, copy));
		response.headers.set('cache-control', BROWSER_ON_WORKERS);
	}
	return response;
};
