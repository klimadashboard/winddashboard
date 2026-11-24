<script lang="ts">
	/**
	 * Fußzeile mit Datenhinweis — gleicher Wortlaut wie in der Presseaussendung
	 * vom 25.11.2026 ("Datenhinweis & Methodik"). Auf der Kartenseite und auf
	 * /methodik; dort ohne den Link auf sich selbst.
	 */
	let { showMethodikLink = true }: { showMethodikLink?: boolean } = $props();
</script>

<div class="space-y-4">
	<div class="text-xs leading-relaxed text-slate-500 max-w-2xl space-y-2">
		<p>
			<strong class="font-semibold text-slate-600">Datenhinweis:</strong>
			Die Karte auf winddashboard.at zeigt, welchen Einfluss die Kriterien auf die Standortwahl
			für Windräder haben. Sie soll und kann keine einzelnen Standorte bewerten oder prüfen und ist
			keine rechtsverbindliche Auskunft darüber, wo Windräder gebaut werden dürfen. Sie soll als
			Grundlage für die Diskussion über Kriterien und deren Einfluss dienen, und nicht konkrete
			Projekte und Standorte bewerten.
		</p>
		<p>
			<strong class="font-semibold text-slate-600">Daten:</strong>
			J. Hurt, „Wind power exclusion and suitability areas for Austria on a 25&nbsp;m grid
			(Abschichtung Windkraft Österreich)“,
			<a
				href="https://doi.org/10.5281/zenodo.24267882"
				target="_blank"
				rel="noopener"
				class="underline underline-offset-2 hover:text-slate-800">doi:10.5281/zenodo.24267882</a
			>
		</p>
	</div>

	<div class="flex flex-wrap items-center gap-x-6 gap-y-2">
		<span class="text-xs text-slate-400">© Klimadashboard.org</span>
		<a
			href="https://klimadashboard.org/impressum"
			target="_blank"
			rel="noopener"
			class="text-xs text-slate-400 hover:text-slate-700 transition-colors">Impressum</a
		>
		{#if showMethodikLink}
			<a
				href="/methodik"
				class="text-xs font-semibold transition-colors inline-flex items-center gap-1"
				style="color: var(--blue-sky);"
			>
				Wie wir rechnen: Methodik
				<svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
					<path stroke-linecap="round" stroke-linejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
				</svg>
			</a>
		{/if}
	</div>
</div>
