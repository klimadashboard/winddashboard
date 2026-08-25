import type { Region } from '$lib/stores/windStore';

export const ssr = false;
export const prerender = false;

export async function load({ params }): Promise<{ region: Region | null }> {
	const fields = 'id,name,code,layer,layer_label,postcodes,center,outline,parents';
	const res = await fetch(
		`https://base.klimadashboard.org/items/regions/${params.id}?fields=${fields}`
	);
	if (!res.ok) return { region: null };
	const json = await res.json();
	return { region: (json.data as Region) ?? null };
}
