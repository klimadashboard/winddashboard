import { read } from '$app/server';
import { error } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

// Import each file as a Vite asset URL.
// `?url` tells Vite to treat the file as a static asset (not parse it as JSON),
// returning a URL string. `read()` from $app/server then retrieves the content
// at runtime — bundled with the server function on Vercel, never exposed as a
// public static URL.
import possibleZones      from '../../../../geodata/possible_zones.geojson?url';
import officialZoning     from '../../../../geodata/official_zoning.geojson?url';
import existingTurbines   from '../../../../geodata/existing_turbines.geojson?url';
import austriaOutline     from '../../../../geodata/austria_outline.geojson?url';
import zoneCentroids      from '../../../../geodata/zone_centroids.geojson?url';
import exclusionSchutz    from '../../../../geodata/exclusion_schutz.geojson?url';
import exclusionSiedlung  from '../../../../geodata/exclusion_siedlung.geojson?url';
import exclusionSonstige  from '../../../../geodata/exclusion_sonstige.geojson?url';
import exclusionWind      from '../../../../geodata/exclusion_wind.geojson?url';
import variantStats       from '../../../../geodata/variant_stats.json?url';

// Settlement-distance variants (interactive slider) — see src/lib/config/variants.ts
// "default" has no separate file — possible_zones.geojson/zone_centroids.geojson
// already ARE the default variant (extract_possible_zones.py writes them
// unsuffixed for exactly this reason), so both names below alias the same asset
// instead of duplicating ~15 MB of identical content.
import possibleZones800      from '../../../../geodata/possible_zones_800.geojson?url';
import possibleZones1000     from '../../../../geodata/possible_zones_1000.geojson?url';
import possibleZones1200     from '../../../../geodata/possible_zones_1200.geojson?url';
import possibleZones1500     from '../../../../geodata/possible_zones_1500.geojson?url';
import possibleZones2000     from '../../../../geodata/possible_zones_2000.geojson?url';
import zoneCentroids800      from '../../../../geodata/zone_centroids_800.geojson?url';
import zoneCentroids1000     from '../../../../geodata/zone_centroids_1000.geojson?url';
import zoneCentroids1200     from '../../../../geodata/zone_centroids_1200.geojson?url';
import zoneCentroids1500     from '../../../../geodata/zone_centroids_1500.geojson?url';
import zoneCentroids2000     from '../../../../geodata/zone_centroids_2000.geojson?url';

const FILES: Record<string, string> = {
	possible_zones:     possibleZones,
	official_zoning:    officialZoning,
	existing_turbines:  existingTurbines,
	austria_outline:    austriaOutline,
	zone_centroids:     zoneCentroids,
	exclusion_schutz:   exclusionSchutz,
	exclusion_siedlung: exclusionSiedlung,
	exclusion_sonstige: exclusionSonstige,
	exclusion_wind:     exclusionWind,
	variant_stats:      variantStats,

	possible_zones_default: possibleZones,
	possible_zones_800:     possibleZones800,
	possible_zones_1000:    possibleZones1000,
	possible_zones_1200:    possibleZones1200,
	possible_zones_1500:    possibleZones1500,
	possible_zones_2000:    possibleZones2000,
	zone_centroids_default: zoneCentroids,
	zone_centroids_800:     zoneCentroids800,
	zone_centroids_1000:    zoneCentroids1000,
	zone_centroids_1200:    zoneCentroids1200,
	zone_centroids_1500:    zoneCentroids1500,
	zone_centroids_2000:    zoneCentroids2000,
	// Band-layer GeoJSONs removed — detail view now uses vector tiles served by TileServer GL.
	// See scripts/raster/windkraft_exclusion_bands.mbtiles and PIPELINE.md §6.
};

export const GET: RequestHandler = async ({ params, request }) => {
	const assetUrl = FILES[params.name];

	if (!assetUrl) {
		throw error(404, 'Not found');
	}

	// Block cross-origin fetches (hotlinking from other domains).
	const origin = request.headers.get('origin');
	const host   = request.headers.get('host') ?? '';
	if (origin && !origin.includes(host.split(':')[0])) {
		throw error(403, 'Forbidden');
	}

	const response = read(assetUrl);
	const contentType = params.name === 'variant_stats'
		? 'application/json; charset=utf-8'
		: 'application/geo+json; charset=utf-8';

	return new Response(response.body, {
		headers: {
			'Content-Type':  contentType,
			'Cache-Control': 'private, max-age=3600',
		},
	});
};
