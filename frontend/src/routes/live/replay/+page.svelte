<script lang="ts">
	import { page } from '$app/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import AppBackground from '$lib/components/common/AppBackground.svelte';
	import ReplayList from '$lib/components/live/replay/ReplayList.svelte';
	import SEO from '$lib/components/SEO.svelte';

	const { t } = useTranslation();
</script>

<SEO
	title={t('replay.list.seoTitle')}
	description={t('replay.list.seoDescription')}
	path={$page.url.pathname}
/>
<AppBackground hideDecorationsOnMobile={true} />
<ReplayList basePath="/live/replay" />
