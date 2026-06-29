<script lang="ts">
	import { onMount, untrack } from 'svelte';
	import { liveHistoryStore } from '$lib/stores/liveHistory.svelte';
	import { liveHistoryFilterStore } from '$lib/stores/liveHistoryFilter.svelte';
	import { History, Trophy } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';
	import { spring } from 'svelte/motion';
	import AppBackground from '$lib/components/common/AppBackground.svelte';
	import { membersStore } from '$lib/stores/theater.svelte';
	import { EmptyState } from '$lib/components';
	import HistoryTopBar from '$lib/components/live/history/shared/HistoryTopBar.svelte';
	import LiveRankingSkeleton from '$lib/components/live/history/shared/LiveRankingSkeleton.svelte';
	import LiveRankingCard from '$lib/components/live/history/shared/LiveRankingCard.svelte';

	const basePath = '/jkt48/live/history/members';

	let scrollY = $state(0);
	let mouse = $state(spring({ x: 0, y: 0 }, { stiffness: 0.1, damping: 0.25 }));

	const { t } = useTranslation();

	let rankingList = $derived(liveHistoryStore.globalMembersRanking);
	let pagination = $derived(liveHistoryStore.globalRankingPagination);
	let isLoading = $derived(liveHistoryStore.isLoading);
	let hasMore = $derived(pagination.current_page < pagination.last_page);

	let mounted = $state(false);

	onMount(() => {
		mounted = true;
		loadRanking(1, true);
		membersStore.load({ limit: 100 });
	});

	async function loadRanking(page: number, force: boolean = false) {
		await liveHistoryStore.loadGlobalMembersRanking(page, force);
	}

	$effect(() => {
		const _trigger =
			liveHistoryFilterStore.filterType +
			liveHistoryFilterStore.customRange.start +
			liveHistoryFilterStore.customRange.end;
		if (mounted) {
			untrack(() => {
				loadRanking(1, true);
			});
		}
	});

	function handleIntersect() {
		if (isLoading || !hasMore) return;
		loadRanking(pagination.current_page + 1);
	}

	function getMemberObj(memberId: string) {
		return membersStore.list.find((m) => String(m.id) === String(memberId));
	}
</script>

<SEO title={t('liveHistory.globalRankingTitle')} path={basePath} />

<div
	role="presentation"
	class="h-full w-full flex flex-col overflow-hidden bg-gradient-to-b from-pink-50/50 via-white to-white dark:from-zinc-950 dark:via-zinc-950 dark:to-zinc-900"
	onmousemove={(e) => {
		const { clientX, clientY } = e;
		const { innerWidth, innerHeight } = window;
		mouse.set({ x: clientX / innerWidth - 0.5, y: clientY / innerHeight - 0.5 });
	}}
>
	<AppBackground interactive={true} bind:mouse bind:scrollY />

	<HistoryTopBar
		title={t('liveHistory.globalRankingTitle')}
		subtitle={t('liveHistory.globalRankingSubtitle')}
		icon={Trophy}
		iconColor="text-purple-500"
		showDateFilter={true}
	/>

	<!-- Main Content -->
	<div class="flex-1 overflow-y-auto" onscroll={(e) => (scrollY = e.currentTarget.scrollTop)}>
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-28 relative z-10">
			{#if isLoading && rankingList.length === 0}
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					{#each Array(6) as _}
						<LiveRankingSkeleton />
					{/each}
				</div>
			{:else if rankingList.length === 0}
				<EmptyState
					icon={History}
					title={t('liveHistory.noHistory')}
					description={t('liveHistory.noHistoryDesc')}
				/>
			{:else}
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					{#each rankingList as member, index}
						{@const memberObj = getMemberObj(member.member_id)}
						<LiveRankingCard
							item={member}
							{index}
							href={`${basePath}/${member.member_id}`}
							mode="global"
							memberImage={memberObj?.img || ''}
							memberImageMedium={memberObj?.img_medium}
							memberImageSmall={memberObj?.img_small}
							blurHash={memberObj?.blurHash}
							timesLabel={t('liveHistory.times')}
						/>
					{/each}
				</div>

				{#if hasMore}
					<div
						use:infiniteScroll
						onintersect={handleIntersect}
						class="w-full py-6 flex justify-center"
					>
						{#if isLoading}
							<div
								class="w-8 h-8 border-4 border-purple-500/30 border-t-purple-500 rounded-full animate-spin"
							></div>
						{/if}
					</div>
				{/if}
			{/if}
		</div>
	</div>
</div>
