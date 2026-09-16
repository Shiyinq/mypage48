<script lang="ts">
	import LiveLayout from '$lib/components/live/LiveLayout.svelte';
	import LiveDisabled from '$lib/components/live/LiveDisabled.svelte';
	import { FEATURES } from '$lib/config/features';
	import type { Snippet } from 'svelte';

	interface Props {
		children: Snippet;
	}

	let { children }: Props = $props();
</script>

{#if FEATURES.OSHI_LIVE_ENABLED}
	<LiveLayout basePath="/jkt48/live" backPath="/">
		{@render children()}
	</LiveLayout>
{:else}
	<LiveDisabled backPath="/" />
{/if}
