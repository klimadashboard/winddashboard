<script lang="ts">
	import { vizMode } from '$lib/stores/windStore';
	import type { VizMode } from '$lib/stores/windStore';

	const options: { value: VizMode; label: string }[] = [
		{ value: 'zones',   label: 'Potenzialzonen' },
		{ value: 'heatmap', label: 'Heatmap' },
		{ value: 'hexbin',  label: 'Hexbin 3D' },
		{ value: 'dots',    label: 'Windgitter' },
	];
</script>

<div
	class="rounded-2xl flex items-center gap-2 px-3 py-1.5 text-xs"
	style="background: white; border: 1px solid #e2e8f0; box-shadow: 0 2px 12px rgba(0,0,0,0.07);"
>
	<span class="font-semibold whitespace-nowrap" style="color: var(--text-dark);">Ansicht</span>
	<select
		value={$vizMode}
		onchange={(e) => vizMode.set((e.currentTarget as HTMLSelectElement).value as VizMode)}
		class="bg-transparent font-medium cursor-pointer rounded pr-1 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-400"
		style="color: var(--blue-dark);"
	>
		{#each options as opt}
			<option value={opt.value}>{opt.label}</option>
		{/each}
	</select>
</div>
