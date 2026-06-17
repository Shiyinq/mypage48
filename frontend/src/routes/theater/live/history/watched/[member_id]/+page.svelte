<script lang="ts">
	import { page } from '$app/stores';
	import { untrack, onMount } from 'svelte';
	import { liveHistoryStore } from '$lib/stores/liveHistory.svelte';
	import { liveHistoryFilterStore } from '$lib/stores/liveHistoryFilter.svelte';
	import { EmptyState } from '$lib/components';
	import { History, Clock, Activity, PlaySquare, Smartphone } from 'lucide-svelte';
	import { formatLiveDate, formatDurationSeconds, parseUTCDate } from '$lib/utils/time';
	import HistoryTopBar from '$lib/components/live/history/shared/HistoryTopBar.svelte';
	import LiveHistoryItemSkeleton from '$lib/components/live/history/shared/LiveHistoryItemSkeleton.svelte';
	import LiveStatCard from '$lib/components/live/history/shared/LiveStatCard.svelte';
	import LiveHistoryItemCard from '$lib/components/live/history/shared/LiveHistoryItemCard.svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';
	import PlatformLogo from '$lib/components/live/PlatformLogo.svelte';
	import { isImmersive } from '$lib/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { spring } from 'svelte/motion';
	import AppBackground from '$lib/components/common/AppBackground.svelte';
	import { membersStore } from '$lib/stores/theater.svelte';

	let memberId = $derived($page.params.member_id as string);
	let mounted = $state(false);
	let scrollY = $state(0);
	let mouse = $state(spring({ x: 0, y: 0 }, { stiffness: 0.1, damping: 0.25 }));

	const { t, locale } = useTranslation();

	let list = $derived(liveHistoryStore.list);
	let pagination = $derived(liveHistoryStore.pagination);
	let stats = $derived(liveHistoryStore.memberStats[memberId]);
	let isLoading = $derived(liveHistoryStore.isLoading);
	let hasMore = $derived(pagination.current_page < pagination.last_page);
	let memberName = $derived(list.length > 0 ? list[0].member_name : memberId);

	onMount(() => {
		mounted = true;
		isImmersive.set(true);
		document.body.style.overflow = 'hidden';
		membersStore.load({ limit: 100 });

		return () => {
			isImmersive.set(false);
			document.body.style.overflow = '';
			liveHistoryStore.reset();
		};
	});

	$effect(() => {
		// React to dateRange or memberId changes
		const _range = liveHistoryFilterStore.dateRange;
		if (mounted) {
			untrack(() => {
				loadHistory(1, true);
				liveHistoryStore.loadMemberStats(memberId);
			});
		}
	});

	async function loadHistory(pageIdx: number, force: boolean = false) {
		await liveHistoryStore.load(pageIdx, memberId, force);
	}

	function handleIntersect() {
		if (!mounted || isLoading || !hasMore) return;
		loadHistory(pagination.current_page + 1);
	}

	function formatDate(dateStr: string) {
		return formatLiveDate(dateStr, locale.value);
	}
</script>

<SEO title={`Live History: ${memberName}`} path={`/theater/live/history/watched/${memberId}`} />

<div
	role="presentation"
	class="fixed inset-0 bg-gradient-to-b from-pink-50/50 via-white to-white dark:from-zinc-950 dark:via-zinc-950 dark:to-zinc-900 flex flex-col overflow-hidden z-[9999]"
	onmousemove={(e) => {
		const { clientX, clientY } = e;
		const { innerWidth, innerHeight } = window;
		const x = clientX / innerWidth - 0.5;
		const y = clientY / innerHeight - 0.5;
		mouse.set({ x, y });
	}}
>
	<AppBackground hideDecorationsOnMobile={true} interactive={true} bind:mouse bind:scrollY />

	<HistoryTopBar
		title={memberName}
		subtitle={t('liveHistory.subtitle')}
		icon={History}
		iconColor="text-red-500"
		showDateFilter={true}
	/>

	<!-- Main Content -->
	<div class="flex-1 overflow-y-auto" onscroll={(e) => (scrollY = e.currentTarget.scrollTop)}>
		<div class="max-w-7xl mx-auto px-4 sm:px-6 pt-4 sm:pt-6 pb-32 relative z-10">
			<!-- Member Stats -->
			{#if stats}
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
					<LiveStatCard
						title={t('liveHistory.totalWatches')}
						value={`${stats.total_watches} ${t('liveHistory.times')}`}
						icon={PlaySquare}
						color="red"
					/>

					<LiveStatCard
						title={t('liveHistory.totalDuration')}
						value={formatDurationSeconds(stats.total_duration, true)}
						icon={Clock}
						color="amber"
					/>

					<LiveStatCard title={t('liveHistory.platformWatches')} icon={Smartphone} color="blue">
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
						title={t('liveHistory.longestWatch')}
						value={stats.longest_watch
							? formatDurationSeconds(stats.longest_watch.duration, true)
							: '-'}
						icon={Activity}
						color="emerald"
					>
						{#snippet subtitle()}
							{#if stats.longest_watch}
								<div class="flex items-center gap-2 mt-1 min-w-0">
									{#if stats.longest_watch.platform}
										<div class="shrink-0">
											<PlatformLogo platform={stats.longest_watch.platform} size="sm" />
										</div>
									{/if}
									{#if stats.longest_watch.started_at}
										<span class="text-[10px] text-zinc-400 dark:text-zinc-500 truncate"
											>{formatDate(stats.longest_watch.started_at)}</span
										>
									{/if}
								</div>
							{/if}
						{/snippet}
					</LiveStatCard>
				</div>
			{/if}

			<!-- Detail List -->
			<h2 class="text-xl font-bold mb-4 flex items-center gap-2">
				<History class="text-red-500" size={24} />
				{t('liveHistory.recentHistory')}
			</h2>

			{#if isLoading && list.length === 0}
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					{#each Array(6) as _}
						<LiveHistoryItemSkeleton />
					{/each}
				</div>
			{:else if list.length === 0}
				<EmptyState
					icon={History}
					title={t('liveHistory.noHistory')}
					description={t('liveHistory.noHistoryDesc')}
				/>
			{:else}
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					{#each list as item (item._id)}
						<LiveHistoryItemCard
							href="#"
							mode="watched"
							memberName={item.member_name}
							liveTitle={item.live_title}
							platform={item.platform}
							dateStr={formatDate(item.last_updated_at)}
							timeStr={parseUTCDate(item.last_updated_at).toLocaleTimeString(
								locale.value === 'en' ? 'en-US' : locale.value === 'ja' ? 'ja-JP' : 'id-ID'
							)}
							duration={item.duration}
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
