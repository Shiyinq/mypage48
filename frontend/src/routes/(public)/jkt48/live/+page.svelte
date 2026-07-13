<script lang="ts">
	import { untrack } from 'svelte';
	import { liveStore, liveList, liveLoading, scheduledLiveList } from '$lib/stores/live.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import LiveGrid from '$lib/components/live/LiveGrid.svelte';
	import LivePlatformIndicator from '$lib/components/live/LivePlatformIndicator.svelte';
	import AppBackground from '$lib/components/common/AppBackground.svelte';
	import ScheduledLiveCard from '$lib/components/live/ScheduledLiveCard.svelte';

	const { t } = useTranslation();

	let initialLoading = $state(liveList.value.length === 0);

	async function fetchLives() {
		await Promise.all([liveStore.loadLiveList(), liveStore.loadScheduledList()]);
		initialLoading = false;
	}

	$effect(() => {
		untrack(() => {
			fetchLives();
		});

		const intervalId = setInterval(() => {
			liveStore.loadLiveList(true);
			liveStore.loadScheduledList(true);
		}, 30000);

		return () => clearInterval(intervalId);
	});
</script>

<SEO
	title={t('theater.live.seoTitle')}
	path="/jkt48/live"
	description={t('theater.live.seoDescription')}
	keywords="JKT48 Live, JKT48 Showroom, JKT48 IDN Live, JKT48 Live Streaming, Multi-view JKT48"
/>

<AppBackground hideDecorationsOnMobile={true} />
<LivePlatformIndicator />

<div class="h-full w-full overflow-y-auto py-8 px-4 sm:px-6 lg:px-8 pb-28">
	<div class="max-w-7xl mx-auto w-full">
		<LiveGrid
			liveList={liveList.value}
			loading={liveLoading.value}
			{initialLoading}
			variant="public"
		/>

		{#if scheduledLiveList.value.length > 0}
			<div class="mt-10 mb-10">
				<div class="flex items-center justify-between mb-4">
					<h2 class="text-xl font-black text-slate-900 dark:text-white">
						{t('theater.live.scheduledTitle', { default: 'Live JKT48 Mendatang' })}
					</h2>
				</div>
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
					{#each scheduledLiveList.value as scheduledLive (scheduledLive.live_id)}
						<ScheduledLiveCard live={scheduledLive} />
					{/each}
				</div>
			</div>
		{/if}
	</div>
</div>
