<script lang="ts">
	import { onMount } from 'svelte';
	import { page48NavbarStore } from '$lib/stores/page48.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import Page48Feed from '$lib/components/page48/Page48Feed.svelte';

	const { t } = useTranslation();

	onMount(() => {
		page48NavbarStore.pageType = 'feed';
	});
</script>

<Page48Feed
	media="video"
	emptyTitle={t('page48.videos.emptyTitle')}
	emptyText={t('page48.videos.emptyText')}
/>
