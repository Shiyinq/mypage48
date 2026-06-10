<script lang="ts">
	import { onMount, untrack } from 'svelte';
	import { page } from '$app/stores';
	import { liveHistoryStore } from '$lib/stores/liveHistory.svelte';
	import { liveHistoryFilterStore } from '$lib/stores/liveHistoryFilter.svelte';
	import { History, Clock, PlaySquare, Smartphone, Activity } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { isImmersive } from '$lib/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';
	import { spring } from 'svelte/motion';
	import AppBackground from '$lib/components/common/AppBackground.svelte';
	import { membersStore } from '$lib/stores/theater.svelte';
	import { EmptyState } from '$lib/components';
	import PlatformLogo from '$lib/components/live/PlatformLogo.svelte';
	import { formatTimeAgo, formatLiveDate, formatDurationSeconds } from '$lib/utils/time';

	import HistoryTopBar from '$lib/components/live/history/shared/HistoryTopBar.svelte';
	import LiveHistoryItemSkeleton from '$lib/components/live/history/shared/LiveHistoryItemSkeleton.svelte';
	import LiveStatCard from '$lib/components/live/history/shared/LiveStatCard.svelte';
	import LiveHistoryItemCard from '$lib/components/live/history/shared/LiveHistoryItemCard.svelte';

	const basePath = '/jkt48/live/history/members';
	const baseLivePath = '/jkt48/live';

	let scrollY = $state(0);
	let mouse = $state(spring({ x: 0, y: 0 }, { stiffness: 0.1, damping: 0.25 }));

	const { t, locale } = useTranslation();

	let memberId = $derived($page.params.member_id || '');
	let historyList = $derived(liveHistoryStore.globalMemberHistory);
	let pagination = $derived(liveHistoryStore.globalMemberHistoryPagination);
	let isLoading = $derived(liveHistoryStore.isLoading);
	let hasMore = $derived(pagination.page < pagination.total_pages);
	let stats = $derived(liveHistoryStore.globalMemberStats[memberId]);

	let memberInfo = $derived(() => {
		const member = membersStore.list.find(
			(m) =>
				String(m.id) === String(memberId) ||
				(m.socials?.idn_app && String(memberId).includes(m.socials.idn_app)) ||
				(m.socials?.showroom && String(memberId) === String(m.socials.showroom))
		);
		return member;
	});

	let displayName = $derived(() => {
		const m = memberInfo();
		if (m) return m.name;
		if (historyList.length > 0) return historyList[0].member?.name || memberId;
		return memberId;
	});

	let mounted = $state(false);

	onMount(() => {
		mounted = true;
		isImmersive.set(true);
		document.body.style.overflow = 'hidden';
		if (memberId) {
			liveHistoryStore.loadGlobalMemberHistory(memberId, 1, true);
			liveHistoryStore.loadGlobalMemberStats(memberId);
		}
		membersStore.load({ limit: 100 });

		return () => {
			isImmersive.set(false);
			document.body.style.overflow = '';
		};
	});

	$effect(() => {
		const _trigger =
			liveHistoryFilterStore.filterType +
			liveHistoryFilterStore.customRange.start +
			liveHistoryFilterStore.customRange.end;
		if (mounted && memberId) {
			untrack(() => {
				liveHistoryStore.loadGlobalMemberHistory(memberId, 1, true);
				liveHistoryStore.loadGlobalMemberStats(memberId);
			});
		}
	});

	function handleIntersect() {
		if (isLoading || !hasMore || !memberId) return;
		liveHistoryStore.loadGlobalMemberHistory(memberId, pagination.page + 1);
	}

	function formatDate(dateStr: string) {
		return formatLiveDate(dateStr, locale.value);
	}
</script>

<SEO title={displayName()} path={`${basePath}/${memberId}`} />

<div
	role="presentation"
	class="fixed inset-0 bg-gradient-to-b from-pink-50/50 via-white to-white dark:from-zinc-950 dark:via-zinc-950 dark:to-zinc-900 flex flex-col overflow-hidden z-[9999]"
	onmousemove={(e) => {
		const { clientX, clientY } = e;
		const { innerWidth, innerHeight } = window;
		mouse.set({ x: clientX / innerWidth - 0.5, y: clientY / innerHeight - 0.5 });
	}}
>
	<AppBackground interactive={true} bind:mouse bind:scrollY />

	<HistoryTopBar
		title={displayName()}
		subtitle={t('liveHistory.liveHistory')}
		icon={History}
		iconColor="text-red-500"
		showDateFilter={true}
	/>

	<!-- Main Content -->
	<div class="flex-1 overflow-y-auto" onscroll={(e) => (scrollY = e.currentTarget.scrollTop)}>
		<div class="max-w-7xl mx-auto px-4 sm:px-6 pt-6 pb-32 relative z-10">
			<!-- Member Stats -->
			{#if stats}
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
					<LiveStatCard
						title={t('liveHistory.totalLives')}
						value={`${stats.total_lives} ${t('liveHistory.times')}`}
						icon={PlaySquare}
						color="red"
					/>
					<LiveStatCard
						title={t('liveHistory.totalDuration')}
						value={formatDurationSeconds(stats.total_duration, true)}
						icon={Clock}
						color="amber"
					/>

					<LiveStatCard title={t('liveHistory.totalLivePlatform')} icon={Smartphone} color="blue">
						{#snippet subtitle()}
							<div class="flex items-center gap-3 flex-wrap mt-1">
								{#each Object.entries(stats.platform_counts || {}) as [platform, count]}
									<div class="flex items-center gap-1.5">
										<PlatformLogo {platform} size="sm" />
										<span class="text-sm font-bold text-slate-700 dark:text-zinc-300">{count}x</span
										>
									</div>
								{/each}
							</div>
						{/snippet}
					</LiveStatCard>

					<LiveStatCard
						title={t('liveHistory.longestLive')}
						value={stats.longest_live
							? formatDurationSeconds(stats.longest_live.duration, true)
							: '-'}
						icon={Activity}
						color="emerald"
					>
						{#snippet subtitle()}
							{#if stats.longest_live}
								<div class="flex items-center gap-2 mt-1 min-w-0">
									{#if stats.longest_live.platform}
										<div class="shrink-0">
											<PlatformLogo platform={stats.longest_live.platform} size="sm" />
										</div>
									{/if}
									{#if stats.longest_live.started_at}
										<span class="text-[10px] text-zinc-400 dark:text-zinc-500 truncate"
											>{formatDate(stats.longest_live.started_at)}</span
										>
									{/if}
								</div>
							{/if}
						{/snippet}
					</LiveStatCard>
				</div>
			{/if}

			<div class="flex items-center gap-2 mb-6">
				<History class="w-6 h-6 text-red-500" />
				<h2 class="text-2xl font-black text-slate-800 dark:text-white">
					{t('liveHistory.recentHistory')}
				</h2>
			</div>

			{#if isLoading && historyList.length === 0}
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					{#each Array(6) as _}
						<LiveHistoryItemSkeleton />
					{/each}
				</div>
			{:else if historyList.length === 0}
				<EmptyState
					icon={History}
					title={t('liveHistory.noHistory')}
					description={t('liveHistory.noHistoryDesc')}
				/>
			{:else}
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					{#each historyList as item (item._id)}
						<LiveHistoryItemCard
							href={item.status === 'live'
								? `${baseLivePath}/${item.platform}/${item.live_id}`
								: `${basePath}/${item.member?.id || ''}`}
							mode="global"
							memberImage={item.platform === 'showroom'
								? item.member?.img || item.image
								: item.image || item.member?.img}
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
