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
	<div class="mb-10">
		<h3 class="text-2xl font-extrabold tracking-tight mb-4" style="color: var(--blue-sky);">
			Weg zum Windrad
		</h3>

		<p class="text-sm text-slate-500 leading-relaxed mb-3">{GENERAL_INTRO}</p>
		{#if content.intro}
			<p class="text-sm text-slate-500 leading-relaxed mb-4">{content.intro}</p>
		{/if}

		<div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
			{#each content.steps as step}
				<button
					class="flex flex-col gap-3 rounded-2xl border border-slate-100 bg-slate-50 p-4 text-left transition-colors duration-150 hover:bg-blue-50 hover:border-blue-200 cursor-pointer group"
					onclick={() => openModal(step)}
				>
					<span
						class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
						style="background: var(--blue-sky); color: #fff;"
					>{step.number}</span>
					<span class="flex-1 text-sm font-semibold leading-snug" style="color: var(--text-dark);">{step.title}</span>
					{#if step.responsible}
						<span
							class="self-start text-[10px] font-semibold uppercase tracking-wide px-2 py-0.5 rounded-full bg-blue-50"
							style="color: var(--blue-sky);"
						>{step.responsible}</span>
					{/if}
					<span class="text-xs text-slate-400 group-hover:text-blue-500 transition-colors">Mehr erfahren →</span>
				</button>
			{/each}
		</div>
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
			<span
				class="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold"
				style="background: var(--blue-sky); color: #fff;"
			>{openStep.number}</span>
			<div class="flex-1 flex flex-col gap-1">
				<h2 class="text-sm font-bold leading-snug" style="color: var(--text-dark);">{openStep.title}</h2>
				{#if openStep.responsible}
					<span
						class="self-start text-[10px] font-semibold uppercase tracking-wide px-2 py-0.5 rounded-full bg-blue-50"
						style="color: var(--blue-sky);"
					>{openStep.responsible}</span>
				{/if}
			</div>
			<button
				class="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer"
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
				<p class="text-sm text-slate-600 leading-relaxed">{para}</p>
			{/each}
		</div>
	</div>
{/if}
