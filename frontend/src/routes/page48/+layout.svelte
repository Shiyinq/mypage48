<script lang="ts">
	import type { Snippet } from 'svelte';
	import { onMount } from 'svelte';
	import Page48Layout from '$lib/components/page48/Page48Layout.svelte';
	import { page48NavStore } from '$lib/stores/page48Nav.svelte';

	interface Props {
		children: Snippet;
	}
	let { children }: Props = $props();

	// Record back/forward navigations as they happen. `beforeNavigate` does not
	// report them, and `afterNavigate` runs after the new page has already
	// mounted, so the browser event is the earliest reliable signal. The value is
	// a timestamp because the API cache only honours it for a short window.
	onMount(() => {
		const onPopState = () => {
			page48NavStore.viaHistoryAt = Date.now();
		};
		window.addEventListener('popstate', onPopState);
		return () => window.removeEventListener('popstate', onPopState);
	});
</script>

<Page48Layout basePath="/page48">
	{@render children()}
</Page48Layout>
