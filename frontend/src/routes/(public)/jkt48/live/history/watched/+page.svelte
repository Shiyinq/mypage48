<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { History } from 'lucide-svelte';
	import { PromoBanner } from '$lib/components/common';
	import SEO from '$lib/components/SEO.svelte';
	import AppBackground from '$lib/components/common/AppBackground.svelte';

	const { t } = useTranslation();
</script>

<SEO
	title={t('liveHistory.publicWatchedEmptyTitle')}
	path="/jkt48/live/history/watched"
	description={t('liveHistory.publicWatchedEmptyDesc')}
/>

<AppBackground hideDecorationsOnMobile={true} />
<div class="w-full flex flex-col items-center justify-center min-h-[calc(100svh-64px)] p-4">
	<PromoBanner
		title={t('liveHistory.publicWatchedEmptyTitle')}
		desc={t('liveHistory.publicWatchedEmptyDesc')}
		actionText={t('liveHistory.registerToWatch')}
		href="/register"
		class="max-w-xl w-full"
		hideCloseIcon={true}
		icon={History}
	/>
</div>
