<script lang="ts">
	import { onMount } from 'svelte';
	import { liveHistoryStore } from '$lib/stores/liveHistory.svelte';
	import { EmptyState } from '$lib/components';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import {
		History,
		Clock,
		ChevronLeft,
		Trophy,
		Users,
		Smartphone,
		Eye,
		PlaySquare
	} from 'lucide-svelte';
	import { isImmersive } from '$lib/stores';
	import AnimatedBackground from '$lib/components/common/AnimatedBackground.svelte';
	import { spring } from 'svelte/motion';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';
	import { formatTimeAgo } from '$lib/utils/time';

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
		isImmersive.set(true);
		document.body.style.overflow = 'hidden';
		loadHistory(1, true);
		liveHistoryStore.loadGlobalStats();

		return () => {
			isImmersive.set(false);
			document.body.style.overflow = '';
		};
	});

	async function loadHistory(page: number, force: boolean = false) {
		await liveHistoryStore.loadGlobal(page, force);
		if (force) initialLoading = false;
	}

	function handleIntersect() {
		if (!mounted || isLoading || !hasMore) return;
		loadHistory(pagination.page + 1);
	}

	function parseUTCDate(dateStr: string) {
		const timePart = dateStr.split('T')[1] || '';
		if (!dateStr.endsWith('Z') && !timePart.includes('+') && !timePart.includes('-')) {
			return new Date(dateStr + 'Z');
		}
		return new Date(dateStr);
	}

	function formatDate(dateStr: string) {
		const localeMap: Record<string, string> = { id: 'id-ID', en: 'en-US', ja: 'ja-JP' };
		return new Intl.DateTimeFormat(localeMap[locale.value] || 'id-ID', {
			dateStyle: 'medium',
			timeStyle: 'short'
		}).format(parseUTCDate(dateStr));
	}

	function formatDuration(seconds: number) {
		const h = Math.floor(seconds / 3600);
		const m = Math.floor((seconds % 3600) / 60);
		const s = Math.floor(seconds % 60);
		if (h > 0) return `${h}h ${m}m ${s}s`;
		if (m > 0) return `${m}m ${s}s`;
		return `${s}s`;
	}
</script>

<SEO
	title={t('liveHistory.globalTitle')}
	path={basePath}
	description={t('liveHistory.globalSubtitle')}
/>

<div
	role="presentation"
	class="fixed inset-0 bg-gradient-to-b from-slate-50/50 via-white to-white dark:from-zinc-950 dark:via-zinc-950 dark:to-zinc-900 flex flex-col overflow-hidden z-[9999]"
	onmousemove={(e) => {
		const { clientX, clientY } = e;
		const { innerWidth, innerHeight } = window;
		mouse.set({ x: clientX / innerWidth - 0.5, y: clientY / innerHeight - 0.5 });
	}}
>
	<AnimatedBackground interactive={true} bind:mouse bind:scrollY />

	<!-- Top Bar -->
	<div
		class="h-14 border-b border-gray-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md flex items-center justify-between px-4 z-[10000] shrink-0"
	>
		<button
			onclick={() => history.back()}
			class="flex items-center gap-3 cursor-pointer group text-left"
		>
			<div
				class="flex items-center justify-center w-8 h-8 rounded-full group-hover:bg-gray-100 dark:group-hover:bg-zinc-800 text-slate-600 dark:text-zinc-400 transition-colors shrink-0"
			>
				<ChevronLeft size={20} />
			</div>
			<div class="flex flex-col min-w-0">
				<h1
					class="text-sm font-bold text-slate-900 dark:text-white truncate flex items-center gap-1.5"
				>
					<History size={14} class="text-red-500" />
					{t('liveHistory.globalTitle')}
				</h1>
				<p class="text-[10px] text-slate-500 dark:text-zinc-400 truncate font-medium">
					{t('liveHistory.globalSubtitle')}
				</p>
			</div>
		</button>
	</div>

	<!-- Main Content -->
	<div class="flex-1 overflow-y-auto" onscroll={(e) => (scrollY = e.currentTarget.scrollTop)}>
		<div class="max-w-7xl mx-auto px-4 sm:px-6 pt-6 pb-32 relative z-10">
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
						value={formatDuration(globalStats.total_duration)}
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

					{#if globalStats.highest_view_live}
						<LiveStatCard
							title={t('liveHistory.highestViews')}
							value={`${globalStats.highest_view_live.duration.toLocaleString()} ${t('liveHistory.views')}`}
							icon={Eye}
							color="emerald"
						>
							{#snippet subtitle()}
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
							{/snippet}
						</LiveStatCard>
					{/if}
				</div>
			{:else if isLoadingStats}
				<div class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
					{#each Array(4) as _}
						<div
							class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 animate-pulse"
						>
							<div class="flex items-center gap-4">
								<div class="w-11 h-11 bg-zinc-200 dark:bg-zinc-800 rounded-full shrink-0"></div>
								<div class="flex flex-col gap-2 flex-1">
									<div class="h-3 bg-zinc-200 dark:bg-zinc-800 rounded w-16"></div>
									<div class="h-5 bg-zinc-200 dark:bg-zinc-800 rounded w-12"></div>
								</div>
							</div>
						</div>
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

			{#if initialLoading}
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					{#each Array(6) as _}
						<div
							class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 flex flex-col gap-3"
						>
							<div class="flex items-center justify-between">
								<div class="h-3 bg-zinc-200 dark:bg-zinc-800 rounded w-24 animate-pulse"></div>
								<div class="w-16 h-4 bg-zinc-200 dark:bg-zinc-800 rounded animate-pulse"></div>
							</div>
							<div class="flex items-center gap-3 mt-2">
								<div
									class="w-16 h-16 rounded-xl bg-zinc-200 dark:bg-zinc-800 animate-pulse shrink-0"
								></div>
								<div class="flex flex-col gap-2 w-full">
									<div class="h-5 bg-zinc-200 dark:bg-zinc-800 rounded w-2/3 animate-pulse"></div>
									<div class="h-4 bg-zinc-200 dark:bg-zinc-800 rounded w-1/3 animate-pulse"></div>
								</div>
							</div>
						</div>
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
							href={item.status === 'live'
								? `${baseLivePath}/${item.platform}/${item.live_id}`
								: `${basePath}/members/${item.member?.id || ''}`}
							mode="global"
							memberImage={item.platform === 'showroom'
								? item.member?.img || item.image
								: item.image || item.member?.img}
							memberName={item.member?.name}
							liveTitle={item.title}
							platform={item.platform}
							dateStr={formatDate(item.start_at)}
							timeStr={formatTimeAgo(item.start_at, t)}
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
