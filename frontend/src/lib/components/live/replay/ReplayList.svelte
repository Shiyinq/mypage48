<script lang="ts">
	import { onMount } from 'svelte';
	import { fade, slide } from 'svelte/transition';
	import { goto } from '$app/navigation';
	import { replayStore } from '$lib/stores/replay.svelte';
	import { liveNavbarStore } from '$lib/stores/liveNavbar.svelte';
	import { membersStore } from '$lib/stores/theater.svelte';
	import OptimizedImage from '$lib/components/common/OptimizedImage.svelte';
	import PlatformLogo from '$lib/components/live/PlatformLogo.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { getPlatformIcon } from '$lib/constants/live';
	import { Search, Play, RotateCcw, User, List, ExternalLink, Database } from 'lucide-svelte';
	import type { ReplaySource } from '$lib/stores/replay.svelte';

	const { t } = useTranslation();

	interface Props {
		basePath?: string;
	}

	let { basePath = '/jkt48/live/replay' }: Props = $props();

	let search = $state('');
	let platformFilter = $state('all');
	let sourceFilter = $state<ReplaySource>(replayStore.currentSource);
	let memberFilter = $state<string | null>(null);
	let page = $state(1);
	const perPage = 12;
	let isFilterOpen = $state(false);
	let isSourceFilterOpen = $state(false);
	let isSearchOpen = $state(false);
	let searchInput: HTMLInputElement | undefined = $state();
	let memberMap = $derived.by(() => {
		const map = new Map<string, { img_small?: string; blurHash?: string }>();
		for (const m of membersStore.list) {
			const key = m.nickname?.toLowerCase();
			if (key) {
				map.set(key, { img_small: m.img_small, blurHash: m.blurHash });
			}
		}
		return map;
	});
	let memberList = $derived.by(() => {
		const list: { nickname: string; img_small?: string; blurHash?: string }[] = [];
		for (const m of membersStore.list) {
			const key = m.nickname?.toLowerCase();
			if (key) {
				list.push({ nickname: key, img_small: m.img_small, blurHash: m.blurHash });
			}
		}
		return list;
	});
	let avatarScrollRef: HTMLDivElement | undefined = $state();
	let atEnd = $state(true);
	let containerRef: HTMLDivElement | undefined = $state();

	$effect(() => {
		if (avatarScrollRef) {
			atEnd =
				avatarScrollRef.scrollLeft + avatarScrollRef.clientWidth >= avatarScrollRef.scrollWidth - 4;
		}
	});

	function onAvatarScroll() {
		if (!avatarScrollRef) return;
		atEnd =
			avatarScrollRef.scrollLeft + avatarScrollRef.clientWidth >= avatarScrollRef.scrollWidth - 4;
	}

	onMount(() => {
		replayStore.loadVideos(sourceFilter);
		membersStore.load({ limit: 100 }, true);
	});

	$effect(() => {
		liveNavbarStore.rightSnippet = rightActions;
		return () => {
			if (liveNavbarStore.rightSnippet === rightActions) {
				liveNavbarStore.rightSnippet = undefined;
			}
		};
	});

	function clickOutside(node: HTMLElement, param: { close: () => void; exclude?: string }) {
		const handle = (event: MouseEvent) => {
			const target = event.target as Element;
			if (node && !node.contains(target) && (!param.exclude || !target.closest(param.exclude))) {
				param.close();
			}
		};
		document.addEventListener('click', handle, true);
		return {
			destroy() {
				document.removeEventListener('click', handle, true);
			}
		};
	}

	let filteredVideos = $derived.by(() => {
		let result = replayStore.videos;
		if (memberFilter) {
			result = result.filter((v) => v.member.toLowerCase() === memberFilter);
		}
		if (search) {
			const lower = search.toLowerCase();
			result = result.filter(
				(v) => v.title.toLowerCase().includes(lower) || v.member.toLowerCase().includes(lower)
			);
		}
		if (platformFilter !== 'all') {
			result = result.filter((v) => v.platform.toLowerCase() === platformFilter.toLowerCase());
		}
		return result;
	});

	let totalCount = $derived(filteredVideos.length);
	let totalPages = $derived(Math.ceil(totalCount / perPage));
	let paginatedVideos = $derived(filteredVideos.slice((page - 1) * perPage, page * perPage));

	let startIndex = $derived(totalCount === 0 ? 0 : (page - 1) * perPage + 1);
	let endIndex = $derived(totalCount === 0 ? 0 : Math.min(page * perPage, totalCount));

	function getYouTubeThumbnail(youtubeId: string | undefined): string {
		if (!youtubeId) return '';
		return `https://img.youtube.com/vi/${youtubeId}/mqdefault.jpg`;
	}

	function handleVideoClick(youtubeId: string) {
		goto(`${basePath}/${youtubeId}`);
	}

	function handleSearch(e: Event) {
		const target = e.target as HTMLInputElement;
		search = target.value;
		page = 1;
	}

	$effect(() => {
		if (isSearchOpen) {
			requestAnimationFrame(() => searchInput?.focus());
		}
	});

	function setPlatform(filter: string) {
		platformFilter = filter;
		isFilterOpen = false;
		page = 1;
	}

	function setSource(source: ReplaySource) {
		sourceFilter = source;
		isSourceFilterOpen = false;
		page = 1;
		replayStore.loadVideos(source);
	}

	function goToPage(p: number) {
		page = p;
		containerRef?.scrollTo({ top: 0, behavior: 'smooth' });
	}

	function setMemberFilter(nickname: string | null) {
		memberFilter = memberFilter === nickname ? null : nickname;
		page = 1;
	}

	let pageNumbers = $derived.by(() => {
		const pages: (number | string)[] = [];
		if (totalPages <= 7) {
			for (let i = 1; i <= totalPages; i++) pages.push(i);
		} else {
			pages.push(1);
			if (page > 3) pages.push('...');
			for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i++) {
				pages.push(i);
			}
			if (page < totalPages - 2) pages.push('...');
			pages.push(totalPages);
		}
		return pages;
	});

	const platformOptions = [
		{ label: t('replay.list.all'), value: 'all', icon: null },
		{ label: t('replay.list.idn'), value: 'idn', icon: 'idn' },
		{ label: t('replay.list.showroom'), value: 'showroom', icon: 'showroom' }
	];

	const sourceOptions: { label: string; value: ReplaySource }[] = [
		{ label: 'MyPage48', value: 'mypage48' },
		{ label: 'JeketiBots', value: 'jeketibots' }
	];

	let selectedOption = $derived(
		platformOptions.find((o) => o.value === platformFilter) || platformOptions[0]
	);
</script>

{#snippet rightActions()}
	<div class="flex items-center gap-2">
		<span
			class="text-xs text-slate-500 dark:text-slate-400 font-medium whitespace-nowrap tabular-nums"
		>
			{startIndex}-{endIndex}/{totalCount}
		</span>
		<div class="relative">
			<button
				data-replay-search="true"
				onclick={() => (isSearchOpen = !isSearchOpen)}
				class="flex items-center justify-center rounded-full transition-all cursor-pointer border h-8 sm:h-9 w-8 sm:w-9 shadow-sm {isSearchOpen
					? 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border-red-100 dark:border-red-800'
					: 'bg-white dark:bg-zinc-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-zinc-700 hover:border-red-200 dark:hover:border-red-500/50 hover:text-red-600 dark:hover:text-red-400'}"
			>
				<Search size={15} />
			</button>

			{#if isSearchOpen}
				<div
					use:clickOutside={{
						close: () => (isSearchOpen = false),
						exclude: '[data-replay-search]'
					}}
					transition:slide={{ duration: 150 }}
					class="absolute top-full right-0 mt-2 z-[7000] w-64 bg-white dark:bg-zinc-900 rounded-2xl border border-slate-200 dark:border-zinc-700 shadow-xl overflow-hidden p-3"
				>
					<input
						bind:this={searchInput}
						type="text"
						placeholder={t('replay.list.searchPlaceholder')}
						value={search}
						oninput={handleSearch}
						class="w-full px-3 py-2 bg-slate-50 dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700 rounded-xl text-sm text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-zinc-500 outline-none focus:border-red-500/50 focus:ring-2 focus:ring-red-500/10 transition-all"
					/>
				</div>
			{/if}
		</div>

		<div class="relative">
			<button
				data-replay-source="true"
				onclick={() => (isSourceFilterOpen = !isSourceFilterOpen)}
				class="flex items-center justify-center rounded-full transition-all cursor-pointer border h-8 sm:h-9 w-8 sm:w-9 shadow-sm {isSourceFilterOpen
					? 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border-red-100 dark:border-red-800'
					: 'bg-white dark:bg-zinc-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-zinc-700 hover:border-red-200 dark:hover:border-red-500/50 hover:text-red-600 dark:hover:text-red-400'}"
				title="Source"
			>
				<Database size={15} />
			</button>

			{#if isSourceFilterOpen}
				<div
					use:clickOutside={{
						close: () => (isSourceFilterOpen = false),
						exclude: '[data-replay-source]'
					}}
					transition:slide={{ duration: 150 }}
					class="absolute top-full right-0 mt-2 z-[7000] min-w-[150px] bg-white dark:bg-zinc-900 rounded-2xl border border-slate-200 dark:border-zinc-700 shadow-xl overflow-hidden"
				>
					{#each sourceOptions as opt}
						<button
							class="w-full flex items-center gap-3 px-4 py-2.5 text-sm font-bold transition-colors text-left cursor-pointer {sourceFilter ===
							opt.value
								? 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400'
								: 'text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-zinc-800'}"
							onclick={() => setSource(opt.value)}
						>
							{opt.label}
						</button>
					{/each}
				</div>
			{/if}
		</div>

		<div class="relative">
			<button
				data-replay-filter="true"
				onclick={() => (isFilterOpen = !isFilterOpen)}
				class="flex items-center justify-center rounded-full transition-all cursor-pointer border h-8 sm:h-9 w-8 sm:w-9 shadow-sm {isFilterOpen
					? 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border-red-100 dark:border-red-800'
					: 'bg-white dark:bg-zinc-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-zinc-700 hover:border-red-200 dark:hover:border-red-500/50 hover:text-red-600 dark:hover:text-red-400'}"
			>
				{#if selectedOption.icon}
					<span
						class="text-[10px] sm:text-xs font-black uppercase text-slate-700 dark:text-slate-300"
						>{getPlatformIcon(selectedOption.icon).charAt(0)}</span
					>
				{:else}
					<List size={15} />
				{/if}
			</button>

			{#if isFilterOpen}
				<div
					use:clickOutside={{
						close: () => (isFilterOpen = false),
						exclude: '[data-replay-filter]'
					}}
					transition:slide={{ duration: 150 }}
					class="absolute top-full right-0 mt-2 z-[7000] min-w-[180px] bg-white dark:bg-zinc-900 rounded-2xl border border-slate-200 dark:border-zinc-700 shadow-xl overflow-hidden"
				>
					{#each platformOptions as opt}
						<button
							class="w-full flex items-center gap-3 px-4 py-2.5 text-sm font-bold transition-colors text-left cursor-pointer {platformFilter ===
							opt.value
								? 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400'
								: 'text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-zinc-800'}"
							onclick={() => setPlatform(opt.value)}
						>
							{#if opt.icon}
								<PlatformLogo platform={opt.icon} size="xs" />
							{:else}
								{opt.label}
							{/if}
						</button>
					{/each}
				</div>
			{/if}
		</div>
	</div>
{/snippet}

<div bind:this={containerRef} class="h-full w-full overflow-y-auto pt-4 px-4 sm:px-6 lg:px-8 pb-28">
	<div class="max-w-7xl mx-auto w-full">
		<div class="flex flex-col gap-2">
			{#if !(replayStore.error && replayStore.videos.length === 0)}
				{#if memberList.length === 0}
					<div class="flex gap-3 py-2 px-1">
						{#each Array(5) as _}
							<div class="shrink-0 flex flex-col items-center gap-1">
								<div
									class="w-10 h-10 sm:w-11 sm:h-11 rounded-full bg-slate-200 dark:bg-zinc-800 animate-pulse"
								></div>
								<div class="w-8 h-2 rounded bg-slate-200 dark:bg-zinc-800 animate-pulse"></div>
							</div>
						{/each}
					</div>
				{:else}
					<div class="flex gap-3 py-2 px-1">
						<div class="shrink-0">
							<button
								onclick={() => setMemberFilter(null)}
								class="flex flex-col items-center gap-1 cursor-pointer"
								title={t('replay.list.allMembers')}
							>
								<div
									class="w-10 h-10 sm:w-11 sm:h-11 rounded-full flex items-center justify-center text-xs font-bold transition-all {!memberFilter
										? 'ring-2 ring-red-500 ring-offset-2 ring-offset-white dark:ring-offset-zinc-900 bg-red-500 text-white'
										: 'bg-slate-200 dark:bg-zinc-700 text-slate-500 dark:text-slate-400 hover:bg-slate-300 dark:hover:bg-zinc-600'}"
								>
									<List size={16} />
								</div>
								<span
									class="text-[10px] text-slate-500 dark:text-slate-400 truncate max-w-12 text-center font-medium"
								>
									{t('replay.list.all')}
								</span>
							</button>
						</div>
						<div
							bind:this={avatarScrollRef}
							onscroll={onAvatarScroll}
							class="flex gap-3 overflow-x-auto overflow-y-clip hide-scrollbar flex-1 py-1 pl-1"
							style="scrollbar-width: none; -ms-overflow-style: none; -webkit-mask-image: {!atEnd
								? 'linear-gradient(to right, black calc(100% - 40px), transparent 100%)'
								: 'none'}; mask-image: {!atEnd
								? 'linear-gradient(to right, black calc(100% - 40px), transparent 100%)'
								: 'none'};"
						>
							{#each memberList as m}
								<button
									onclick={() => setMemberFilter(m.nickname)}
									class="shrink-0 flex flex-col items-center gap-1 cursor-pointer"
									title={m.nickname}
								>
									<div
										class="w-10 h-10 sm:w-11 sm:h-11 rounded-full overflow-hidden transition-all {memberFilter ===
										m.nickname
											? 'ring-2 ring-red-500 ring-offset-2 ring-offset-white dark:ring-offset-zinc-900'
											: 'ring-1 ring-slate-300 dark:ring-zinc-600 hover:ring-slate-400 dark:hover:ring-zinc-500'}"
									>
										<OptimizedImage
											src={m.img_small}
											srcSmall={m.img_small}
											blurHash={m.blurHash}
											alt={m.nickname}
											class="w-full h-full object-cover"
											noBackground={true}
										/>
									</div>
									<span
										class="text-[10px] text-slate-500 dark:text-slate-400 truncate max-w-12 text-center font-medium"
									>
										{m.nickname}
									</span>
								</button>
							{/each}
						</div>
					</div>
				{/if}
			{/if}
			{#if replayStore.loading && replayStore.videos.length === 0}
				<div class="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-4 gap-4">
					{#each Array(8) as _}
						<div class="animate-pulse">
							<div class="aspect-video bg-slate-200 dark:bg-zinc-800 rounded-xl"></div>
							<div class="mt-3 space-y-2 px-1">
								<div class="h-4 w-3/4 bg-slate-200 dark:bg-zinc-800 rounded"></div>
								<div class="h-3 w-1/2 bg-slate-200 dark:bg-zinc-800 rounded"></div>
							</div>
						</div>
					{/each}
				</div>
			{:else if replayStore.error && replayStore.videos.length === 0}
				<div class="flex flex-col items-center justify-center py-24 text-center px-6" in:fade>
					<div
						class="w-24 h-24 rounded-full bg-slate-100 dark:bg-zinc-900 flex items-center justify-center mb-6 text-slate-300 dark:text-zinc-800"
					>
						<RotateCcw size={40} />
					</div>
					<h2 class="text-2xl font-black text-slate-900 dark:text-white mb-2">
						{t('replay.list.loadError')}
					</h2>
					<p class="text-slate-500 dark:text-slate-400 font-medium max-w-md text-sm">
						{replayStore.error}
					</p>
					<button
						class="mt-6 px-6 py-3 bg-red-600 text-white rounded-xl text-xs font-black uppercase tracking-widest hover:bg-red-500 transition-all"
						onclick={() => replayStore.loadVideos()}
					>
						{t('replay.list.retry')}
					</button>
				</div>
			{:else if paginatedVideos.length === 0}
				<div class="flex flex-col items-center justify-center py-24 text-center px-6" in:fade>
					<div
						class="w-24 h-24 rounded-full bg-slate-100 dark:bg-zinc-900 flex items-center justify-center mb-6 text-slate-300 dark:text-zinc-800"
					>
						<RotateCcw size={40} />
					</div>
					<h2 class="text-2xl font-black text-slate-900 dark:text-white mb-2">
						{t('replay.list.empty')}
					</h2>
					<p class="text-slate-500 dark:text-slate-400 font-medium max-w-md text-sm">
						{search || platformFilter !== 'all'
							? t('replay.list.noSearchResults')
							: t('replay.list.noVideos')}
					</p>
				</div>
			{:else}
				<div class="grid grid-cols-1 sm:grid-cols-3 lg:grid-cols-4 gap-3 sm:gap-4">
					{#each paginatedVideos as video (video.youtube_id || video.live_id || video.title)}
						{@const memberData = memberMap.get(video.member.toLowerCase())}
						<button
							class="group text-left w-full focus:outline-none cursor-pointer"
							onclick={() => {
								if (video.youtube_id) handleVideoClick(video.youtube_id);
							}}
						>
							<div
								class="relative aspect-video rounded-xl overflow-hidden bg-slate-100 dark:bg-zinc-800"
							>
								<img
									src={getYouTubeThumbnail(video.youtube_id)}
									alt={video.title}
									loading="lazy"
									class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
								/>
								<div
									class="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-all duration-300 flex flex-col items-center justify-center gap-2"
								>
									<div
										class="w-12 h-12 rounded-full bg-white/90 shadow-lg flex items-center justify-center opacity-0 group-hover:opacity-100 scale-50 group-hover:scale-100 transition-all duration-300"
									>
										<Play size={20} class="text-red-600 ml-0.5" fill="currentColor" />
									</div>
									<a
										href={'https://www.youtube.com/watch?v=' + video.youtube_id}
										target="_blank"
										rel="noopener noreferrer"
										class="relative inline-flex items-center justify-center text-[10px] text-white/80 hover:text-white underline underline-offset-2 opacity-0 group-hover:opacity-100 pointer-events-none group-hover:pointer-events-auto transition-all duration-300 group/link"
										onclick={(e) => e.stopPropagation()}
									>
										<span
											>{replayStore.currentSource === 'mypage48' ? 'MyPage48' : 'JeketiBots'}</span
										>
										<span
											class="absolute -right-4 opacity-0 group-hover/link:opacity-100 transition-opacity"
										>
											<ExternalLink size={10} />
										</span>
									</a>
								</div>
								<div class="absolute top-2 right-2">
									<PlatformLogo
										platform={video.platform === 'SHOWROOM' ? 'showroom' : 'idn'}
										size="xs"
									/>
								</div>
							</div>
							<div class="flex gap-2.5 mt-2.5 px-1">
								<div class="shrink-0">
									{#if membersStore.isLoading}
										<div
											class="w-9 h-9 rounded-full bg-slate-200 dark:bg-zinc-800 animate-pulse"
										></div>
									{:else if memberData}
										<OptimizedImage
											src={memberData.img_small}
											srcSmall={memberData.img_small}
											blurHash={memberData.blurHash}
											alt={video.member}
											class="w-9 h-9 rounded-full object-cover"
											noBackground={true}
										/>
									{:else}
										<div
											class="w-9 h-9 rounded-full bg-slate-200 dark:bg-zinc-700 flex items-center justify-center"
										>
											<User size={16} class="text-slate-400 dark:text-zinc-500" />
										</div>
									{/if}
								</div>
								<div class="min-w-0 flex-1">
									<h3
										class="text-sm font-bold text-slate-900 dark:text-white truncate leading-snug"
									>
										{video.member}
									</h3>
									<p
										class="text-xs text-slate-500 dark:text-slate-400 truncate mt-0.5 leading-relaxed"
									>
										{video.title}
									</p>
									<div class="text-[11px] text-slate-400 dark:text-zinc-500 font-medium mt-0.5">
										{video.date}
									</div>
								</div>
							</div>
						</button>
					{/each}
				</div>

				{#if totalPages > 1}
					<div class="flex items-center justify-center gap-2 mt-8">
						<button
							class="px-3 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer {page ===
							1
								? 'text-slate-400 cursor-not-allowed'
								: 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-zinc-800'}"
							disabled={page === 1}
							onclick={() => goToPage(page - 1)}
						>
							{t('replay.list.prev')}
						</button>

						{#each pageNumbers as p}
							{#if p === '...'}
								<span class="px-2 text-slate-400">...</span>
							{:else}
								<button
									class="w-9 h-9 rounded-xl text-xs font-bold transition-all cursor-pointer {page ===
									p
										? 'bg-red-600 text-white shadow-md shadow-red-600/20'
										: 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-zinc-800'}"
									onclick={() => goToPage(p as number)}
								>
									{p}
								</button>
							{/if}
						{/each}

						<button
							class="px-3 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer {page ===
							totalPages
								? 'text-slate-400 cursor-not-allowed'
								: 'text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-zinc-800'}"
							disabled={page === totalPages}
							onclick={() => goToPage(page + 1)}
						>
							{t('replay.list.next')}
						</button>
					</div>
				{/if}
			{/if}
			<div class="flex justify-center mt-10 pb-6">
				<a
					href={replayStore.currentSource === 'mypage48'
						? 'https://www.youtube.com/@MyPage48'
						: 'https://www.youtube.com/@JeketiBots'}
					target="_blank"
					rel="noopener noreferrer"
					class="group flex items-center gap-1 text-[11px] text-slate-400 dark:text-zinc-600 hover:text-slate-600 dark:hover:text-zinc-400 transition-colors font-medium"
				>
					<span>
						{t('replay.list.originalSource')}
						{replayStore.currentSource === 'mypage48' ? 'MyPage48' : 'JeketiBots'}
					</span>
					<ExternalLink
						size={12}
						class="opacity-0 -translate-x-2 transition-all duration-300 group-hover:opacity-100 group-hover:translate-x-0"
					/>
				</a>
			</div>
		</div>
	</div>
</div>

<style>
	:global(.hide-scrollbar)::-webkit-scrollbar {
		display: none;
	}
</style>
