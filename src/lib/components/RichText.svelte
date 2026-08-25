<script lang="ts">
	import Footnote from './Footnote.svelte';

	let { text }: { text: string } = $props();

	type Segment = { kind: 'text'; value: string } | { kind: 'footnote'; id: number };

	const segments = $derived.by((): Segment[] => {
		const parts: Segment[] = [];
		const re = /\[(\d+)\]/g;
		let lastIndex = 0;
		let match: RegExpExecArray | null;
		while ((match = re.exec(text))) {
			if (match.index > lastIndex) {
				parts.push({ kind: 'text', value: text.slice(lastIndex, match.index) });
			}
			parts.push({ kind: 'footnote', id: Number(match[1]) });
			lastIndex = re.lastIndex;
		}
		if (lastIndex < text.length) {
			parts.push({ kind: 'text', value: text.slice(lastIndex) });
		}
		return parts;
	});
</script>

{#each segments as segment}
	{#if segment.kind === 'text'}
		{segment.value}
	{:else}
		<Footnote id={segment.id} />
	{/if}
{/each}
