<script lang="ts">
	import { selectedRegion } from '$lib/stores/windStore';

	let { data } = $props();

	$effect(() => {
		if (data.region) selectedRegion.set(data.region);
	});
</script>
