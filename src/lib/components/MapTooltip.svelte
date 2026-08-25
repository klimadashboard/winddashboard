<script lang="ts">
	import type { HoverInfo } from "./Map.svelte";

	let { info = null }: { info: HoverInfo | null } = $props();

	function formatPd(val: unknown): string {
		const n = Number(val);
		return isNaN(n) ? "–" : `${Math.round(n)} W/m²`;
	}

	function formatDate(val: unknown): string {
		if (!val) return "–";
		const d = new Date(String(val));
		return isNaN(d.getTime()) ? String(val) : d.toLocaleDateString("de-AT");
	}

	const visible = $derived(
		info && (info.zone || info.official || info.turbine || (info.bands && info.bands.length > 0)),
	);
	const style = $derived(
		info ? `left:${info.x + 14}px; top:${info.y - 10}px;` : "",
	);
</script>

{#if visible && info}
	<div
		class="absolute z-50 pointer-events-none max-w-xs rounded-2xl bg-white/97 backdrop-blur-sm border border-slate-200 text-sm overflow-hidden"
		style="min-width: 220px; box-shadow: 0 4px 24px rgba(0,0,0,0.10); {style}"
	>
		{#if info.bands && info.bands.length > 0}
		<div class="px-3 py-2 border-b border-slate-100">
			<p class="text-[10px] font-bold uppercase tracking-widest mb-2" style="color:#64748b;">
				{info.bands.length === 1 ? 'Ausschlussgrund' : `${info.bands.length} Ausschlussgründe`}
			</p>
			<div class="space-y-1.5">
				{#each info.bands as band}
					<div class="flex items-start gap-2">
						<span class="w-2.5 h-2.5 rounded-sm flex-shrink-0 mt-0.5 border border-black/10"
							style="background:{band.color.slice(0,7)};"></span>
						<div>
							<p class="text-xs font-semibold text-slate-800 leading-tight">{band.label}</p>
							<p class="text-[10px] text-slate-400 leading-snug">{band.description}</p>
						</div>
					</div>
				{/each}
			</div>
		</div>
	{/if}

	{#if info.zone}
			<div class="px-3 py-2 border-b border-slate-100">
				<div class="flex items-center gap-2 mb-1">
					<span
						class="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0"
						style="background:#2563eb"
					></span>
					<span
						class="font-semibold text-slate-800 text-xs uppercase tracking-wide"
						>Potenzielle Zone</span
					>
				</div>
				<div class="text-slate-600 text-xs space-y-0.5">
					<div>
						<span class="text-slate-400">Fläche</span>
						<span class="font-medium text-slate-700"
							>{Number(info.zone.area_ha).toLocaleString("de-AT")} ha</span
						>
					</div>
					{#if Number(info.zone.n_existing_turbines) > 0}
						<div>
							<span class="text-slate-400">Bestehende Anlagen</span>
							<span class="font-medium text-slate-700"
								>{info.zone.n_existing_turbines}</span
							>
						</div>
					{/if}
					<div class="text-slate-400 mt-1 text-[10px]">
						{info.zone.bundesland ?? ""}
					</div>
				</div>
			</div>
		{/if}

		{#if info.official}
			<div class="px-3 py-2 border-b border-slate-100">
				<div class="flex items-center gap-2 mb-1">
					<span
						class="inline-block w-2.5 h-2.5 rounded flex-shrink-0 bg-violet-500 border border-violet-600"
					></span>
					<span
						class="font-semibold text-slate-800 text-xs uppercase tracking-wide"
						>Offizielle Eignungszone</span
					>
				</div>
				<div class="text-slate-600 text-xs space-y-0.5">
					<div>
						<span class="text-slate-400">Bezeichnung</span>
						<span class="font-medium text-slate-700">{info.official.name}</span>
					</div>
					<div>
						<span class="text-slate-400">Fläche</span>
						<span class="font-medium text-slate-700"
							>{Number(info.official.area_ha).toLocaleString("de-AT")} ha</span
						>
					</div>
					<div>
						<span class="text-slate-400">Rechtsgrundlage</span>
						<span class="font-medium text-slate-700"
							>{info.official.legal_basis ?? "–"}</span
						>
					</div>
					<div>
						<span class="text-slate-400">Gültig ab</span>
						<span class="font-medium text-slate-700"
							>{formatDate(info.official.effective_from)}</span
						>
					</div>
					{#if info.official.communities}
						<div class="text-slate-400 text-[10px] mt-0.5">
							{info.official.communities}
						</div>
					{/if}
				</div>
			</div>
		{/if}

		{#if info.turbine}
			<div class="px-3 py-2">
				<div class="flex items-center gap-2 mb-1">
					<span class="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0 bg-slate-800 border-2 border-white shadow"></span>
					<span class="font-semibold text-slate-800 text-xs uppercase tracking-wide">Bestehende Anlage</span>
				</div>
				<div class="text-slate-600 text-xs space-y-0.5">
					{#if info.turbine.gemeinde || info.turbine.bezirk}
						<div><span class="text-slate-400">Standort</span> <span class="font-medium text-slate-700">{[info.turbine.gemeinde, info.turbine.bezirk].filter(Boolean).join(', ')}</span></div>
					{/if}
					{#if info.turbine.power_kw}
						<div><span class="text-slate-400">Leistung</span> <span class="font-medium text-slate-700">{Number(info.turbine.power_kw).toLocaleString('de-AT')} kW</span></div>
					{/if}
					{#if info.turbine.commissioned}
						<div><span class="text-slate-400">Inbetriebnahme</span> <span class="font-medium text-slate-700">{String(info.turbine.commissioned).slice(-4)}</span></div>
					{/if}
				</div>
			</div>
		{/if}
	</div>
{/if}
