<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { liveHistoryStore } from '$lib/stores/liveHistory.svelte';
	import { EmptyState } from '$lib/components';
	import { Tv, History, Clock, Activity, PlaySquare, ChevronLeft, Smartphone } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';
	import PlatformLogo from '$lib/components/live/PlatformLogo.svelte';
	import { isImmersive } from '$lib/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { spring } from 'svelte/motion';
	import AnimatedBackground from '$lib/components/common/AnimatedBackground.svelte';
	import { membersStore } from '$lib/stores/theater.svelte';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import { OptimizedImage } from '$lib/components/common';

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
	let memberInfo = $derived(
		membersStore.list.find(
			(m) =>
				String(m.id) === String(memberId) ||
				m.name === memberName ||
				m.nickname === memberName ||
				(m.socials?.idn_app && String(memberId).includes(m.socials.idn_app)) ||
				(m.socials?.showroom && String(memberId) === String(m.socials.showroom))
		)
	);

	onMount(() => {
		mounted = true;
		isImmersive.set(true);
		document.body.style.overflow = 'hidden';
		loadHistory(1);
		liveHistoryStore.loadMemberStats(memberId);
		membersStore.load({ limit: 100 });

		return () => {
			isImmersive.set(false);
			document.body.style.overflow = '';
			liveHistoryStore.reset();
		};
	});

	// Re-load if memberId changes
	$effect(() => {
		if (mounted && liveHistoryStore.currentMemberFilter !== memberId) {
			loadHistory(1, true);
			liveHistoryStore.loadMemberStats(memberId);
		}
	});

	async function loadHistory(pageIdx: number, force: boolean = false) {
		await liveHistoryStore.load(pageIdx, memberId, force);
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
</script>

<SEO title={`Live History: ${memberName}`} path={`/theater/live/history/${memberId}`} />

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
		<div class="flex items-center gap-4">
			<a
				href="/theater/live/history"
				class="flex items-center gap-2 text-slate-900 dark:text-white hover:text-red-600 transition-colors"
			>
				<ChevronLeft size={20} />
				<span class="font-black tracking-tighter text-lg"
					>Watch <span class="text-red-600 italic">History</span></span
				>
			</a>
			<div class="hidden sm:block h-4 w-px bg-gray-200 dark:bg-zinc-800"></div>
			<div
				class="hidden xs:flex items-center gap-2 px-3 py-1 bg-red-50 dark:bg-red-500/10 rounded-full"
			>
				<Tv size={14} class="text-red-600" />
				<span
					class="text-[10px] font-black uppercase tracking-widest text-red-600 dark:text-red-400"
					>{memberName}</span
				>
			</div>
		</div>
	</div>

	<!-- Main Content -->
	<div class="flex-1 overflow-y-auto" onscroll={(e) => (scrollY = e.currentTarget.scrollTop)}>
		<div class="max-w-7xl mx-auto px-4 sm:px-6 pt-6 pb-32 relative z-10">
			<!-- Header Title -->
			<div class="flex items-center gap-4 mb-8">
				<div
					class="w-16 h-16 rounded-2xl bg-white dark:bg-zinc-900 shadow-xl border border-gray-100 dark:border-zinc-800 flex items-center justify-center shrink-0 -rotate-6 overflow-hidden"
				>
					{#if memberInfo?.img}
						<OptimizedImage
							src={getExternalMediaUrl(memberInfo.img)}
							alt={memberName}
							class="w-full h-full object-cover"
						/>
					{:else}
						<Tv size={32} class="text-red-500" />
					{/if}
				</div>
				<div>
					<h1 class="text-3xl font-black text-slate-900 dark:text-white tracking-tight">
						{memberName}
					</h1>
					<p class="text-slate-500 dark:text-zinc-400 text-sm font-medium mt-1">
						{t('liveHistory.subtitle')}
					</p>
				</div>
			</div>

			<!-- Member Stats -->
			{#if stats}
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
					<div
						class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 flex items-center gap-4 hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
					>
						<div
							class="w-12 h-12 bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400 rounded-full flex items-center justify-center shrink-0"
						>
							<PlaySquare size={24} />
						</div>
						<div>
							<p
								class="text-sm text-zinc-500 dark:text-zinc-400 font-medium uppercase tracking-wider"
							>
								{t('liveHistory.totalWatches')}
							</p>
							<p class="text-2xl font-black">{stats.total_watches} {t('liveHistory.times')}</p>
						</div>
					</div>

					<div
						class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 flex items-center gap-4 hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
					>
						<div
							class="w-12 h-12 bg-amber-100 dark:bg-amber-500/20 text-amber-600 dark:text-amber-400 rounded-full flex items-center justify-center shrink-0"
						>
							<Clock size={24} />
						</div>
						<div>
							<p
								class="text-sm text-zinc-500 dark:text-zinc-400 font-medium uppercase tracking-wider"
							>
								{t('liveHistory.totalDuration')}
							</p>
							<p class="text-2xl font-black">{formatDuration(stats.total_duration)}</p>
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
						class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 flex items-center gap-4 hover:shadow-lg hover:-translate-y-1 transition-all duration-300 min-w-0"
					>
						<div
							class="w-12 h-12 bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 rounded-full flex items-center justify-center shrink-0"
						>
							<Activity size={24} />
						</div>
						<div class="min-w-0">
							<p
								class="text-sm text-zinc-500 dark:text-zinc-400 font-medium uppercase tracking-wider"
							>
								{t('liveHistory.longestWatch')}
							</p>
							<p class="text-2xl font-black">
								{stats.longest_watch ? formatDuration(stats.longest_watch.duration) : '-'}
							</p>
							{#if stats.longest_watch}
								<div class="flex items-center gap-1.5 mt-1 min-w-0">
									{#if stats.longest_watch.live_title}
										<span
											class="text-xs font-medium text-zinc-500 dark:text-zinc-400 truncate"
											title={stats.longest_watch.live_title}>{stats.longest_watch.live_title}</span
										>
									{/if}
									{#if stats.longest_watch.platform}
										<div class="shrink-0">
											<PlatformLogo platform={stats.longest_watch.platform} size="sm" />
										</div>
									{/if}
								</div>
								{#if stats.longest_watch.started_at}
									<div class="mt-0.5">
										<span class="text-[10px] text-zinc-400 dark:text-zinc-500"
											>{formatDate(stats.longest_watch.started_at)}</span
										>
									</div>
								{/if}
							{/if}
						</div>
					</div>
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
						<div
							class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 flex flex-col gap-4"
						>
							<div class="flex items-center justify-between">
								<div class="h-4 bg-zinc-200 dark:bg-zinc-800 rounded w-32 animate-pulse"></div>
								<div class="w-12 h-4 bg-zinc-200 dark:bg-zinc-800 rounded animate-pulse"></div>
							</div>
							<div class="h-5 bg-zinc-200 dark:bg-zinc-800 rounded w-full animate-pulse"></div>
							<div
								class="mt-auto pt-2 flex items-center justify-between border-t border-gray-100 dark:border-zinc-800"
							>
								<div class="w-16 h-6 bg-zinc-200 dark:bg-zinc-800 rounded animate-pulse"></div>
								<div class="w-16 h-3 bg-zinc-200 dark:bg-zinc-800 rounded animate-pulse"></div>
							</div>
						</div>
					{/each}
				</div>
			{:else if list.length === 0}
				<EmptyState
					icon={Tv}
					title={t('liveHistory.noHistory')}
					description={`Kamu belum pernah menonton live stream ${memberName} yang tercatat.`}
				/>
			{:else}
				<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
					{#each list as item (item._id)}
						<div
							class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-xl p-4 flex flex-col gap-3 hover:border-red-500/50 hover:shadow-lg transition-all"
						>
							<div class="flex items-center justify-between">
								<span class="text-xs font-bold text-zinc-500 dark:text-zinc-400"
									>{formatDate(item.started_at)}</span
								>
								<PlatformLogo platform={item.platform} size="sm" />
							</div>

							{#if item.live_title}
								<span class="text-sm font-black text-slate-900 dark:text-white line-clamp-2"
									>{item.live_title}</span
								>
							{/if}

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
						</div>
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
