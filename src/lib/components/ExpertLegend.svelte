<script lang="ts">
	import { expertMode } from '$lib/stores/windStore';
	import { LEGEND_CODES, GROUP_LABELS } from '$lib/config/legend';

	// Group codes (skip code 0 "Außerhalb")
	const groups = ['suitable', 'exclusion', 'terrain', 'wind'] as const;
	type Group = typeof groups[number];

	function hexToRgba(hex: string): string {
		// Convert e.g. "#3b82f6ff" or "#3b82f6a0" to rgba
		const r = parseInt(hex.slice(1, 3), 16);
		const g = parseInt(hex.slice(3, 5), 16);
		const b = parseInt(hex.slice(5, 7), 16);
		const a = hex.length >= 9 ? parseInt(hex.slice(7, 9), 16) / 255 : 1;
		return `rgba(${r},${g},${b},${a.toFixed(2)})`;
	}

	function codesForGroup(group: Group) {
		return LEGEND_CODES.filter(c => c.group === group);
	}
</script>

{#if $expertMode}
	<div class="bg-white/97 backdrop-blur-sm rounded-2xl border border-slate-200 p-4 w-64 max-h-[70vh] overflow-y-auto" style="box-shadow: 0 2px 18px rgba(0,0,0,0.06);">
		<div class="flex items-center gap-2 mb-3">
			<svg class="w-4 h-4" style="color: var(--blue-dark);" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
				<path stroke-linecap="round" stroke-linejoin="round" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
			</svg>
			<h3 class="text-sm font-bold tracking-tight" style="color: var(--text-dark);">Legende</h3>
		</div>

		<div class="space-y-3">
			{#each groups as group}
				<div>
					<div class="text-[10px] font-bold uppercase tracking-widest mb-1.5" style="color: var(--blue-sky);">{GROUP_LABELS[group]}</div>
					<div class="space-y-1">
						{#each codesForGroup(group) as code}
							<div class="flex items-start gap-2">
								<span
									class="w-3 h-3 rounded-sm flex-shrink-0 mt-0.5 border border-black/10"
									style="background-color: {hexToRgba(code.color)};"
								></span>
								<div>
									<div class="text-xs text-slate-700 leading-tight">{code.name}</div>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/each}
		</div>

		<!-- Vector layer legend -->
		<div class="mt-3 pt-3 border-t border-slate-100">
			<div class="text-[10px] font-bold uppercase tracking-widest mb-1.5" style="color: var(--blue-sky);">Vektorebenen</div>
			<div class="space-y-1">
				<div class="flex items-center gap-2">
					<span class="w-3 h-0.5 bg-amber-500 flex-shrink-0" style="border-top: 2px dashed #d97706;"></span>
					<span class="text-xs text-slate-700">Offizielle Eignungszonen (NÖ)</span>
				</div>
				<div class="flex items-center gap-2">
					<span class="w-3 h-3 rounded-full bg-slate-800 border border-white flex-shrink-0 shadow-sm"></span>
					<span class="text-xs text-slate-700">Bestehende Windkraftanlagen</span>
				</div>
			</div>
		</div>
	</div>
{/if}
