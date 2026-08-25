<script lang="ts">
	import './layout.css';

	let { children } = $props();
</script>

<svelte:head>
	<title>Windkraft Österreich – Potenzialatlas</title>
	<meta name="description" content="Interaktiver Atlas für Windkraftpotenzial in Österreich" />
</svelte:head>

<div class="min-h-screen w-full" style="background: var(--off-white);">
	{@render children()}
</div>
