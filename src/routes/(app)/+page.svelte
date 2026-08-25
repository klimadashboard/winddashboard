<script lang="ts">
	import { selectedRegion } from '$lib/stores/windStore';

	$effect(() => {
		selectedRegion.set(null);
	});
</script>
