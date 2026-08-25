<script lang="ts">
	import { infoCards, faqCategories } from '$lib/data/faq';
	import type { GraphicKey } from '$lib/data/faq';

	const graphicSrc: Record<GraphicKey, string> = {
		'winter-power':   '/graphics/winterkraft.png',
		'windrad-height': '/graphics/windrad-height.png',
		'rotor-growth': '/graphics/rotordurchmesser.png',
		'land-use':       '/graphics/flaechenbedarf.jpg',
		'repowering':     '/graphics/repowering.png',
		'bird-population':'/graphics/bird-population.png',
		'sound-level':    '/graphics/sound-level.png',
		'infrasound':     '/graphics/infraschall-vergleich.jpg',
		'merit-order':    '/graphics/merit-order.jpg',
	};

	let activeCategory = $state(faqCategories[0].id);
	let openFaq = $state<number | null>(null);

	const currentCategory = $derived(
		faqCategories.find((c) => c.id === activeCategory) ?? faqCategories[0]
	);

	function selectCategory(id: string) {
		activeCategory = id;
		openFaq = null;
	}

	function toggleFaq(id: number) {
		openFaq = openFaq === id ? null : id;
	}
</script>

{#snippet graphic(key: GraphicKey)}
	<div class="my-4 rounded-xl overflow-hidden">
		<img src={graphicSrc[key]} alt={key} class="w-full h-auto block" />
	</div>
{/snippet}

<section class="bg-[#f8f9fc] border-t border-slate-200">
	<div class="max-w-5xl mx-auto px-4 sm:px-6 py-14">

		<!-- ── Section header ── -->
		<div class="mb-10">
			<p class="text-xs font-bold uppercase tracking-widest mb-1" style="color: var(--blue-sky);">
				Hintergrundwissen
			</p>
			<h2 class="text-3xl font-extrabold tracking-tight" style="color: var(--text-dark); letter-spacing: -0.02em;">
				Wissenswertes über Windkraft
			</h2>
			<p class="mt-2 text-base text-slate-500 max-w-2xl">
				Fakten, Hintergründe und häufige Fragen rund um Windenergie in Österreich –
				basierend auf dem Factsheet der Scientists for Future Austria.
			</p>
		</div>

		<!-- ── Info Cards Grid ── -->
		<div class="grid grid-cols-1 md:grid-cols-2 gap-5 mb-14">
			{#each infoCards as card}
				<div
					class="bg-white rounded-2xl border border-slate-200 p-6 flex flex-col"
					style="box-shadow: 0 2px 18px rgba(0,0,0,0.05);"
				>
					<h3 class="font-extrabold text-base mb-1" style="color: var(--blue-dark);">
						{card.title}
					</h3>
					<p class="text-sm font-semibold text-slate-500 mb-3 leading-snug">{card.lead}</p>

					{#if card.graphic}
						{@render graphic(card.graphic)}
					{/if}

					<div class="space-y-2 mt-auto">
						{#each card.content as para}
							<p class="text-sm text-slate-600 leading-relaxed">{para}</p>
						{/each}
					</div>
				</div>
			{/each}
		</div>

		<!-- ── FAQ Section ── -->
		<div>
			<p class="text-xs font-bold uppercase tracking-widest mb-1" style="color: var(--blue-sky);">
				FAQ
			</p>
			<h2 class="text-3xl font-extrabold tracking-tight mb-6" style="color: var(--text-dark); letter-spacing: -0.02em;">
				Häufig gestellte Fragen
			</h2>

			<!-- Category tabs -->
			<div class="flex flex-wrap gap-2 mb-6">
				{#each faqCategories as cat}
					<button
						class="px-4 py-2 rounded-full text-sm font-semibold border-2 transition-all duration-150 cursor-pointer"
						style={activeCategory === cat.id
							? `background: ${cat.color}; color: #fff; border-color: ${cat.color};`
							: `background: transparent; color: ${cat.color}; border-color: ${cat.color}; opacity: 0.8;`}
						onclick={() => selectCategory(cat.id)}
					>
						{cat.label}
					</button>
				{/each}
			</div>

			<!-- FAQ accordion -->
			<div class="space-y-2">
				{#each currentCategory.items as item}
					{@const isOpen = openFaq === item.id}
					<div
						class="bg-white rounded-2xl border overflow-hidden transition-shadow duration-150"
						style="border-color: {isOpen ? currentCategory.color + '40' : '#e2e8f0'}; box-shadow: {isOpen ? '0 4px 20px rgba(0,0,0,0.07)' : '0 1px 6px rgba(0,0,0,0.04)'};"
					>
						<button
							class="w-full flex items-start justify-between px-5 py-4 text-left transition-colors duration-150 cursor-pointer"
							style="background: {isOpen ? currentCategory.bg : 'transparent'};"
							onclick={() => toggleFaq(item.id)}
						>
							<span class="font-semibold text-sm leading-snug pr-2" style="color: var(--text-dark);">
								<span
									class="inline-flex items-center justify-center w-5 h-5 rounded-full text-xs font-bold mr-2 shrink-0"
									style="background: {currentCategory.color}20; color: {currentCategory.color};"
								>{item.id}</span>{item.question}
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
								<path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
							</svg>
						</button>

						{#if isOpen}
							<div class="px-5 pb-5 border-t" style="border-color: {currentCategory.color}20;">
								{#if item.graphic}
									{@render graphic(item.graphic)}
								{/if}
								<div class="space-y-3 mt-3">
									{#each item.answer as para}
										<p class="text-sm text-slate-600 leading-relaxed">{para}</p>
									{/each}
								</div>
							</div>
						{/if}
					</div>
				{/each}
			</div>
		</div>

		<!-- ── Attribution ── -->
		<div class="mt-10 pt-6 border-t border-slate-200">
			<p class="text-xs text-slate-400 leading-relaxed">
				Inhalte basieren auf dem Factsheet „Information Windkraft" der
				<a
					href="https://www.scientists4future.at/2026/04/28/factsheet-windkraft/"
					target="_blank"
					rel="noopener"
					class="underline hover:text-slate-600 transition-colors"
				>Scientists for Future Austria</a>
				(1. Ausgabe, Mai 2026), Autoren: Jan Hurt, Max Nutz.
			</p>
		</div>
	</div>
</section>
