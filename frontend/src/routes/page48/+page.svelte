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
	title={t('page48.seo.feedTitle')}
	path="/page48"
	description={t('page48.seo.feedDesc')}
	keywords="Page48, JKT48, JKT48 Page48, hashtag JKT48, komunitas JKT48, fan JKT48"
/>

<Page48Feed showComposer />
