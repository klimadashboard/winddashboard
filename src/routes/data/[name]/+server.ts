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
import zoneStats          from '../../../../geodata/zone_stats.json?url';
import regionStats        from '../../../../geodata/region_stats.json?url';

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
	zone_stats:         zoneStats,
	region_stats:       regionStats,
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
	const contentType = params.name === 'zone_stats' || params.name === 'region_stats'
		? 'application/json; charset=utf-8'
		: 'application/geo+json; charset=utf-8';

	return new Response(response.body, {
		headers: {
			'Content-Type':  contentType,
			'Cache-Control': 'private, max-age=3600',
		},
	});
};
