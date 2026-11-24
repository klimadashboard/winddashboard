<script lang="ts">
	import './layout.css';
	import SeoHead from '$lib/components/SeoHead.svelte';
	import { page } from '$app/stores';
	import { dev } from '$app/environment';
	import { RYBBIT_SITE_ID } from '$lib/analytics';

	let { children } = $props();

	// Grundangaben für jede Seite. Einzelseiten setzen eigene Tags über eine
	// zweite <SeoHead>-Instanz; steht derselbe Tag zweimal im Head, gewinnt der
	// zuletzt gerenderte — also der der Seite.
	const isRoot = $derived($page.url.pathname === '/');
</script>

<svelte:head>
	<!-- Rybbit wie in klimadashboard-core; lokal aus, damit Entwicklung die Zahlen nicht verfälscht. -->
	{#if !dev}
		<script src="https://analytics.klimadashboard.org/api/script.js" data-site-id={RYBBIT_SITE_ID} defer></script>
	{/if}
</svelte:head>

{#if isRoot}
	<SeoHead
		title="Windkraft in Österreich: Wo Windräder möglich sind"
		description="Interaktive Karte für ganz Österreich: Wo Windräder gebaut werden können, welche Abstände gelten und was in deiner Gemeinde geplant ist. Für alle 2.116 Gemeinden."
	/>
{/if}

<div class="min-h-screen w-full" style="background: var(--off-white);">
	{@render children()}
</div>
