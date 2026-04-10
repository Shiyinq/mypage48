<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { liveStore, liveList, liveLoading } from '$lib/stores/live';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import LiveGrid from '$lib/components/live/LiveGrid.svelte';

	const { t } = useTranslation();

	let interval: any;
	let initialLoading = $liveList.length === 0;

	async function fetchLives() {
		await liveStore.loadLiveList();
		initialLoading = false;
	}

	onMount(() => {
		fetchLives();
		interval = setInterval(() => liveStore.loadLiveList(true), 30000);
	});

	onDestroy(() => {
		if (interval) clearInterval(interval);
	});
</script>

<SEO
	title={$t('theater.live.title')}
	path="/theater/live"
	description={$t('theater.live.subtitle')}
/>

<div class="w-full pb-12">
	<LiveGrid
		liveList={$liveList}
		loading={$liveLoading}
		{initialLoading}
		variant="theater"
		multiviewHref="/theater/live/multiview"
	/>
</div>
