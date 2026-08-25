<script lang="ts">
	import { getSource } from '$lib/data/sources';

	let { id }: { id: number } = $props();

	const source = $derived(getSource(id));

	let open = $state(false);
	let buttonEl: HTMLButtonElement;
	let panelPos = $state({ top: 0, left: 0 });

	// Fixed positioning computed from the button's own screen position, rather
	// than an absolutely-positioned child of the button — the popover otherwise
	// gets clipped by whichever ancestor happens to set overflow-hidden/-auto
	// (the FAQ accordion item, the bento modal, ...), no matter how high its
	// z-index is set. Fixed positioning escapes that entirely.
	function place() {
		const r = buttonEl.getBoundingClientRect();
		const panelWidth = 256; // matches w-64 below
		let left = r.left + r.width / 2 - panelWidth / 2;
		left = Math.max(8, Math.min(left, window.innerWidth - panelWidth - 8));
		panelPos = { top: r.bottom + 6, left };
	}

	function toggle(e: MouseEvent) {
		e.stopPropagation();
		if (!open) place();
		open = !open;
	}

	function close() {
		open = false;
	}
</script>

<svelte:window onclick={close} onresize={close} onscroll={close} />

<span class="relative inline-block">
	<button
		bind:this={buttonEl}
		class="inline-flex items-center justify-center align-super ml-px mr-0.5 w-4 h-4 rounded-full text-[9px] font-bold leading-none cursor-pointer transition-colors"
		style="background: {open ? 'var(--blue-sky)' : 'var(--blue-sky)20'}; color: {open ? '#fff' : 'var(--blue-sky)'};"
		onclick={toggle}
		aria-label="Quelle {id} anzeigen"
	>
		{id}
	</button>

	{#if open && source}
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
		<span
			class="fixed z-[100] w-64 rounded-lg bg-white border border-slate-200 shadow-xl p-3 text-left"
			style="top:{panelPos.top}px; left:{panelPos.left}px; font-weight: normal;"
			onclick={(e) => e.stopPropagation()}
			role="tooltip"
		>
			<span class="block text-xs text-slate-600 leading-relaxed">{source.citation}</span>
			{#if source.url}
				<a
					href={source.url}
					target="_blank"
					rel="noopener"
					class="mt-1.5 inline-flex items-center gap-1 text-xs font-semibold underline"
					style="color: var(--blue-sky);"
				>
					Quelle ansehen ↗
				</a>
			{/if}
		</span>
	{/if}
</span>
