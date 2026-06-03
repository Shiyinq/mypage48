<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { liveHistoryStore } from '$lib/stores/liveHistory.svelte';
	import {
		History,
		ChevronLeft,
		Tv,
		Clock,
		Calendar,
		PlaySquare,
		Smartphone,
		Activity
	} from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { isImmersive } from '$lib/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';
	import { spring } from 'svelte/motion';
	import AnimatedBackground from '$lib/components/common/AnimatedBackground.svelte';
	import { membersStore } from '$lib/stores/theater.svelte';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import { OptimizedImage } from '$lib/components/common';
	import { EmptyState } from '$lib/components';
	import PlatformLogo from '$lib/components/live/PlatformLogo.svelte';
	import { formatDurationSeconds, formatTimeAgo } from '$lib/utils/time';

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
		const localeMap: Record<string, string> = {
			id: 'id-ID',
			en: 'en-US',
			ja: 'ja-JP'
		};
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

<SEO title={displayName()} path={`/theater/live/history/members/${memberId}`} />

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
	<AnimatedBackground interactive={true} bind:mouse bind:scrollY />

	<!-- Top Bar -->
	<div
		class="h-14 border-b border-gray-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md flex items-center justify-between px-4 z-[10000] shrink-0"
	>
		<a href="/theater/live/history/members" class="flex items-center gap-3 cursor-pointer group">
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
		</a>
	</div>

	<!-- Main Content -->
	<div class="flex-1 overflow-y-auto" onscroll={(e) => (scrollY = e.currentTarget.scrollTop)}>
		<div class="max-w-7xl mx-auto px-4 sm:px-6 pt-6 pb-32 relative z-10">
			<!-- Member Stats -->
			{#if stats}
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
					<div
						class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 flex items-center gap-4 hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
					>
						<div
							class="w-11 h-11 bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400 rounded-full flex items-center justify-center shrink-0"
						>
							<PlaySquare size={22} />
						</div>
						<div>
							<p
								class="text-xs text-zinc-500 dark:text-zinc-400 font-medium uppercase tracking-wider"
							>
								{t('liveHistory.totalLives')}
							</p>
							<p class="text-xl font-black truncate">
								{stats.total_lives}
								{t('liveHistory.times')}
							</p>
						</div>
					</div>

					<div
						class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 flex items-center gap-4 hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
					>
						<div
							class="w-11 h-11 bg-amber-100 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400 rounded-full flex items-center justify-center shrink-0"
						>
							<Clock size={22} />
						</div>
						<div>
							<p
								class="text-xs text-zinc-500 dark:text-zinc-400 font-medium uppercase tracking-wider"
							>
								{t('liveHistory.totalDuration')}
							</p>
							<p class="text-xl font-black truncate">{formatDuration(stats.total_duration)}</p>
						</div>
					</div>

					<div
						class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 flex items-center gap-4 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 min-w-0"
					>
						<div
							class="w-11 h-11 bg-blue-100 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400 rounded-full flex items-center justify-center shrink-0"
						>
							<Smartphone size={22} />
						</div>
						<div class="min-w-0">
							<p
								class="text-xs text-zinc-500 dark:text-zinc-400 font-medium uppercase tracking-wider truncate"
							>
								{t('liveHistory.totalLivePlatform')}
							</p>
							<div class="flex items-center gap-3 flex-wrap mt-1">
								{#each Object.entries(stats.platform_counts || {}) as [platform, count]}
									<div class="flex items-center gap-1.5">
										<PlatformLogo {platform} size="sm" />
										<span class="text-sm font-bold text-slate-700 dark:text-zinc-300">{count}x</span
										>
									</div>
								{/each}
							</div>
						</div>
					</div>

					<div
						class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 flex items-center gap-4 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 min-w-0"
					>
						<div
							class="w-11 h-11 bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 rounded-full flex items-center justify-center shrink-0"
						>
							<Activity size={22} />
						</div>
						<div class="min-w-0">
							<p
								class="text-xs text-zinc-500 dark:text-zinc-400 font-medium uppercase tracking-wider"
							>
								{t('liveHistory.longestLive')}
							</p>
							<p class="text-xl font-black truncate">
								{stats.longest_live ? formatDuration(stats.longest_live.duration) : '-'}
							</p>
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
						</div>
					</div>
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
						<a
							href={item.status === 'live'
								? `/theater/live/${item.platform}/${item.live_id}`
								: `/theater/live/history/members/${item.member?.id || ''}`}
							class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 flex flex-col gap-3 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group block"
						>
							<div
								class="absolute -right-4 -bottom-4 opacity-[0.03] dark:opacity-[0.02] group-hover:opacity-[0.05] transition-opacity pointer-events-none"
							>
								<History size={100} />
							</div>

							<div class="flex items-center justify-between">
								<div class="flex items-center gap-2 flex-wrap">
									{#if item.status === 'live'}
										<div
											class="flex items-center gap-1 bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 px-2 py-0.5 rounded-md text-[10px] font-bold"
										>
											<div class="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></div>
											<span>LIVE</span>
										</div>
									{:else}
										<div
											class="flex items-center gap-1.5 text-xs font-medium text-zinc-500 dark:text-zinc-400"
										>
											<History size={12} />
											<span>{formatTimeAgo(item.start_at, t)}</span>
										</div>
									{/if}
								</div>

								<div class="flex items-center gap-2">
									<div
										class="flex items-center gap-1 text-xs font-bold text-slate-700 dark:text-zinc-300"
									>
										<span>{item.view_num.toLocaleString()}</span>
										<span class="text-[10px] text-zinc-400 font-medium uppercase tracking-wider"
											>{t('liveHistory.views')}</span
										>
									</div>
									<PlatformLogo platform={item.platform} size="sm" />
								</div>
							</div>

							<div class="flex items-start gap-4 mt-2 z-10">
								<div
									class="w-16 h-16 rounded-xl bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center shrink-0 overflow-hidden shadow-sm"
								>
									{#if item.member?.img || item.image}
										<OptimizedImage
											src={getExternalMediaUrl(
												(item.platform === 'showroom'
													? item.member?.img || item.image
													: item.image || item.member?.img) || ''
											)}
											alt={item.member?.name}
											class="w-full h-full object-cover"
										/>
									{:else}
										<Tv size={20} class="text-zinc-400" />
									{/if}
								</div>
								<div class="flex flex-col min-w-0 flex-1">
									<div
										class="flex items-center gap-1.5 text-xs font-medium text-zinc-500 dark:text-zinc-400 mb-0.5"
									>
										<Calendar size={12} />
										<span>{formatDate(item.start_at)}</span>
									</div>
									<span
										class="text-lg font-black text-slate-900 dark:text-white truncate leading-tight"
										title={item.member?.name}>{item.member?.name}</span
									>
									{#if item.title}
										<span
											class="text-sm font-medium text-zinc-600 dark:text-zinc-300 line-clamp-1 mt-0.5"
											title={item.title}>{item.title}</span
										>
									{/if}
									{#if item.status !== 'live'}
										<div
											class="flex items-center gap-1.5 mt-1.5 text-xs font-bold text-zinc-500 dark:text-zinc-400"
										>
											<Clock size={12} />
											<span>{item.duration ? formatDurationSeconds(item.duration) : 'Ended'}</span>
										</div>
									{/if}
								</div>
							</div>
						</a>
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
