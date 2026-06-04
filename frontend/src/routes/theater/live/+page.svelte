<script lang="ts">
	import { untrack } from 'svelte';
	import { liveStore, liveList, liveLoading } from '$lib/stores/live.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import LiveGrid from '$lib/components/live/LiveGrid.svelte';

	const { t } = useTranslation();

	let initialLoading = $state(liveList.value.length === 0);

	async function fetchLives() {
		await liveStore.loadLiveList();
		initialLoading = false;
	}

	$effect(() => {
		untrack(() => {
			fetchLives();
		});

		const intervalId = setInterval(() => {
			liveStore.loadLiveList(true);
		}, 30000);

		return () => clearInterval(intervalId);
	});
</script>

<SEO
	title={t('theater.live.seoTitle')}
	path="/theater/live"
	description={t('theater.live.seoDescription')}
/>

<div class="w-full pb-12">
	<LiveGrid
		liveList={liveList.value}
		loading={liveLoading.value}
		{initialLoading}
		variant="theater"
		multiviewHref="/theater/live/multiview"
		globalHistoryHref="/theater/live/history"
		historyHref="/theater/live/history/watched"
	/>
</div>
