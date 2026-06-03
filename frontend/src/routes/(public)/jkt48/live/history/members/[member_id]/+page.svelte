<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { liveHistoryStore } from '$lib/stores/liveHistory.svelte';
	import { History, ChevronLeft, Clock, PlaySquare, Smartphone, Activity } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { isImmersive } from '$lib/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';
	import { spring } from 'svelte/motion';
	import AnimatedBackground from '$lib/components/common/AnimatedBackground.svelte';
	import { membersStore } from '$lib/stores/theater.svelte';
	import { EmptyState } from '$lib/components';
	import PlatformLogo from '$lib/components/live/PlatformLogo.svelte';
	import { formatTimeAgo } from '$lib/utils/time';

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

	onMount(() => {
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

	function handleIntersect() {
		if (isLoading || !hasMore || !memberId) return;
		liveHistoryStore.loadGlobalMemberHistory(memberId, pagination.page + 1);
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
					{displayName()}
				</h1>
				<p class="text-[10px] text-slate-500 dark:text-zinc-400 truncate font-medium">
					{t('liveHistory.liveHistory')} · {pagination.total}
					{t('liveHistory.times')}
				</p>
			</div>
		</button>
	</div>

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
						value={formatDuration(stats.total_duration)}
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
						value={stats.longest_live ? formatDuration(stats.longest_live.duration) : '-'}
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
