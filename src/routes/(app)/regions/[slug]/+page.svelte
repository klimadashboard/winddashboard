<script lang="ts">
	import { selectedRegion } from '$lib/stores/windStore';
	import SeoHead from '$lib/components/SeoHead.svelte';

	let { data } = $props();

	$effect(() => {
		if (data.region) selectedRegion.set(data.region);
	});

	// Eigener Titel je Region. Ohne das teilen sich alle 2.116 Gemeindeseiten
	// den Titel des Root-Layouts — für Suchmaschinen 2.116 Duplikate, und
	// "Windkraft <Gemeinde>" ist genau die Suche, für die diese Seiten da sind.
	const region = $derived(data.region);
	const title = $derived(
		region
			? `Windkraft in ${region.name}: Zonen und Potenzialflächen`
			: 'Region nicht gefunden – Windkraft Österreich'
	);
	const description = $derived(
		region
			? `Wo in ${region.name} Windräder möglich sind: ausgewiesene Windkraftzonen, ` +
				`Potenzialflächen, geltende Mindestabstände und bereits bestehende Anlagen ` +
				`auf der interaktiven Karte.`
			: 'Diese Region konnte nicht geladen werden.'
	);
</script>

<SeoHead {title} {description} type="article" />
