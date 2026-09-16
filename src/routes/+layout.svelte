<script lang="ts">
	import './layout.css';
	import SeoHead from '$lib/components/SeoHead.svelte';
	import { page } from '$app/stores';

	let { children } = $props();

	// Grundangaben für jede Seite. Einzelseiten setzen eigene Tags über eine
	// zweite <SeoHead>-Instanz; steht derselbe Tag zweimal im Head, gewinnt der
	// zuletzt gerenderte — also der der Seite.
	const isRoot = $derived($page.url.pathname === '/');
</script>

{#if isRoot}
	<SeoHead
		title="Windkraft in Österreich: Wo Windräder möglich sind"
		description="Interaktive Karte für ganz Österreich: Wo Windräder gebaut werden können, welche Abstände gelten und was in Ihrer Gemeinde geplant ist. Für alle 2.116 Gemeinden."
	/>
{/if}

<div class="min-h-screen w-full" style="background: var(--off-white);">
	{@render children()}
</div>
