import type { RegionStatsTable } from '$lib/data/regionStats';
// Dieselbe Datei, die unter /data/region_stats.json ausgeliefert wird
// (scripts/stage_static_data.py kopiert sie vor jedem Build dorthin).
import table from '../../../static/data/region_stats.json';

/**
 * Die Kennzahlentabelle für das Server-Rendering, mit in den Build gepackt.
 *
 * Vorher wurde sie zur Laufzeit per fetch geholt: Auf Vercel ging das, auf
 * Cloudflare Workers zählt aber jede Millisekunde CPU (Free: 10 ms je Anfrage),
 * und beim Vorrendern (prerender) gibt es keinen laufenden Server, von dem man
 * sie holen könnte. Die Datei ist öffentlich; sie im Server-Bundle zu haben,
 * gibt nichts preis.
 */
export const regionStatsTable = table as unknown as RegionStatsTable;
