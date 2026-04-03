<script lang="ts">
	import LiveMultiview from '$lib/components/live/LiveMultiview.svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();
</script>

<SEO
	title={$t('theater.live.multiview.title')}
	description={$t('theater.live.multiview.seoDescription')}
	path="/theater/live/multiview"
/>

<LiveMultiview basePath="/theater/live" />
