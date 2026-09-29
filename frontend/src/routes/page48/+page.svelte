<script lang="ts">
	import { onMount } from 'svelte';
	import { page48NavbarStore } from '$lib/stores/page48.svelte';
	import Page48Feed from '$lib/components/page48/Page48Feed.svelte';

	onMount(() => {
		page48NavbarStore.pageType = 'feed';
	});
</script>

<Page48Feed showComposer />
