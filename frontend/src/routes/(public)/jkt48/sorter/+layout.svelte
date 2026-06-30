<script lang="ts">
	import type { Snippet } from 'svelte';
	import SorterLayout from '$lib/components/sorter/SorterLayout.svelte';

	interface Props {
		children: Snippet;
	}
	let { children }: Props = $props();
</script>

<SorterLayout basePath="/jkt48/sorter" backPath="/">
	{@render children()}
</SorterLayout>
