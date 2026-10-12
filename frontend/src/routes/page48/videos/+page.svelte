<script lang="ts">
	import { onMount } from 'svelte';
	import { page48NavbarStore } from '$lib/stores/page48.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import Page48VideoFeed from '$lib/components/page48/Page48VideoFeed.svelte';

	const { t } = useTranslation();

	onMount(() => {
		page48NavbarStore.pageType = 'feed';
	});
</script>

<SEO
	title={t('page48.seo.videosTitle')}
	path="/page48/videos"
	description={t('page48.seo.videosDesc')}
	keywords="Page48, JKT48, video JKT48, komunitas JKT48"
/>

<Page48VideoFeed />
