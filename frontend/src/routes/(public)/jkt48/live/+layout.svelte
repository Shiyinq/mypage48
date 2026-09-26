<script lang="ts">
	import LiveLayout from '$lib/components/live/LiveLayout.svelte';
	import LiveDisabled from '$lib/components/live/LiveDisabled.svelte';
	import { FEATURES } from '$lib/config/features';
	import { page } from '$app/stores';
	import type { Snippet } from 'svelte';

	interface Props {
		children: Snippet;
	}

	let { children }: Props = $props();

	let isDetailRoute = $derived($page.url.pathname.startsWith('/jkt48/live/details'));
</script>

{#if isDetailRoute}
	{@render children()}
{:else if FEATURES.OSHI_LIVE_ENABLED}
	<LiveLayout basePath="/jkt48/live" backPath="/">
		{@render children()}
	</LiveLayout>
{:else}
	<LiveDisabled backPath="/" />
{/if}
