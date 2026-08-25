<script lang="ts">
	import { goto } from '$app/navigation';
	import { selectedRegion } from '$lib/stores/windStore';
	import type { Region } from '$lib/stores/windStore';

	let query       = $state('');
	let results: Region[] = $state([]);
	let loading     = $state(false);
	let open        = $state(false);
	let activeIndex = $state(-1);
	let debounceTimer: ReturnType<typeof setTimeout>;
	let inputEl: HTMLInputElement;
	let listEl: HTMLUListElement;

	async function search(q: string) {
		if (q.length < 2) { results = []; open = false; return; }
		loading = true;
		try {
			const fields = 'id,name,code,layer,layer_label,postcodes,center,outline,parents';
			const base   = `https://base.klimadashboard.org/items/regions?filter[country][_eq]=AT&limit=8&fields=${fields}`;

			// Always search by name; additionally search by postcode when query has digits
			const fetches: Promise<Region[]>[] = [
				fetch(`${base}&search=${encodeURIComponent(q)}`).then(r => r.json()).then(j => j.data ?? []),
			];
			if (/\d/.test(q)) {
				fetches.push(
					fetch(`${base}&filter[postcodes][_contains]=${encodeURIComponent(q)}`).then(r => r.json()).then(j => j.data ?? []),
				);
			}

			// Merge results, deduplicate by id, cap at 8
			const arrays = await Promise.all(fetches);
			const seen = new Set<string>();
			const merged: Region[] = [];
			for (const arr of arrays) {
				for (const item of arr) {
					if (!seen.has(item.id)) {
						seen.add(item.id);
						merged.push(item);
					}
				}
			}
			results = merged.slice(0, 8);
			open = results.length > 0;
		} catch {
			results = [];
		} finally {
			loading = false;
		}
	}

	function onInput() {
		clearTimeout(debounceTimer);
		activeIndex = -1;
		if (!query) { open = false; results = []; return; }
		debounceTimer = setTimeout(() => search(query), 280);
	}

	function onKeyDown(e: KeyboardEvent) {
		if (!open && results.length && e.key === 'ArrowDown') {
			open = true;
		}
		if (e.key === 'ArrowDown') {
			e.preventDefault();
			activeIndex = Math.min(activeIndex + 1, results.length - 1);
			scrollActive();
		} else if (e.key === 'ArrowUp') {
			e.preventDefault();
			activeIndex = Math.max(activeIndex - 1, -1);
			scrollActive();
		} else if (e.key === 'Enter') {
			if (activeIndex >= 0 && results[activeIndex]) {
				e.preventDefault();
				selectRegion(results[activeIndex]);
			}
		} else if (e.key === 'Escape') {
			open = false;
			activeIndex = -1;
			inputEl?.blur();
		}
	}

	function scrollActive() {
		if (!listEl || activeIndex < 0) return;
		listEl.querySelectorAll('li')[activeIndex]?.scrollIntoView({ block: 'nearest' });
	}

	function selectRegion(r: Region) {
		selectedRegion.set(r);
		goto('/regions/' + r.id, { noScroll: true });
		open = false;
		activeIndex = -1;
		inputEl?.blur();
	}

	function clearSelection() {
		selectedRegion.set(null);
		goto('/', { noScroll: true });
		inputEl?.focus();
	}

	// Sync query with store; clear when no region selected (e.g. back button)
	$effect(() => {
		const r = $selectedRegion;
		if (r) {
			query = r.name;
		} else {
			query       = '';
			open        = false;
			results     = [];
			activeIndex = -1;
		}
	});

	function matchedPostcode(r: Region): string | null {
		if (!r.postcodes?.length) return null;
		const lower = query.toLowerCase();
		return r.postcodes.find(p => p.toLowerCase().startsWith(lower)) ?? null;
	}
</script>

<div class="relative w-full">
	<div class="flex items-center gap-2">
		<!-- Search icon -->
		<svg class="w-4 h-4 text-slate-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
			<path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 1 1 5 11a6 6 0 0 1 12 0z" />
		</svg>

		<input
			bind:this={inputEl}
			bind:value={query}
			oninput={onInput}
			onkeydown={onKeyDown}
			onfocus={() => { if (results.length) open = true; }}
			placeholder="Gemeinde, Bezirk oder PLZ suchen …"
			class="flex-1 text-sm text-slate-800 placeholder:text-slate-400 bg-transparent outline-none min-w-0 rounded focus-visible:ring-2 focus-visible:ring-blue-400"
			autocomplete="off"
			spellcheck="false"
			role="combobox"
			aria-expanded={open}
			aria-autocomplete="list"
			aria-controls="searchbar-results"
			aria-activedescendant={activeIndex >= 0 ? `searchbar-option-${activeIndex}` : undefined}
		/>

		{#if loading}
			<svg class="w-4 h-4 text-slate-400 animate-spin flex-shrink-0" fill="none" viewBox="0 0 24 24">
				<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
				<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
			</svg>
		{:else if $selectedRegion}
			<button onclick={clearSelection} class="text-slate-400 hover:text-slate-600 transition-colors flex-shrink-0" aria-label="Auswahl löschen">
				<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
					<path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		{/if}
	</div>

	<!-- Dropdown: opens upward, escapes the inspector card (no overflow-hidden on parent) -->
	{#if open && results.length}
		<ul
			bind:this={listEl}
			id="searchbar-results"
			class="absolute bottom-full mb-3 left-0 right-0 bg-white rounded-2xl border border-slate-200 overflow-hidden z-50 max-h-72 overflow-y-auto"
			style="box-shadow: 0 4px 24px rgba(0,0,0,0.10);"
			role="listbox"
		>
			{#each results as r, i}
				<li id="searchbar-option-{i}" role="option" aria-selected={i === activeIndex}>
					<button
						onclick={() => selectRegion(r)}
						class="w-full flex items-start gap-3 px-4 py-2.5 transition-colors text-left"
						style="{i === activeIndex ? 'background: #eef3ff;' : ''}"
						onmouseenter={(e) => { if (i !== activeIndex) (e.currentTarget as HTMLElement).style.background = '#f8f9fc'; }}
						onmouseleave={(e) => { if (i !== activeIndex) (e.currentTarget as HTMLElement).style.background = ''; }}
					>
						<svg class="w-4 h-4 text-slate-400 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
							<path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
							<path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
						</svg>
						<div class="min-w-0">
							<div class="text-sm font-medium truncate" style="color: var(--text-dark);">{r.name}</div>
							<div class="text-xs text-slate-400 flex items-center gap-1.5">
								<span>{r.layer_label}</span>
								{#if matchedPostcode(r)}
									<span class="rounded px-1" style="background: #eef3ff; color: var(--blue-dark);">{matchedPostcode(r)}</span>
								{/if}
							</div>
						</div>
					</button>
				</li>
			{/each}
		</ul>
	{/if}
</div>
