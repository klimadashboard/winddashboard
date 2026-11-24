<script lang="ts">
	import { stateContent, GENERAL_INTRO, type Step } from '$lib/data/wegZumWindrad';
	import type { Region } from '$lib/stores/windStore';

	let { region }: { region: Region } = $props();

	const stateId = $derived(
		region.parents?.find(p => p.layer === 'state')?.id ?? (region.layer === 'state' ? region.id : null)
	);
	const content = $derived(stateId ? (stateContent[stateId] ?? null) : null);

	let openStep = $state<Step | null>(null);

	function openModal(step: Step) { openStep = step; }
	function closeModal() { openStep = null; }

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') closeModal();
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if content}
	<div class="mb-12">
		<h2 class="text-2xl font-extrabold tracking-tight mb-4" style="color: var(--blue-sky);">
			Weg zum Windrad
		</h2>

		<div class="max-w-2xl space-y-3 mb-5">
			<p class="text-base text-slate-700 leading-relaxed">{GENERAL_INTRO}</p>
			{#if content.intro}
				<p class="text-base text-slate-700 leading-relaxed">{content.intro}</p>
			{/if}
		</div>

		<!--
			Nummerierte Liste mit Trennlinien statt Kartenraster (3 + 1 Karten mit
			Kreis-Nummern und Pillen ließen rechts eine Lücke und wirkten
			schablonenhaft). Gleiche Optik wie die FAQ darunter.
		-->
		<ol class="border-t border-slate-200">
			{#each content.steps as step}
				<li class="border-b border-slate-200">
					<button
						class="w-full grid grid-cols-[1.75rem_1fr_auto] gap-x-3 items-baseline py-3.5 text-left cursor-pointer group"
						onclick={() => openModal(step)}
					>
						<span class="text-base font-bold tabular-nums" style="color: var(--blue-sky-ink);"
							>{step.number}</span
						>
						<span class="min-w-0">
							<span
								class="block text-base font-semibold leading-snug group-hover:underline underline-offset-2 decoration-slate-300"
								style="color: var(--text-dark);">{step.title}</span
							>
							{#if step.responsible}
								<span class="block mt-1 text-xs font-semibold uppercase tracking-wide text-slate-600"
									>{step.responsible}</span
								>
							{/if}
						</span>
						<span class="text-sm font-semibold whitespace-nowrap" style="color: var(--blue-sky-ink);"
							><span class="hidden sm:inline">Mehr erfahren&nbsp;</span>→</span
						>
					</button>
				</li>
			{/each}
		</ol>
	</div>
{/if}

{#if openStep}
	<button
		class="fixed inset-0 z-40 bg-black/40"
		style="backdrop-filter: blur(2px);"
		onclick={closeModal}
		aria-label="Schließen"
	></button>

	<div
		class="fixed z-50 bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden flex flex-col"
		style="top: 50%; left: 50%; transform: translate(-50%, -50%); width: min(480px, calc(100vw - 2rem)); max-height: min(560px, calc(100vh - 4rem));"
		role="dialog"
		aria-modal="true"
	>
		<div class="flex items-center gap-3 px-5 py-4 border-b border-slate-100 flex-shrink-0">
			<span class="self-start text-base font-bold tabular-nums" style="color: var(--blue-sky-ink);"
				>{openStep.number}</span
			>
			<div class="flex-1 flex flex-col gap-1">
				<h2 class="text-base font-bold leading-snug" style="color: var(--text-dark);">{openStep.title}</h2>
				{#if openStep.responsible}
					<span class="text-xs font-semibold uppercase tracking-wide text-slate-600"
						>{openStep.responsible}</span
					>
				{/if}
			</div>
			<button
				class="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors cursor-pointer"
				onclick={closeModal}
				aria-label="Schließen"
			>
				<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
					<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>

		<div class="overflow-y-auto px-5 py-4 space-y-3">
			{#each openStep.paragraphs as para}
				<p class="text-base text-slate-700 leading-relaxed">{para}</p>
			{/each}
		</div>
	</div>
{/if}
