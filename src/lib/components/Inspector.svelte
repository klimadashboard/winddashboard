<script lang="ts">
	import { selectedRegion, regionStats, settlementVariant, variantStats, storyComplete } from "$lib/stores/windStore";
	import { infoCards, faqCategories } from "$lib/data/faq";
	import type { InfoCard, GraphicKey } from "$lib/data/faq";
	import { getRegionIntro } from "$lib/data/regionIntro";
	import { AUSTRIA_HA } from "$lib/config/austria";
	import { goto } from "$app/navigation";
	import WegZumWindrad from "./WegZumWindrad.svelte";
	import RichText from "./RichText.svelte";
	import Lightbox from "./Lightbox.svelte";

	let lightbox: ReturnType<typeof Lightbox> | undefined;

	function replayIntro() {
		selectedRegion.set(null);
		storyComplete.set(false);
		goto("/", { noScroll: true });
	}

	const graphicSrc: Record<GraphicKey, string> = {
		"winter-power": "/graphics/winterkraft.png",
		"windrad-height": "/graphics/windrad-height.png",
		"rotor-growth": "/graphics/rotordurchmesser.png",
		"land-use": "/graphics/flaechenbedarf.jpg",
		"repowering": "/graphics/repowering.png",
		"bird-population": "/graphics/bird-population.png",
		"sound-level": "/graphics/sound-level.png",
		"infrasound": "/graphics/infraschall-vergleich.jpg",
		"merit-order": "/graphics/merit-order.jpg",
	};

	// Photo backgrounds for the bento grid tiles (by card id)
	const bentoBg: Record<string, string> = {
		"winter-power": "/images/winter.jpg",
		"technical-data": "/images/powerplant.jpg",
		"land-use": "/images/sky.jpg",
		"repowering": "/images/repowering.jpg",
	};

	const region = $derived($selectedRegion);
	const stats = $derived($regionStats);
	const intro = $derived(region ? getRegionIntro(region, stats) : null);
	// Falls back to the last known "default" figures while variant_stats.json is loading.
	const zoneCount = $derived($variantStats?.[$settlementVariant]?.count ?? 4093);
	const totalAreaHa = $derived($variantStats?.[$settlementVariant]?.totalHa ?? 351912);
	const potentialPct = $derived(Math.round((totalAreaHa / AUSTRIA_HA) * 1000) / 10);

	// ── Bento card modal ──
	let openCard = $state<InfoCard | null>(null);
	function openBentoCard(card: InfoCard) {
		openCard = card;
	}
	function closeBentoCard() {
		openCard = null;
	}

	// ── FAQ ──
	let activeCategory = $state(faqCategories[0].id);
	let openFaq = $state<number | null>(null);
	const currentCategory = $derived(
		faqCategories.find((c) => c.id === activeCategory) ?? faqCategories[0],
	);
	function selectCategory(id: string) {
		activeCategory = id;
		openFaq = null;
	}
	function toggleFaq(id: number) {
		openFaq = openFaq === id ? null : id;
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === "Escape") closeBentoCard();
	}

	$effect(() => {
		region;
		openFaq = null;
		openCard = null;
	});
</script>

<svelte:window onkeydown={handleKeydown} />

{#if region}
	<!-- ── Regional view ── -->

	<!-- Region intro text -->
	<div class="mb-8">
		<h2
			class="font-extrabold text-3xl tracking-tight mb-5"
			style="color: var(--text-dark); letter-spacing: -0.03em;"
		>
			{region.name}
		</h2>
		{#if intro}
			<p
				class="text-2xl font-extrabold tracking-tight mb-3"
				style="color: var(--blue-sky);"
			>
				Was zeigt die Karte?
			</p>
			{#each intro.paragraphs as para, i}
				<p class="text-base leading-relaxed text-slate-700 {i > 0 ? 'mt-3' : ''}">{para}</p>
			{/each}
			{#if intro.bullets}
				<ul class="mt-3 space-y-1">
					{#each intro.bullets as bullet}
						<li class="flex gap-2 text-sm text-slate-600 leading-relaxed">
							<span
								class="mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0"
								style="background: var(--blue-sky);"
							></span>
							{bullet}
						</li>
					{/each}
				</ul>
			{/if}
			{#if intro.afterBullets}
				{#each intro.afterBullets as para}
					<p class="mt-3 text-sm text-slate-500 leading-relaxed">{para}</p>
				{/each}
			{/if}
		{/if}
	</div>

	<!-- Weg zum Windrad (hidden if no state content — WegZumWindrad renders nothing when content is null) -->
	<WegZumWindrad {region} />

	<!-- Hintergrundwissen (also in region view) -->
	{@render bentoGrid()}

	<!-- FAQs (also in region view) -->
	{@render faqSection()}
{:else}
	<!-- ── Default view ── -->

	<div class="mb-10">
		<h2
			class="font-extrabold text-3xl tracking-tight mb-3"
			style="color: var(--text-dark); letter-spacing: -0.03em;"
		>
			Wo der Wind weht
		</h2>
		<p class="text-base leading-relaxed text-slate-600 max-w-2xl">
			Unsere Landkarte zeigt, wo in Österreich Windräder gebaut werden können.
			Insgesamt gibt es <span class="font-semibold" style="color: var(--text-dark);"
				>{zoneCount.toLocaleString("de-AT")} potenzielle Windeignungsflächen</span
			> in Österreich, die einer Fläche von {potentialPct.toLocaleString("de-AT")} % der österreichischen
			Landesfläche entsprechen.
		</p>
		<p class="text-sm text-slate-400 mt-2 leading-relaxed">
			Suche nach einer Gemeinde oder einem Bezirk für regionale Details.
		</p>
		<div class="mt-3 flex flex-wrap items-center gap-2">
			<button
				onclick={replayIntro}
				class="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-full px-3 py-1.5 transition-colors cursor-pointer"
			>
				<svg
					class="w-3.5 h-3.5"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
					stroke-width="2"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M4 4v5h5M20 20v-5h-5M4 9a9 9 0 0114.65-4.65M20 15a9 9 0 01-14.65 4.65"
					/>
				</svg>
				Intro erneut ansehen
			</button>
			<a
				href="/methodik"
				class="inline-flex items-center gap-1.5 text-xs font-semibold rounded-full px-3 py-1.5 transition-colors"
				style="background: #eef3ff; color: var(--blue-dark);"
			>
				<svg
					class="w-3.5 h-3.5"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
					stroke-width="2"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M12 17.25h.008v.008H12v-.008z M12 21a9 9 0 100-18 9 9 0 000 18z"
					/>
				</svg>
				Wie wir das berechnen: Methodik
			</a>
		</div>
	</div>

	{@render bentoGrid()}
	{@render faqSection()}
{/if}

<!-- ── Zoom hint overlay for lightbox-enabled graphics (snippet) ── -->
{#snippet zoomHint()}
	<div
		class="absolute inset-0 rounded-xl flex items-center justify-center bg-black/0 group-hover:bg-black/10 transition-colors duration-150"
	>
		<span
			class="w-8 h-8 rounded-full bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-150"
		>
			<svg class="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16zM11 8v6M8 11h6" />
			</svg>
		</span>
	</div>
{/snippet}

<!-- ── Hintergrundwissen Bento Grid (snippet) ── -->
{#snippet bentoGrid()}
	<div class="mb-12">
		<p
			class="text-2xl font-extrabold tracking-tight mb-4"
			style="color: var(--blue-sky);"
		>
			Hintergrundwissen
		</p>
		<!--
			3-col bento on sm+:
			  Row 1: [Card 0: col-span-2] [Card 1]
			  Row 2: [Card 2] [Card 3: col-span-2]
			2-col on mobile:
			  Row 1: [Card 0: full width]
			  Row 2: [Card 1] [Card 2]
			  Row 3: [Card 3: full width]
		-->
		<div class="grid grid-cols-2 sm:grid-cols-3 gap-3">
			{#each infoCards as card, i}
				{@const isWide = i === 0 || i === 3}
				<button
					class="group relative overflow-hidden rounded-2xl cursor-pointer text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
					class:col-span-2={isWide}
					style="height: 13rem;"
					onclick={() => openBentoCard(card)}
				>
					{#if bentoBg[card.id]}
						<div
							class="absolute inset-0 bg-cover bg-center transition-transform duration-500 group-hover:scale-105"
							style="background-image: url('{bentoBg[card.id]}');"
						></div>
					{/if}
					<div
						class="absolute inset-0"
						style="background: linear-gradient(160deg, rgba(8,18,50,0.20) 0%, rgba(8,18,50,0.78) 55%, rgba(8,18,50,0.96) 100%);"
					></div>
					<div class="absolute bottom-0 left-0 right-0 p-4 sm:p-5">
						<p
							class="text-white font-bold text-sm sm:text-base leading-snug mb-1"
						>
							{card.title}
						</p>
						<p class="text-white/65 text-xs leading-snug line-clamp-2">
							{card.lead}
						</p>
					</div>
					<div
						class="absolute top-3 right-3 w-7 h-7 rounded-full bg-white/10 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200"
					>
						<svg
							class="w-3.5 h-3.5 text-white"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
							stroke-width="2.5"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								d="M9 5l7 7-7 7"
							/>
						</svg>
					</div>
				</button>
			{/each}
		</div>
	</div>
{/snippet}

<!-- ── FAQ Section (snippet) ── -->
{#snippet faqSection()}
	<div>
		<p
			class="text-2xl font-extrabold tracking-tight mb-4"
			style="color: var(--blue-sky);"
		>
			Häufig gestellte Fragen
		</p>

		<div class="flex flex-wrap gap-1.5 mb-4">
			{#each faqCategories as cat}
				<button
					class="px-3 py-1.5 rounded-full text-xs font-semibold border transition-all duration-150 cursor-pointer"
					style={activeCategory === cat.id
						? `background: ${cat.color}; color: #fff; border-color: ${cat.color};`
						: `background: transparent; color: ${cat.color}; border-color: ${cat.color}; opacity: 0.75;`}
					onclick={() => selectCategory(cat.id)}
				>
					{cat.label}
				</button>
			{/each}
		</div>

		<div class="space-y-2">
			{#each currentCategory.items as item}
				{@const isOpen = openFaq === item.id}
				<div
					class="rounded-xl border overflow-hidden transition-shadow duration-150"
					style="border-color: {isOpen
						? currentCategory.color + '40'
						: '#f1f5f9'}; box-shadow: {isOpen
						? '0 2px 12px rgba(0,0,0,0.06)'
						: 'none'};"
				>
					<button
						class="w-full flex items-start justify-between px-4 py-3 text-left transition-colors duration-150 cursor-pointer"
						style="background: {isOpen ? currentCategory.bg : 'transparent'};"
						onclick={() => toggleFaq(item.id)}
					>
						<span
							class="text-sm font-semibold leading-snug pr-2"
							style="color: var(--text-dark);"
						>
							<span
								class="inline-flex items-center justify-center w-5 h-5 rounded-full text-[10px] font-bold mr-2"
								style="background: {currentCategory.color}20; color: {currentCategory.color};"
								>{item.id}</span
							>{item.question}
						</span>
						<svg
							class="w-4 h-4 flex-shrink-0 mt-0.5 transition-transform duration-200"
							class:rotate-180={isOpen}
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
							stroke-width="2.5"
							style="color: {currentCategory.color};"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								d="M19 9l-7 7-7-7"
							/>
						</svg>
					</button>

					{#if isOpen}
						<div
							class="px-4 pb-4 border-t"
							style="border-color: {currentCategory.color}20;"
						>
							<div class="space-y-2 mt-3">
								{#each item.answer as para}
									<p class="text-sm text-slate-600 leading-relaxed"><RichText text={para} /></p>
								{/each}
							</div>
							{#if item.graphic}
								<div class="my-4">
									<button
										type="button"
										class="group relative block max-w-xl w-full mx-auto cursor-zoom-in"
										onclick={() => lightbox?.show(graphicSrc[item.graphic!], item.question)}
										aria-label="Grafik vergrößern"
									>
										<img
											src={graphicSrc[item.graphic]}
											alt={item.question}
											class="w-full h-auto block rounded-xl"
										/>
										{@render zoomHint()}
									</button>
									{#if item.graphicCaption}
										<p class="text-xs text-slate-400 text-center mt-1.5 leading-relaxed">
											<RichText text={item.graphicCaption} />
										</p>
									{/if}
								</div>
							{/if}
						</div>
					{/if}
				</div>
			{/each}
		</div>

		<p class="text-xs text-slate-400 leading-relaxed mt-5">
			Inhalte: <a
				href="https://www.scientists4future.at/2026/04/28/factsheet-windkraft/"
				target="_blank"
				rel="noopener"
				class="underline">Scientists for Future Austria</a
			>, Factsheet Windkraft (Mai 2026).
		</p>
	</div>
{/snippet}

<!-- ── Bento popup modal ── -->
{#if openCard}
	<button
		class="fixed inset-0 z-40 bg-black/40"
		style="backdrop-filter: blur(3px);"
		onclick={closeBentoCard}
		aria-label="Schließen"
	></button>

	<div class="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
		<div
			class="pointer-events-auto bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col"
			style="width: min(560px, calc(100vw - 2rem)); max-height: min(640px, calc(100vh - 4rem));"
			role="dialog"
			aria-modal="true"
		>
			<div
				class="flex items-center gap-3 px-5 py-4 border-b border-slate-100 flex-shrink-0"
			>
				<h2
					class="flex-1 text-base font-bold leading-snug"
					style="color: var(--text-dark);"
				>
					{openCard.title}
				</h2>
				<button
					class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"
					onclick={closeBentoCard}
					aria-label="Schließen"
				>
					<svg
						class="w-4 h-4"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
						stroke-width="2.5"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M6 18L18 6M6 6l12 12"
						/>
					</svg>
				</button>
			</div>
			<div class="overflow-y-auto px-5 py-4 space-y-3">
				<p class="text-sm font-semibold text-slate-500">{openCard.lead}</p>
				{#if openCard.graphic}
					<div class="my-3">
						<button
							type="button"
							class="group relative block max-w-xl w-full mx-auto cursor-zoom-in"
							onclick={() => lightbox?.show(graphicSrc[openCard!.graphic!], openCard!.title)}
							aria-label="Grafik vergrößern"
						>
							<img
								src={graphicSrc[openCard.graphic]}
								alt={openCard.title}
								class="w-full h-auto block rounded-xl"
							/>
							{@render zoomHint()}
						</button>
						{#if openCard.graphicCaption}
							<p class="text-xs text-slate-400 text-center mt-1.5 leading-relaxed">
								<RichText text={openCard.graphicCaption} />
							</p>
						{/if}
					</div>
				{/if}
				{#each openCard.content as para}
					<p class="text-sm text-slate-600 leading-relaxed"><RichText text={para} /></p>
				{/each}
			</div>
		</div>
	</div>
{/if}

<Lightbox bind:this={lightbox} />
