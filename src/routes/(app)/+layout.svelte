<script lang="ts">
	import Map from "$lib/components/Map.svelte";
	import WindParticles from "$lib/components/WindParticles.svelte";
	import DotGrid from "$lib/components/DotGrid.svelte";
	import MapTooltip from "$lib/components/MapTooltip.svelte";
	import Inspector from "$lib/components/Inspector.svelte";
	import HexbinOverlay from "$lib/components/HexbinOverlay.svelte";
	import MapControlPanel from "$lib/components/MapControlPanel.svelte";
	import NoeMindestabstandNotice from "$lib/components/NoeMindestabstandNotice.svelte";
	import Scrollytelling from "$lib/components/Scrollytelling.svelte";
	import SearchBar from "$lib/components/SearchBar.svelte";
	import { vizMode, storyComplete, selectedRegion, variantStats } from "$lib/stores/windStore";
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
			fetch("/data/variant_stats")
				.then((r) => r.json())
				.then((stats) => variantStats.set(stats))
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
			<!-- bottom-14 clears the search bar, which straddles the map's bottom edge -->
			<div class="absolute bottom-14 left-4 z-10">
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
								class="text-[11px] font-medium rounded-full px-2 py-0.5 shrink-0 whitespace-nowrap"
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
				<div class="max-w-4xl mx-auto px-4 sm:px-6 py-6 flex items-center gap-6">
					<span class="text-xs text-slate-400">© Klimadashboard.org</span>
					<a
						href="https://klimadashboard.org/impressum"
						target="_blank"
						rel="noopener"
						class="text-xs text-slate-400 hover:text-slate-700 transition-colors"
					>Impressum</a>
					<a
						href="/methodik"
						class="text-xs font-semibold transition-colors inline-flex items-center gap-1"
						style="color: var(--blue-sky);"
					>
						Wie wir rechnen: Methodik
						<svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
							<path stroke-linecap="round" stroke-linejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
						</svg>
					</a>
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
