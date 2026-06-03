<script lang="ts">
	import { onMount } from 'svelte';
	import { liveHistoryStore } from '$lib/stores/liveHistory.svelte';
	import { EmptyState } from '$lib/components';
	import {
		Tv,
		History,
		Clock,
		ChevronLeft,
		PlaySquare,
		Trophy,
		Activity,
		Smartphone,
		Users,
		ChevronRight
	} from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';
	import PlatformLogo from '$lib/components/live/PlatformLogo.svelte';
	import { goto } from '$app/navigation';
	import { isImmersive } from '$lib/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { spring } from 'svelte/motion';
	import AnimatedBackground from '$lib/components/common/AnimatedBackground.svelte';
	import { membersStore } from '$lib/stores/theater.svelte';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import { OptimizedImage } from '$lib/components/common';
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
		isImmersive.set(true);
		document.body.style.overflow = 'hidden';
		loadHistory(1);
		liveHistoryStore.loadOverallStats();
		membersStore.load({ limit: 100 });

		return () => {
			isImmersive.set(false);
			document.body.style.overflow = '';
		};
	});

	async function loadHistory(page: number) {
		await liveHistoryStore.load(page);
	}

	function handleIntersect() {
		if (!mounted || isLoading || !hasMore) return;
		loadHistory(pagination.current_page + 1);
	}

	function formatDuration(seconds: number) {
		const h = Math.floor(seconds / 3600);
		const m = Math.floor((seconds % 3600) / 60);
		const s = Math.floor(seconds % 60);
		if (h > 0) return `${h}h ${m}m ${s}s`;
		if (m > 0) return `${m}m ${s}s`;
		return `${s}s`;
	}

	function parseUTCDate(dateStr: string) {
		// Pymongo often returns naive UTC datetimes, serialized as "YYYY-MM-DDTHH:MM:SS".
		// Check if timezone info exists (+, -, or Z) at the end of the string.
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

	function getMemberImage(item: LiveHistory) {
		const member = membersStore.list.find(
			(m) =>
				String(m.id) === String(item.member_id) ||
				m.name === item.member_name ||
				m.nickname === item.member_name ||
				(m.socials?.idn_app && String(item.member_id).includes(m.socials.idn_app)) ||
				(m.socials?.showroom && String(item.member_id) === String(m.socials.showroom))
		);
		return member?.img;
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
	<AnimatedBackground interactive={true} bind:mouse bind:scrollY />

	<!-- Top Bar -->
	<div
		class="h-14 border-b border-gray-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md flex items-center justify-between px-4 z-[10000] shrink-0"
	>
		<div class="flex items-center gap-3">
			<a
				href="/theater/live"
				class="flex items-center justify-center w-8 h-8 rounded-full hover:bg-gray-100 dark:hover:bg-zinc-800 text-slate-600 dark:text-zinc-400 transition-colors shrink-0"
			>
				<ChevronLeft size={20} />
			</a>
			<div class="flex flex-col min-w-0">
				<h1
					class="text-sm font-bold text-slate-900 dark:text-white truncate flex items-center gap-1.5"
				>
					<History size={14} class="text-red-500" />
					{t('liveHistory.title')}
				</h1>
				<p class="text-[10px] text-slate-500 dark:text-zinc-400 truncate font-medium">
					{t('liveHistory.subtitle')}
				</p>
			</div>
		</div>
	</div>

	<!-- Main Content -->
	<div class="flex-1 overflow-y-auto" onscroll={(e) => (scrollY = e.currentTarget.scrollTop)}>
		<div class="max-w-7xl mx-auto px-4 sm:px-6 pt-6 pb-32 relative z-10">
			<!-- Overall Stats -->
			{#if overallStats}
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
					<div
						class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 flex items-center gap-4 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 min-w-0"
					>
						<div
							class="w-12 h-12 bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400 rounded-full flex items-center justify-center shrink-0"
						>
							<PlaySquare size={24} />
						</div>
						<div class="min-w-0">
							<p
								class="text-sm text-zinc-500 dark:text-zinc-400 font-medium uppercase tracking-wider truncate"
							>
								{t('liveHistory.totalWatches')}
							</p>
							<p class="text-xl sm:text-2xl font-black truncate">
								{totalWatches}
								{t('liveHistory.times')}
							</p>
						</div>
					</div>

					<div
						class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 flex items-center gap-4 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 min-w-0"
					>
						<div
							class="w-12 h-12 bg-amber-100 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400 rounded-full flex items-center justify-center shrink-0"
						>
							<Clock size={24} />
						</div>
						<div class="min-w-0">
							<p
								class="text-sm text-zinc-500 dark:text-zinc-400 font-medium uppercase tracking-wider truncate"
							>
								{t('liveHistory.totalDuration')}
							</p>
							<p class="text-xl sm:text-2xl font-black truncate">
								{formatDuration(overallStats.total_duration)}
							</p>
						</div>
					</div>

					<div
						class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 flex items-center gap-4 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 min-w-0"
					>
						<div
							class="w-12 h-12 bg-pink-100 dark:bg-pink-500/20 text-pink-600 dark:text-pink-400 rounded-full flex items-center justify-center shrink-0"
						>
							<Users size={24} />
						</div>
						<div class="min-w-0">
							<p
								class="text-sm text-zinc-500 dark:text-zinc-400 font-medium uppercase tracking-wider truncate"
							>
								{t('liveHistory.membersWatched')}
							</p>
							<p class="text-xl sm:text-2xl font-black truncate">
								{Object.keys(overallStats.member_counts).length}
							</p>
						</div>
					</div>

					<div
						class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 flex items-center gap-4 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 min-w-0"
					>
						<div
							class="w-12 h-12 bg-blue-100 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400 rounded-full flex items-center justify-center shrink-0"
						>
							<Smartphone size={24} />
						</div>
						<div class="min-w-0">
							<p
								class="text-sm text-zinc-500 dark:text-zinc-400 font-medium uppercase tracking-wider truncate"
							>
								{t('liveHistory.platformWatches')}
							</p>
							<div class="flex items-center gap-3 flex-wrap mt-1">
								{#each Object.entries(overallStats.platform_counts || {}) as [platform, count]}
									<div class="flex items-center gap-1.5">
										<PlatformLogo {platform} size="sm" />
										<span class="text-sm font-bold text-slate-700 dark:text-zinc-300">{count}x</span
										>
									</div>
								{/each}
							</div>
						</div>
					</div>

					<a
						href="/theater/live/history/watched/members"
						class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 flex items-center gap-4 hover:shadow-lg hover:border-purple-500/50 hover:-translate-y-1 transition-all duration-300 min-w-0 sm:col-span-1 lg:col-span-2 group"
					>
						<div
							class="w-12 h-12 bg-purple-100 dark:bg-purple-500/20 text-purple-600 dark:text-purple-400 rounded-full flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform"
						>
							<Trophy size={24} />
						</div>
						<div class="min-w-0 flex-1">
							<p
								class="text-sm text-zinc-500 dark:text-zinc-400 font-medium uppercase tracking-wider truncate"
							>
								{t('liveHistory.mostFrequent')}
							</p>
							<div class="flex items-baseline gap-1.5 truncate">
								<p
									class="text-xl sm:text-2xl font-black truncate group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors"
								>
									{topMemberName}
								</p>
								{#if topMemberCount > 0}
									<span class="text-xs font-bold text-purple-600 dark:text-purple-400 shrink-0"
										>({topMemberCount}x)</span
									>
								{/if}
							</div>
						</div>
						<ChevronRight
							size={20}
							class="text-zinc-400 opacity-0 group-hover:opacity-100 transition-opacity shrink-0 ml-2"
						/>
					</a>

					<div
						class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 flex items-center gap-4 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 min-w-0 sm:col-span-1 lg:col-span-2"
					>
						<div
							class="w-12 h-12 bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 rounded-full flex items-center justify-center shrink-0"
						>
							<Activity size={24} />
						</div>
						<div class="min-w-0">
							<p
								class="text-sm text-zinc-500 dark:text-zinc-400 font-medium uppercase tracking-wider truncate"
							>
								{t('liveHistory.longestWatch')}
							</p>
							<p class="text-xl sm:text-2xl font-black truncate">
								{overallStats.longest_watch
									? formatDuration(overallStats.longest_watch.duration)
									: '-'}
							</p>
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
						</div>
					</div>
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
						<div
							class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 flex flex-col gap-3"
						>
							<div class="flex items-center justify-between">
								<div class="h-3 bg-zinc-200 dark:bg-zinc-800 rounded w-24 animate-pulse"></div>
								<div class="w-16 h-4 bg-zinc-200 dark:bg-zinc-800 rounded animate-pulse"></div>
							</div>
							<div class="flex items-center justify-between mt-2">
								<div class="flex items-center gap-3">
									<div
										class="w-12 h-16 rounded-xl bg-zinc-200 dark:bg-zinc-800 animate-pulse shrink-0"
									></div>
									<div class="flex flex-col gap-2">
										<div class="h-5 bg-zinc-200 dark:bg-zinc-800 rounded w-32 animate-pulse"></div>
										<div class="h-4 bg-zinc-200 dark:bg-zinc-800 rounded w-20 animate-pulse"></div>
									</div>
								</div>
							</div>
						</div>
					{/each}
				</div>
			{:else if list.length === 0}
				<EmptyState
					icon={Tv}
					title={t('liveHistory.noHistory')}
					description={t('liveHistory.noHistoryDesc')}
				/>
			{:else}
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					{#each list as item (item._id)}
						<button
							class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 flex flex-col gap-3 hover:border-red-500/50 hover:shadow-lg transition-all text-left cursor-pointer w-full"
							onclick={() => goto(`/theater/live/history/watched/${item.member_id}`)}
						>
							<div class="flex items-center justify-between">
								<div class="flex flex-col">
									<span class="text-xs font-medium text-zinc-500 dark:text-zinc-400">
										{formatDate(item.last_updated_at)}
									</span>
								</div>
								<PlatformLogo platform={item.platform} size="sm" />
							</div>

							<div class="flex items-center justify-between mt-2">
								<div class="flex items-center gap-3">
									<div
										class="w-12 h-16 rounded-xl bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center shrink-0 overflow-hidden shadow-sm"
									>
										{#if getMemberImage(item)}
											<OptimizedImage
												src={getExternalMediaUrl(getMemberImage(item) || '')}
												alt={item.member_name}
												class="w-full h-full object-cover"
											/>
										{:else}
											<Tv size={20} class="text-red-500" />
										{/if}
									</div>
									<div class="flex flex-col">
										<span class="text-lg font-black">{item.member_name}</span>
										{#if item.live_title}
											<span
												class="text-sm font-medium text-zinc-600 dark:text-zinc-300 line-clamp-1"
												>{item.live_title}</span
											>
										{/if}
									</div>
								</div>
								<ChevronRight size={20} class="text-zinc-400 shrink-0 ml-2" />
							</div>

							<div
								class="mt-auto pt-2 flex items-center justify-between border-t border-gray-100 dark:border-zinc-800"
							>
								<div
									class="flex items-center gap-1.5 bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 px-2 py-1 rounded-md"
								>
									<Clock size={14} />
									<div class="flex items-center gap-1 text-xs">
										<span class="font-medium opacity-70">{t('liveHistory.watchedFor')}</span>
										<span class="font-bold">{formatDuration(item.duration)}</span>
									</div>
								</div>
								<span class="text-[10px] font-medium text-zinc-500 dark:text-zinc-400">
									{parseUTCDate(item.last_updated_at).toLocaleTimeString(
										locale.value === 'en' ? 'en-US' : locale.value === 'ja' ? 'ja-JP' : 'id-ID'
									)}
								</span>
							</div>
						</button>
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
