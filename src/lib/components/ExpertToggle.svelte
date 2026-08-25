<script lang="ts">
	import { expertMode } from "$lib/stores/windStore";
</script>

<button
	onclick={() => expertMode.update((v) => !v)}
	class="flex items-center gap-2 rounded-2xl px-4 py-2.5 text-sm font-medium transition-all duration-200"
	style="
		box-shadow: 0 2px 12px rgba(0,0,0,0.08);
		background: {$expertMode ? 'var(--blue-dark)' : 'white'};
		color: {$expertMode ? 'white' : '#374151'};
		border: 1px solid {$expertMode ? '#162d7a' : '#e2e8f0'};
	"
>
	<svg
		class="w-4 h-4"
		fill="none"
		viewBox="0 0 24 24"
		stroke="currentColor"
		stroke-width="2"
	>
		{#if $expertMode}
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
			/>
		{:else}
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
			/>
		{/if}
	</svg>
	{$expertMode ? "Details an" : "Details"}
</button>
