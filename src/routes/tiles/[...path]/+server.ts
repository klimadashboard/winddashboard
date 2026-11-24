import { error } from '@sveltejs/kit';
import { TILE_ORIGIN } from '$lib/config/tiles';
import type { RequestHandler } from './$types';

/**
 * Kachel-Proxy vor dem Kachelserver, damit Vercels CDN die Kacheln vorhält.
 * Warum, steht bei TILE_SERVER_BASE in config/tiles.ts.
 *
 * Nur die Kachelsätze dieser Karte und nur Kachelpfade, kein offener Proxy
 * auf den ganzen Server. Die Daten werden damit nicht weitergegeben, nur
 * dieselben Kacheln wie bisher unter anderer Adresse ausgeliefert.
 */
const ALLOWED = /^data\/(windkraft_[a-z0-9_]+|municipalities-at)\/\d{1,2}\/\d{1,6}\/\d{1,6}\.(pbf|png)$/;

const ON_WORKERS = typeof navigator !== 'undefined' && navigator.userAgent === 'Cloudflare-Workers';

// Browser eine Stunde, CDN eine Woche. Ein neues Deployment leert den
// CDN-Cache ohnehin; neue Daten bekommen bisher auch neue Kachelsatz-IDs.
const CACHE = 'public, max-age=3600, s-maxage=604800, stale-while-revalidate=86400';

export const GET: RequestHandler = async ({ params }) => {
	const path = params.path;
	if (!ALLOWED.test(path)) error(404, 'Not found');

	let upstream: Response;
	try {
		// Globales fetch, nicht das von SvelteKit: es geht an einen fremden Host.
		upstream = await fetch(`${TILE_ORIGIN}/${path}`, { signal: AbortSignal.timeout(10_000) });
	} catch {
		return new Response(null, { status: 504, headers: { 'cache-control': 'no-store' } });
	}

	const isPbf = path.endsWith('.pbf');

	// 204 = leere Kachel. Für Vektorkacheln als leere 200 weitergeben, damit
	// das CDN sie sicher zwischenspeichert; MapLibre liest einen leeren Puffer
	// als leere Kachel. Rasterkacheln bleiben 204 (ein leeres PNG wäre kaputt).
	if (upstream.status === 204 || upstream.status === 404) {
		return new Response(null, {
			status: isPbf ? 200 : upstream.status,
			headers: { 'cache-control': CACHE, 'content-type': isPbf ? 'application/x-protobuf' : 'image/png' }
		});
	}
	if (!upstream.ok) {
		return new Response(null, { status: 502, headers: { 'cache-control': 'no-store' } });
	}

	let body = new Uint8Array(await upstream.arrayBuffer());
	const headers: Record<string, string> = {
		'cache-control': CACHE,
		'content-type': isPbf ? 'application/x-protobuf' : 'image/png',
		'access-control-allow-origin': '*'
	};
	if (!isPbf) return new Response(body, { headers });

	// Ob die gzip-Kodierung des Kachelservers hier noch drauf ist, hängt an
	// der Laufzeit (Node entpackt beim fetch, Workers nicht immer). Darum an
	// den Bytes prüfen und auf die rohe Kachel bringen.
	if (body[0] === 0x1f && body[1] === 0x8b) {
		const raw = new Blob([body]).stream().pipeThrough(new DecompressionStream('gzip'));
		body = new Uint8Array(await new Response(raw).arrayBuffer());
	}

	// Auf Workers roh und ohne Content-Encoding: Cloudflare komprimiert für
	// den Client selbst. Mit gesetztem Content-Encoding legte der Cache von
	// adapter-cloudflare die gepackte Fassung ab und packte sie beim nächsten
	// Treffer noch einmal — MapLibre bekam doppelt gepackte Kacheln.
	if (ON_WORKERS) return new Response(body, { headers });
	headers['content-encoding'] = 'gzip';
	const gz = new Blob([body]).stream().pipeThrough(new CompressionStream('gzip'));
	return new Response(gz, { headers });
};
