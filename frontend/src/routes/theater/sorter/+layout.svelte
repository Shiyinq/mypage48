<script lang="ts">
	import type { Snippet } from 'svelte';
	import SorterLayout from '$lib/components/sorter/SorterLayout.svelte';

	interface Props {
		children: Snippet;
	}
	let { children }: Props = $props();
</script>

<SorterLayout basePath="/theater/sorter" backPath="/theater">
	{@render children()}
</SorterLayout>
