<script lang="ts">
	import LiveLayout from '$lib/components/live/LiveLayout.svelte';
	import type { Snippet } from 'svelte';

	interface Props {
		children: Snippet;
	}

	let { children }: Props = $props();
</script>

<LiveLayout basePath="/theater/live" backPath="/theater">
	{@render children()}
</LiveLayout>
