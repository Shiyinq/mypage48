<script lang="ts">
	import { onMount } from 'svelte';
	import { page48NavbarStore } from '$lib/stores/page48.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import Page48Feed from '$lib/components/page48/Page48Feed.svelte';

	const { t } = useTranslation();

	onMount(() => {
		page48NavbarStore.pageType = 'feed';
	});
</script>

<SEO
	title={t('page48.seo.photosTitle')}
	path="/page48/photos"
	description={t('page48.seo.photosDesc')}
	keywords="Page48, JKT48, gambar JKT48, foto JKT48, komunitas JKT48"
/>

<Page48Feed
	media="image"
	emptyTitle={t('page48.photos.emptyTitle')}
	emptyText={t('page48.photos.emptyText')}
/>
