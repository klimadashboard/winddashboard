/**
 * Rybbit-Ereignisse (analytics.klimadashboard.org), wie in klimadashboard-core.
 *
 * Seitenaufrufe zählt das Skript selbst, auch die clientseitigen Wechsel über
 * `goto()` — jede Region erscheint dort also als eigener Pfad `/regions/<slug>`.
 * Die Ereignisse hier ergänzen, was der Pfad nicht verrät:
 *
 *   - `Region Select`  { region, slug, layer, source }
 *       source = "map" (Klick in die Karte) oder "search" (Suchfeld).
 *       Direkteinstiege über einen Link sind normale Seitenaufrufe.
 *   - `Region Reset`   { from }   zurück zur Österreich-Ansicht
 *   - `Search No Results` { query }  Suchbegriffe ohne Treffer
 *   - `Story Exit`     { step, finished }  wo die Story verlassen wurde
 *   - `Story Replay`   Story über den Knopf im Inspector neu gestartet
 *
 * Ohne geladenes Skript (lokal, Werbeblocker) passiert nichts.
 */
import type { Region } from '$lib/stores/windStore';

declare global {
	interface Window {
		rybbit?: {
			event: (name: string, properties?: Record<string, string | number>) => void;
		};
	}
}

export const RYBBIT_SITE_ID = 'e07dacb55c71';

export function track(name: string, properties?: Record<string, string | number>) {
	try {
		window.rybbit?.event(name, properties);
	} catch {
		// Analyse darf die Seite nie stören.
	}
}

export function trackRegionSelect(region: Region, source: 'map' | 'search') {
	track('Region Select', {
		region: region.name.trim(),
		slug: region.slug,
		layer: region.layer,
		source
	});
}
