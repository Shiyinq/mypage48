<script lang="ts">
	import { onMount, untrack } from 'svelte';
	import { liveHistoryStore } from '$lib/stores/liveHistory.svelte';
	import { liveHistoryFilterStore } from '$lib/stores/liveHistoryFilter.svelte';
	import { EmptyState } from '$lib/components';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { History, Clock, Trophy, Users, Smartphone, Eye, PlaySquare } from 'lucide-svelte';
	import AppBackground from '$lib/components/common/AppBackground.svelte';
	import { spring } from 'svelte/motion';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';
	import { formatTimeAgo, formatLiveDate, formatDurationSeconds } from '$lib/utils/time';

	import HistoryTopBar from '$lib/components/live/history/shared/HistoryTopBar.svelte';
	import LiveHistoryItemSkeleton from '$lib/components/live/history/shared/LiveHistoryItemSkeleton.svelte';
	import LiveStatCardSkeleton from '$lib/components/live/history/shared/LiveStatCardSkeleton.svelte';
	import LiveStatCard from '$lib/components/live/history/shared/LiveStatCard.svelte';
	import LiveHistoryItemCard from '$lib/components/live/history/shared/LiveHistoryItemCard.svelte';
	import PlatformLogo from '$lib/components/live/PlatformLogo.svelte';

	const basePath = '/theater/live/history';
	const baseLivePath = '/theater/live';

	const { t, locale } = useTranslation();

	let mounted = $state(false);
	let scrollY = $state(0);
	let mouse = $state(spring({ x: 0, y: 0 }, { stiffness: 0.1, damping: 0.25 }));

	let list = $derived(liveHistoryStore.globalList);
	let pagination = $derived(liveHistoryStore.globalPagination);
	let isLoading = $derived(liveHistoryStore.isLoading);
	let hasMore = $derived(pagination.page < pagination.total_pages);
	let initialLoading = $state(true);

	let globalStats = $derived(liveHistoryStore.globalStats);
	let isLoadingStats = $derived(liveHistoryStore.isLoadingGlobalStats);

	onMount(() => {
		mounted = true;
	});

	async function loadHistory(page: number, force: boolean = false) {
		await liveHistoryStore.loadGlobal(page, force);
		if (force) initialLoading = false;
	}

	$effect(() => {
		// This will re-trigger whenever filterType or customRange changes
		const _trigger =
			liveHistoryFilterStore.filterType +
			liveHistoryFilterStore.customRange.start +
			liveHistoryFilterStore.customRange.end;
		if (mounted) {
			untrack(() => {
				loadHistory(1, true);
				liveHistoryStore.loadGlobalStats();
			});
		}
	});

	function handleIntersect() {
		if (!mounted || isLoading || !hasMore) return;
		loadHistory(pagination.page + 1);
	}

	function formatDate(dateStr: string) {
		return formatLiveDate(dateStr, locale.value);
	}
</script>

<SEO
	title={t('liveHistory.globalTitle')}
	path={basePath}
	description={t('liveHistory.globalSubtitle')}
/>

<div
	role="presentation"
	class="h-full w-full flex flex-col overflow-hidden bg-gradient-to-b from-slate-50/50 via-white to-white dark:from-zinc-950 dark:via-zinc-950 dark:to-zinc-900"
	onmousemove={(e) => {
		const { clientX, clientY } = e;
		const { innerWidth, innerHeight } = window;
		mouse.set({ x: clientX / innerWidth - 0.5, y: clientY / innerHeight - 0.5 });
	}}
>
	<AppBackground hideDecorationsOnMobile={true} interactive={true} bind:mouse bind:scrollY />

	<HistoryTopBar
		title={t('liveHistory.globalTitle')}
		subtitle={t('liveHistory.globalSubtitle')}
		icon={History}
		iconColor="text-red-500"
		showDateFilter={true}
	/>

	<!-- Main Content -->
	<div class="flex-1 overflow-y-auto" onscroll={(e) => (scrollY = e.currentTarget.scrollTop)}>
		<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-28 relative z-10">
			<!-- Stats Section -->
			{#if globalStats && !isLoadingStats}
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
					<LiveStatCard
						title={t('liveHistory.totalLives')}
						value={globalStats.total_lives.toLocaleString()}
						icon={PlaySquare}
						color="red"
					/>
					<LiveStatCard
						title={t('liveHistory.totalDuration')}
						value={formatDurationSeconds(globalStats.total_duration, true)}
						icon={Clock}
						color="amber"
					/>
					<LiveStatCard
						title={t('liveHistory.uniqueMembers')}
						value={globalStats.unique_members_count}
						icon={Users}
						color="pink"
					/>

					<LiveStatCard title={t('liveHistory.totalLivePlatform')} icon={Smartphone} color="blue">
						{#snippet subtitle()}
							<div class="flex items-center gap-2 flex-wrap mt-1">
								{#each Object.entries(globalStats.platform_counts || {}) as [platform, count]}
									<div class="flex items-center gap-1.5">
										<PlatformLogo {platform} size="sm" />
										<span class="text-sm font-bold text-slate-700 dark:text-zinc-300">{count}x</span
										>
									</div>
								{/each}
							</div>
						{/snippet}
					</LiveStatCard>
				</div>

				<!-- Ranking & Views Cards -->
				<div class="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
					<LiveStatCard
						title={t('liveHistory.mostFrequentLive')}
						value={globalStats.top_member_name || '-'}
						icon={Trophy}
						color="purple"
						href="{basePath}/members"
					>
						{#snippet subtitle()}
							{#if globalStats.top_member_watches > 0}
								<span class="text-xs font-bold text-purple-600 dark:text-purple-400 shrink-0"
									>({globalStats.top_member_watches}x)</span
								>
							{/if}
						{/snippet}
					</LiveStatCard>

					<LiveStatCard
						title={t('liveHistory.highestViews')}
						value={globalStats.highest_view_live
							? `${globalStats.highest_view_live.duration.toLocaleString()} ${t('liveHistory.views')}`
							: '-'}
						icon={Eye}
						color="emerald"
					>
						{#snippet subtitle()}
							{#if globalStats.highest_view_live}
								<div class="flex items-center gap-1.5 mt-0.5 min-w-0">
									{#if globalStats.highest_view_live?.member_name}
										<span class="text-xs font-bold text-emerald-600 dark:text-emerald-400 truncate"
											>{globalStats.highest_view_live.member_name}</span
										>
									{/if}
									{#if globalStats.highest_view_live?.platform}
										<PlatformLogo platform={globalStats.highest_view_live.platform} size="sm" />
									{/if}
								</div>
							{/if}
						{/snippet}
					</LiveStatCard>
				</div>
			{:else if isLoadingStats}
				<div class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
					{#each Array(4) as _}
						<LiveStatCardSkeleton />
					{/each}
				</div>
			{/if}

			<!-- Recent History Title -->
			{#if list.length > 0}
				<div class="flex items-center gap-2 mb-4">
					<History size={18} class="text-red-500" />
					<h2 class="text-lg font-black text-slate-900 dark:text-white">
						{t('liveHistory.recentHistory')}
					</h2>
				</div>
			{/if}

			{#if initialLoading || (isLoading && list.length === 0)}
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					{#each Array(6) as _}
						<LiveHistoryItemSkeleton />
					{/each}
				</div>
			{:else if list.length === 0}
				<EmptyState
					icon={History}
					title={t('liveHistory.noGlobalHistory')}
					description={t('liveHistory.noGlobalHistoryDesc')}
				/>
			{:else}
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					{#each list as item (item._id)}
						<LiveHistoryItemCard
							href={item.status === 'live'
								? `${baseLivePath}/${item.platform}/${item.live_id}`
								: `/theater/live/history/live/${item.live_id}`}
							mode="global"
							memberImage={item.platform === 'showroom' && item.member?.img
								? item.member.img
								: item.image || item.member?.img}
							memberImageMedium={item.platform === 'showroom' && item.member?.img
								? null
								: item.image_medium}
							memberImageSmall={item.platform === 'showroom' && item.member?.img
								? null
								: item.image_small}
							blurHash={item.platform === 'showroom' && item.member?.img ? null : item.blurHash}
							memberName={item.member?.name}
							liveTitle={item.title}
							platform={item.platform}
							dateStr={formatDate(item.start_at)}
							timeStr={formatTimeAgo(item.start_at, t)}
							startAt={item.start_at}
							endAt={item.end_at}
							duration={item.duration}
							peakViewers={item.view_num}
							isLive={item.status === 'live'}
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
								class="w-8 h-8 border-4 border-red-500/30 border-t-red-500 rounded-full animate-spin"
							></div>
						{/if}
					</div>
				{/if}
			{/if}
		</div>
	</div>
</div>
