<script lang="ts">
	import type { Snippet } from 'svelte';
	import Page48Layout from '$lib/components/page48/Page48Layout.svelte';

	interface Props {
		children: Snippet;
	}
	let { children }: Props = $props();
</script>

<Page48Layout basePath="/page48">
	{@render children()}
</Page48Layout>
