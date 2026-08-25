<script lang="ts">
	import { onMount } from "svelte";
	import { fade } from "svelte/transition";
	import { mapZoom, centerBundesland } from "$lib/stores/windStore";
	import { NÖ_TURBINE_LEGACY_NOTE } from "$lib/data/regionIntro";

	// "Nah rangezoomt" — close enough that individual municipalities/zones are
	// legible, roughly the zoom level a Gemeinde/Bezirk search lands on.
	const ZOOM_THRESHOLD = 9;

	const visible = $derived($mapZoom >= ZOOM_THRESHOLD && $centerBundesland === "Niederösterreich");

	// Closed by default; onMount opens on desktop (mirrors MapControlPanel).
	let open = $state(false);
	onMount(() => {
		open = window.innerWidth >= 768;
	});
</script>

{#if visible}
	<div
		transition:fade={{ duration: 200 }}
		class="rounded-2xl overflow-hidden text-xs"
		style="background: white; border: 1px solid #e2e8f0; box-shadow: 0 2px 18px rgba(0,0,0,0.08); max-width: 300px;"
	>
		<button
			onclick={() => (open = !open)}
			class="flex items-center gap-2 px-3 py-2.5 w-full text-left transition-colors hover:bg-slate-50"
		>
			<svg
				class="w-3.5 h-3.5 flex-shrink-0"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
				stroke-width="2"
				style="color: #b45309;"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
				/>
			</svg>
			<span class="flex-1 font-semibold" style="color: var(--text-dark);"
				>Hinweis zu Mindestabständen in NÖ</span
			>
			<svg
				class="w-3.5 h-3.5 flex-shrink-0 opacity-30 transition-transform duration-200"
				class:rotate-180={open}
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
				stroke-width="2"
			>
				<path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
			</svg>
		</button>

		{#if open}
			<div class="border-t border-slate-100 px-3 py-2.5 leading-relaxed" style="color: #4b5563;">
				{NÖ_TURBINE_LEGACY_NOTE}
			</div>
		{/if}
	</div>
{/if}
