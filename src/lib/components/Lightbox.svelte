<script lang="ts">
	let open = $state(false);
	let src = $state('');
	let alt = $state('');
	let zoomed = $state(false);
	let originX = $state(50);
	let originY = $state(50);

	export function show(imgSrc: string, imgAlt: string) {
		src = imgSrc;
		alt = imgAlt;
		zoomed = false;
		open = true;
	}

	function close() {
		open = false;
	}

	function toggleZoom(e: MouseEvent) {
		if (zoomed) {
			zoomed = false;
			return;
		}
		const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
		originX = ((e.clientX - rect.left) / rect.width) * 100;
		originY = ((e.clientY - rect.top) / rect.height) * 100;
		zoomed = true;
	}

	function handleKeydown(e: KeyboardEvent) {
		if (open && e.key === 'Escape') close();
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if open}
	<div
		class="fixed inset-0 z-[200] flex items-center justify-center p-6"
		style="backdrop-filter: blur(4px);"
	>
		<button
			class="absolute inset-0 bg-black/90 border-0 p-0 cursor-default"
			onclick={close}
			aria-label="Schließen"
		></button>

		<button
			type="button"
			class="relative max-w-full max-h-full p-0 border-0 bg-transparent leading-none"
			style="cursor:{zoomed ? 'zoom-out' : 'zoom-in'};"
			onclick={toggleZoom}
		>
			<img
				{src}
				{alt}
				draggable="false"
				class="max-w-full max-h-[85vh] select-none transition-transform duration-300 rounded-md block"
				style="transform-origin:{originX}% {originY}%; transform:scale({zoomed
					? 2.4
					: 1});"
			/>
		</button>

		<button
			class="absolute top-4 right-4 w-9 h-9 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-colors border-0"
			onclick={close}
			aria-label="Schließen"
		>
			<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
				<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
			</svg>
		</button>

		<span class="absolute bottom-4 left-1/2 -translate-x-1/2 text-white/60 text-xs font-medium pointer-events-none">
			{zoomed ? 'Klicken zum Verkleinern' : 'Klicken zum Vergrößern'}
		</span>
	</div>
{/if}
