<script lang="ts">
	import { onMount, untrack } from 'svelte';
	import { pcCollectionStore } from '$lib/stores/pcCollection.svelte';
	import { liveHistoryFilterStore } from '$lib/stores/liveHistoryFilter.svelte';
	import { EmptyState } from '$lib/components';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { Image, ArrowUpDown } from 'lucide-svelte';
	import { isImmersive } from '$lib/stores';
	import AppBackground from '$lib/components/common/AppBackground.svelte';
	import { spring } from 'svelte/motion';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';

	import PhotoCard from '$lib/components/live/PhotoCard.svelte';
	import HistoryTopBar from '$lib/components/live/history/shared/HistoryTopBar.svelte';

	interface Props {
		isPublic?: boolean;
		basePath?: string;
	}

	let { isPublic = false, basePath = '/theater/live/pc' }: Props = $props();

	const { t } = useTranslation();

	let mounted = $state(false);
	let scrollY = $state(0);
	let mouse = $state(spring({ x: 0, y: 0 }, { stiffness: 0.1, damping: 0.25 }));

	let list = $derived(pcCollectionStore.list);
	let pagination = $derived(pcCollectionStore.pagination);
	let isLoading = $derived(pcCollectionStore.isLoading);
	let hasMore = $derived(pagination.page < pagination.total_pages);
	let initialLoading = $state(true);
	let activeTab = $state<'all' | 'owned' | 'unowned'>('all');
	let currentSort = $derived(pcCollectionStore.currentSort);

	onMount(() => {
		mounted = true;
		isImmersive.set(true);
		document.body.style.overflow = 'hidden';
		return () => {
			isImmersive.set(false);
			document.body.style.overflow = '';
		};
	});

	async function loadHistory(page: number, force: boolean = false) {
		await pcCollectionStore.load(activeTab, page, force);
		if (force) initialLoading = false;
	}

	$effect(() => {
		const _trigger =
			liveHistoryFilterStore.filterType +
			liveHistoryFilterStore.customRange.start +
			liveHistoryFilterStore.customRange.end +
			activeTab;
		if (mounted) {
			untrack(() => {
				loadHistory(1, true);
			});
		}
	});

	function handleIntersect() {
		if (!mounted || isLoading || !hasMore) return;
		loadHistory(pagination.page + 1);
	}

	function setTab(tab: 'all' | 'owned' | 'unowned') {
		if (activeTab === tab) return;
		if (isPublic && tab !== 'all') return;
		activeTab = tab;
		// The $effect will trigger reload because activeTab is a dependency
	}
</script>

<SEO title="PC Live - JKT48" path={basePath} description="Photo Card Live Collection" />

<div
	role="presentation"
	class="fixed inset-0 bg-gradient-to-b from-slate-50/50 via-white to-white dark:from-zinc-950 dark:via-zinc-950 dark:to-zinc-900 flex flex-col overflow-hidden z-[9999]"
	onmousemove={(e) => {
		const { clientX, clientY } = e;
		const { innerWidth, innerHeight } = window;
		mouse.set({ x: clientX / innerWidth - 0.5, y: clientY / innerHeight - 0.5 });
	}}
>
	<AppBackground interactive={true} bind:mouse bind:scrollY />

	<HistoryTopBar
		title="PC Live"
		subtitle="Photo Card Live Collection"
		icon={Image}
		iconColor="text-pink-500"
		showDateFilter={true}
	/>

	<!-- Main Content -->
	<div class="flex-1 overflow-y-auto" onscroll={(e) => (scrollY = e.currentTarget.scrollTop)}>
		<div class="max-w-7xl mx-auto px-4 sm:px-6 pt-4 sm:pt-6 pb-32 relative z-10">
			<!-- Tabs & Filter -->
			<div class="flex justify-center mb-6 sm:mb-8 w-full max-w-lg mx-auto">
				<div class="flex w-full items-end border-b border-black/10 dark:border-white/10">
					<!-- Filter Icon with Hidden Select -->
					<div
						class="relative shrink-0 pb-3 px-3 sm:px-4 border-r border-black/10 dark:border-white/10 mr-2 sm:mr-3 flex items-center justify-center"
					>
						<select
							class="absolute inset-0 opacity-0 cursor-pointer w-full h-full z-10"
							value={currentSort}
							onchange={(e) => pcCollectionStore.setSort(e.currentTarget.value)}
							title={t('liveHistory.pcLive.sort.dateDesc') || 'Sort Filter'}
						>
							<option value="date_desc" class="text-black"
								>{t('liveHistory.pcLive.sort.dateDesc') || 'Latest First'}</option
							>
							<option value="date_asc" class="text-black"
								>{t('liveHistory.pcLive.sort.dateAsc') || 'Oldest First'}</option
							>
							<option value="tier_desc" class="text-black"
								>{t('liveHistory.pcLive.sort.tierDesc') || 'Highest Rarity'}</option
							>
							<option value="tier_asc" class="text-black"
								>{t('liveHistory.pcLive.sort.tierAsc') || 'Lowest Rarity'}</option
							>
						</select>
						<ArrowUpDown
							class="w-4 h-4 sm:w-5 sm:h-5 text-zinc-500 dark:text-zinc-400 hover:text-pink-500 transition-colors"
						/>
					</div>

					<button
						class="flex-1 cursor-pointer pb-3 text-xs sm:text-sm font-bold transition-all border-b-2 {activeTab ===
						'all'
							? 'border-pink-500 text-zinc-900 dark:text-white'
							: 'border-transparent text-zinc-500 dark:text-zinc-400 hover:text-zinc-800 dark:hover:text-white'}"
						onclick={() => setTab('all')}
					>
						{t('liveHistory.pcLive.tabs.all') || 'All Cards'}
					</button>
					{#if !isPublic}
						<button
							class="flex-1 cursor-pointer pb-3 text-xs sm:text-sm font-bold transition-all border-b-2 {activeTab ===
							'owned'
								? 'border-pink-500 text-zinc-900 dark:text-white'
								: 'border-transparent text-zinc-500 dark:text-zinc-400 hover:text-zinc-800 dark:hover:text-white'}"
							onclick={() => setTab('owned')}
						>
							{t('liveHistory.pcLive.tabs.owned') || 'Owned'}
						</button>
						<button
							class="flex-1 cursor-pointer pb-3 text-xs sm:text-sm font-bold transition-all border-b-2 {activeTab ===
							'unowned'
								? 'border-pink-500 text-zinc-900 dark:text-white'
								: 'border-transparent text-zinc-500 dark:text-zinc-400 hover:text-zinc-800 dark:hover:text-white'}"
							onclick={() => setTab('unowned')}
						>
							{t('liveHistory.pcLive.tabs.notOwned') || 'Not Owned'}
						</button>
					{/if}
				</div>
			</div>

			{#if initialLoading || (isLoading && list.length === 0)}
				<div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 sm:gap-6">
					{#each Array(10) as _}
						<div class="aspect-[3/4] rounded-2xl bg-zinc-800 animate-pulse"></div>
					{/each}
				</div>
			{:else if list.length === 0}
				<EmptyState
					icon={Image}
					title={t('liveHistory.pcLive.emptyTitle') || 'No Live History'}
					description={t('liveHistory.pcLive.emptyDesc') ||
						'There is no live history data to display as Photo Cards.'}
				/>
			{:else}
				<div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 sm:gap-6">
					{#each list as item (item._id)}
						<div class="transform transition-all duration-300 hover:scale-[1.02]">
							<PhotoCard {item} {isPublic} />
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
								class="w-8 h-8 border-4 border-pink-500/30 border-t-pink-500 rounded-full animate-spin"
							></div>
						{/if}
					</div>
				{/if}
			{/if}
		</div>
	</div>
</div>
