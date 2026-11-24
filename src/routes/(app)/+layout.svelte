<script lang="ts">
	import Map from "$lib/components/Map.svelte";
	import WindParticles from "$lib/components/WindParticles.svelte";
	import DotGrid from "$lib/components/DotGrid.svelte";
	import MapTooltip from "$lib/components/MapTooltip.svelte";
	import Inspector from "$lib/components/Inspector.svelte";
	import SiteFooter from "$lib/components/SiteFooter.svelte";
	import HexbinOverlay from "$lib/components/HexbinOverlay.svelte";
	import MapControlPanel from "$lib/components/MapControlPanel.svelte";
	import NoeMindestabstandNotice from "$lib/components/NoeMindestabstandNotice.svelte";
	import Scrollytelling from "$lib/components/Scrollytelling.svelte";
	import SearchBar from "$lib/components/SearchBar.svelte";
	import { vizMode, storyComplete, selectedRegion, zoneStats } from "$lib/stores/windStore";
	import { browser } from "$app/environment";
	import { onMount } from "svelte";
	import { page } from "$app/stores";
	import type { HoverInfo } from "$lib/components/Map.svelte";

	let { children } = $props();
	let hoverInfo: HoverInfo | null = $state(null);

	// If the user entered the app directly on a non-root URL (e.g. /regions/[id]),
	// skip the story so that clearing the region doesn't send them back to it.
	onMount(() => {
		if (browser && $page.url.pathname !== "/") {
			storyComplete.set(true);
		}
		if (browser) {
			fetch("/data/zone_stats.json")
				.then((r) => r.json())
				.then((stats) => zoneStats.set(stats))
				.catch(() => {});
		}
	});

	const isRoot = $derived($page.url.pathname === "/");
	const showStory = $derived(browser && isRoot && !$storyComplete);
</script>

<div>
	<!--
		Map area: 100vh while story runs, transitions to 60vh once done.
		No overflow-hidden so the search bar card can extend below the boundary.
	-->
	<div
		class="relative"
		style="height: {showStory ? '100vh' : '60vh'}; transition: height 0.85s cubic-bezier(0.4, 0, 0.2, 1);"
	>
		{#if browser}
			<Map onHover={(i) => (hoverInfo = i)} />
			<HexbinOverlay />
			{#if $vizMode === "zones"}
				<WindParticles />
			{/if}
			{#if $vizMode === "dots"}
				<DotGrid />
			{/if}
		{/if}

		<MapTooltip info={hoverInfo} />

		{#if !showStory}
			<div class="absolute top-4 left-4 z-10">
				<MapControlPanel />
			</div>
			<!--
				bottom-14 hält die Suchleiste frei, die über die Kartenunterkante ragt.
				Auf dem Telefon zusätzlich höher, weil die Attributionszeile dort
				angehoben ist (siehe layout.css) und sonst dahinter verschwände.
			-->
			<div class="absolute bottom-24 sm:bottom-14 left-4 z-10">
				<NoeMindestabstandNotice />
			</div>
		{/if}

		<!--
			Search bar: sits at the bottom of the map div and is translated
			down by half its height so it straddles the map/content boundary.
		-->
		{#if !showStory}
			<div class="absolute bottom-0 inset-x-0 z-20 translate-y-1/2 px-4 sm:px-6 pointer-events-auto"
				onmouseenter={() => (hoverInfo = null)}>
				<div class="max-w-4xl mx-auto">
					<div
						class="bg-white rounded-2xl border border-slate-200 px-4 py-3 flex items-center gap-2"
						style="box-shadow: 0 4px 24px rgba(0,0,0,0.13);"
					>
						<div class="flex-1 min-w-0">
							<SearchBar />
						</div>
						{#if $selectedRegion}
							<span
								class="text-xs font-medium rounded-full px-2 py-0.5 shrink-0 whitespace-nowrap"
								style="background: #eef3ff; color: var(--blue-dark);"
							>{$selectedRegion.layer_label}</span>
						{/if}
					</div>
				</div>
			</div>
		{/if}
	</div>

	<!-- ── Content section: standard scroll below the map ── -->
	{#if !showStory}
		<div class="bg-white" onmouseenter={() => (hoverInfo = null)}>
			<!-- pt-14 clears the overlapping search bar -->
			<div class="max-w-4xl mx-auto px-4 sm:px-6 pt-14 pb-10">
				<Inspector />
			</div>

			<footer class="border-t border-slate-200">
				<div class="max-w-4xl mx-auto px-4 sm:px-6 py-6">
					<SiteFooter />
				</div>
			</footer>
		</div>
	{/if}
</div>

<!-- ── Scrollytelling: fixed overlay while story is active ── -->
{#if showStory}
	<Scrollytelling onComplete={() => storyComplete.set(true)} />
{/if}

<!-- Page slot (region pages use this to set store state) -->
{@render children()}
