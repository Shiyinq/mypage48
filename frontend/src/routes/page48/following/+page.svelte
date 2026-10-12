<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page48NavbarStore } from '$lib/stores/page48.svelte';
	import { isAuthenticated } from '$lib/stores/authStatus.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import Page48Feed from '$lib/components/page48/Page48Feed.svelte';

	const { t } = useTranslation();

	onMount(() => {
		page48NavbarStore.pageType = 'feed';
	});

	// The tab stays visible when signed out, but the feed itself needs an account.
	$effect(() => {
		if (!isAuthenticated.value) {
			void goto('/login');
		}
	});
</script>

<SEO
	title={t('page48.seo.followingTitle')}
	path="/page48/following"
	description={t('page48.seo.followingDesc')}
	keywords="Page48, JKT48, following, komunitas JKT48"
/>

{#if isAuthenticated.value}
	<Page48Feed following />
{/if}
