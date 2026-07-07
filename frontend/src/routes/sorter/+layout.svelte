<script lang="ts">
	import type { Snippet } from 'svelte';
	import SorterLayout from '$lib/components/sorter/SorterLayout.svelte';

	interface Props {
		children: Snippet;
	}
	let { children }: Props = $props();
</script>

<SorterLayout basePath="/sorter" backPath="/">
	{@render children()}
</SorterLayout>
