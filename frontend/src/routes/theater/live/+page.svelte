<script lang="ts">
	import { untrack } from 'svelte';
	import { liveStore, liveList, liveLoading } from '$lib/stores/live.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import LiveGrid from '$lib/components/live/LiveGrid.svelte';
	import AppBackground from '$lib/components/common/AppBackground.svelte';

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

<AppBackground hideDecorationsOnMobile={true} />
<div class="h-full w-full overflow-y-auto py-8 px-4 sm:px-6 lg:px-8 pb-28">
	<div class="max-w-7xl mx-auto w-full">
		<LiveGrid
			liveList={liveList.value}
			loading={liveLoading.value}
			{initialLoading}
			variant="theater"
		/>
	</div>
</div>
