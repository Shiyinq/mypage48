<script lang="ts">
	import { untrack, onMount } from 'svelte';
	import { liveHistoryStore } from '$lib/stores/liveHistory.svelte';
	import { liveHistoryFilterStore } from '$lib/stores/liveHistoryFilter.svelte';
	import { EmptyState } from '$lib/components';
	import { History, Clock, PlaySquare, Trophy, Activity, Smartphone, Users } from 'lucide-svelte';
	import { formatLiveDate, formatDurationSeconds, parseUTCDate } from '$lib/utils/time';
	import HistoryTopBar from '$lib/components/live/history/shared/HistoryTopBar.svelte';
	import LiveHistoryItemSkeleton from '$lib/components/live/history/shared/LiveHistoryItemSkeleton.svelte';
	import LiveStatCardSkeleton from '$lib/components/live/history/shared/LiveStatCardSkeleton.svelte';
	import LiveStatCard from '$lib/components/live/history/shared/LiveStatCard.svelte';
	import LiveHistoryItemCard from '$lib/components/live/history/shared/LiveHistoryItemCard.svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';
	import PlatformLogo from '$lib/components/live/PlatformLogo.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { spring } from 'svelte/motion';
	import AppBackground from '$lib/components/common/AppBackground.svelte';
	import { membersStore } from '$lib/stores/theater.svelte';
	import type { LiveHistory } from '$lib/types/liveHistory';

	let mounted = $state(false);
	let scrollY = $state(0);
	let mouse = $state(spring({ x: 0, y: 0 }, { stiffness: 0.1, damping: 0.25 }));

	const { t, locale } = useTranslation();

	let list = $derived(liveHistoryStore.list);
	let pagination = $derived(liveHistoryStore.pagination);
	let overallStats = $derived(liveHistoryStore.overallStats);
	let isLoading = $derived(liveHistoryStore.isLoading);
	let hasMore = $derived(pagination.current_page < pagination.last_page);

	let totalWatches = $derived(overallStats?.total_watches || 0);
	let topMemberId = $derived(overallStats?.top_member_id);
	let topMemberCount = $derived(overallStats?.top_member_watches || 0);

	let topMemberName = $derived(
		topMemberId
			? (() => {
					const member = membersStore.list.find(
						(m) =>
							String(m.id) === String(topMemberId) ||
							(m.socials?.idn_app && String(topMemberId).includes(m.socials.idn_app)) ||
							(m.socials?.showroom && String(topMemberId) === String(m.socials.showroom))
					);
					if (member) return member.name;
					return overallStats?.top_member_name || 'Member JKT48';
				})()
			: '-'
	);

	onMount(() => {
		mounted = true;
		membersStore.load({ limit: 100 });
	});

	$effect(() => {
		// React to dateRange changes
		const _range = liveHistoryFilterStore.dateRange;

		if (mounted) {
			untrack(() => {
				loadHistory(1);
				liveHistoryStore.loadOverallStats();
			});
		}
	});

	async function loadHistory(page: number) {
		await liveHistoryStore.load(page);
	}

	function handleIntersect() {
		if (!mounted || isLoading || !hasMore) return;
		loadHistory(pagination.current_page + 1);
	}

	function formatDate(dateStr: string) {
		return formatLiveDate(dateStr, locale.value);
	}

	function getMember(item: LiveHistory) {
		return membersStore.list.find(
			(m) =>
				String(m.id) === String(item.member_id) ||
				m.name === item.member_name ||
				m.nickname === item.member_name ||
				(m.socials?.idn_app && String(item.member_id).includes(m.socials.idn_app)) ||
				(m.socials?.showroom && String(item.member_id) === String(m.socials.showroom))
		);
	}
</script>

<SEO title="Live Watch History" path="/history/lives" />

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
		title={t('liveHistory.title')}
		subtitle={t('liveHistory.subtitle')}
		icon={History}
		iconColor="text-red-500"
		showDateFilter={true}
	/>

	<!-- Main Content -->
	<div class="flex-1 overflow-y-auto" onscroll={(e) => (scrollY = e.currentTarget.scrollTop)}>
		<div class="max-w-7xl mx-auto px-4 sm:px-6 pt-8 sm:pt-10 pb-32 relative z-10">
			<!-- Overall Stats -->
			{#if overallStats}
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
					<LiveStatCard
						title={t('liveHistory.totalWatches')}
						value={`${totalWatches} ${t('liveHistory.times')}`}
						icon={PlaySquare}
						color="red"
					/>

					<LiveStatCard
						title={t('liveHistory.totalDuration')}
						value={formatDurationSeconds(overallStats.total_duration, true)}
						icon={Clock}
						color="amber"
					/>

					<LiveStatCard
						title={t('liveHistory.membersWatched')}
						value={Object.keys(overallStats.member_counts).length}
						icon={Users}
						color="pink"
					/>

					<LiveStatCard title={t('liveHistory.platformWatches')} icon={Smartphone} color="blue">
						{#snippet subtitle()}
							<div class="flex items-center gap-3 flex-wrap mt-1">
								{#each Object.entries(overallStats.platform_counts || {}) as [platform, count]}
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
						title={t('liveHistory.mostFrequent')}
						value={topMemberName}
						icon={Trophy}
						color="purple"
						href="/theater/live/history/watched/members"
						class="sm:col-span-1 lg:col-span-2"
					>
						{#snippet subtitle()}
							{#if topMemberCount > 0}
								<span class="text-xs font-bold text-purple-600 dark:text-purple-400 shrink-0"
									>({topMemberCount}x)</span
								>
							{/if}
						{/snippet}
					</LiveStatCard>

					<LiveStatCard
						title={t('liveHistory.longestWatch')}
						value={overallStats.longest_watch
							? formatDurationSeconds(overallStats.longest_watch.duration, true)
							: '-'}
						icon={Activity}
						color="emerald"
						class="sm:col-span-1 lg:col-span-2"
					>
						{#snippet subtitle()}
							{#if overallStats.longest_watch}
								<div class="flex items-center gap-1.5 mt-0.5 min-w-0">
									{#if overallStats.longest_watch.member_name}
										<span
											class="text-xs font-bold text-emerald-600 dark:text-emerald-400 truncate"
											title={overallStats.longest_watch.member_name}
											>{overallStats.longest_watch.member_name}</span
										>
									{/if}
									{#if overallStats.longest_watch.platform}
										<div class="shrink-0">
											<PlatformLogo platform={overallStats.longest_watch.platform} size="sm" />
										</div>
									{/if}
								</div>
								<div class="flex items-center gap-1.5 mt-0.5 min-w-0">
									{#if overallStats.longest_watch.live_title}
										<span
											class="text-[10px] text-zinc-400 dark:text-zinc-500 truncate"
											title={overallStats.longest_watch.live_title}
											>{overallStats.longest_watch.live_title}</span
										>
									{/if}
									{#if overallStats.longest_watch.started_at}
										<span class="text-[10px] text-zinc-400 dark:text-zinc-500 shrink-0"
											>{formatDate(overallStats.longest_watch.started_at)}</span
										>
									{/if}
								</div>
							{/if}
						{/snippet}
					</LiveStatCard>
				</div>
			{:else if isLoading && !overallStats}
				<div class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
					{#each Array(4) as _}
						<LiveStatCardSkeleton />
					{/each}
				</div>
			{/if}

			<!-- History List -->
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
						{@const member = getMember(item)}
						<LiveHistoryItemCard
							href={`/theater/live/history/watched/${item.member_id}`}
							mode="watched"
							memberImage={member?.img || ''}
							memberImageMedium={member?.img_medium}
							memberImageSmall={member?.img_small}
							blurHash={member?.blurHash}
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
