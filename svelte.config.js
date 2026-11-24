import vercel from '@sveltejs/adapter-vercel';
import cloudflare from '@sveltejs/adapter-cloudflare';

/**
 * Hosting: Cloudflare Workers (wrangler.jsonc), Umzug von Vercel am 24.11.2026.
 *
 * Grund: Auf Vercel Hobby wäre nach rund 5.000–8.000 Besuchen im Monat
 * Schluss gewesen (1 Mio. CDN-Anfragen, ~125 je Besuch) und die Seite dann
 * 30 Tage gesperrt. Bei Cloudflare sind statische Dateien und Datenübertragung
 * frei; nur der Seitenaufruf selbst startet den Worker.
 *
 * Solange Vercel noch baut (Umstellungsphase), wählt die Umgebungsvariable
 * VERCEL dort weiter den Vercel-Adapter. Danach kann der Zweig weg.
 */
const adapter = process.env.VERCEL
	? // Frankfurt statt Washington (iad1): Publikum, Regions-API und
		// Kachelserver sitzen in Europa.
		vercel({ regions: ['fra1'] })
	: cloudflare();

/** @type {import('@sveltejs/kit').Config} */
const config = {
	compilerOptions: {
		// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
		runes: ({ filename }) => (filename.split(/[/\\]/).includes('node_modules') ? undefined : true)
	},
	kit: { adapter }
};

export default config;
