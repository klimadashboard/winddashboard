<script lang="ts">
	import { page } from '$app/stores';
	import SeoHead from '$lib/components/SeoHead.svelte';

	const status = $derived($page.status);
	const title = $derived(
		status === 404 ? 'Seite nicht gefunden' : 'Da ist etwas schiefgelaufen'
	);
	const message = $derived(
		status === 404
			? 'Diese Seite gibt es nicht — vielleicht wurde eine Gemeinde umbenannt oder zusammengelegt. Suchen Sie auf der Karte einfach neu.'
			: ($page.error?.message ?? 'Bitte versuchen Sie es später noch einmal.')
	);
</script>

<SeoHead title="{title} – Windkraft Österreich" description={message} />

<!-- noindex: Fehlerseiten sollen nicht im Index landen. -->
<svelte:head>
	<meta name="robots" content="noindex" />
</svelte:head>

<div class="min-h-screen flex items-center justify-center px-6">
	<div class="max-w-lg text-center">
		<p class="font-mono text-sm tracking-widest text-slate-400 mb-3">{status}</p>
		<h1 class="font-extrabold text-3xl tracking-tight mb-3" style="color: var(--text-dark);">
			{title}
		</h1>
		<p class="text-base leading-relaxed text-slate-600 mb-6">{message}</p>
		<a
			href="/"
			class="inline-flex items-center gap-1.5 text-sm font-semibold rounded-full px-4 py-2 transition-colors"
			style="background: #eef3ff; color: var(--blue-dark);"
		>
			Zur Karte
		</a>
	</div>
</div>
