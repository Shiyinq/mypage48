<script lang="ts">
	import { showToast, ticketsStore } from '$lib/stores';
	import { onMount, untrack } from 'svelte';
	import { Image as ImageIcon } from 'lucide-svelte';
	import { Filter as FilterIcon } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { PageHeader, EmptyState, ErrorState, NoMoreData } from '$lib/components';
	import { Lightbox, MemoriesFilterCard, MemoryCard } from '$lib/components/memories';
	import { slide } from 'svelte/transition';
	import { PolaroidSkeleton } from '$lib/components/skeletons';
	import type { MemoryItem, MemoryFilters as MemoryFiltersType } from '$lib/types';
	import { galleryStore, isGalleryLoading } from '$lib/stores/memories.svelte';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';
	import { isCacheExpired } from '$lib/utils/cache';
	import { formatDate } from '$lib/i18n';

	const { t } = useTranslation();

	// Reactive state from store
	let memories = $derived(galleryStore.list);
	let pagination = $derived(galleryStore.pagination);
	let filter = $derived(galleryStore.filter);
	let error = $derived(galleryStore.error);
	let isLoading = $derived(isGalleryLoading.value);

	let selectedImage: MemoryItem | null = $state(null);
	let mounted = $state(false);
	let isFilterOpen = $state(false);
	let localFilters: MemoryFiltersType = $state({
		type: 'ALL',
		isFavorite: undefined,
		startDate: undefined,
		endDate: undefined,
		days: [],
		title: undefined
	});

	$effect(() => {
		// sync from store if it changes externally
		localFilters = { ...galleryStore.filter };
	});

	$effect(() => {
		// When localFilters changes, load it into store
		const _trackType = localFilters.type;
		const trackStart = localFilters.startDate;
		const trackEnd = localFilters.endDate;
		const _trackTitle = localFilters.title;
		const _trackFavorite = localFilters.isFavorite;

		untrack(() => {
			if ((trackStart && !trackEnd) || (!trackStart && trackEnd)) {
				return;
			}

			if (JSON.stringify(localFilters) !== JSON.stringify(galleryStore.filter)) {
				loadMemoriesWithFilter(localFilters);
			}
		});
	});

	function clickOutside(node: HTMLElement) {
		const handleClick = (event: MouseEvent) => {
			const target = event.target as Element;
			if (node && !node.contains(target) && !target.closest('[data-filter-toggle="true"]')) {
				isFilterOpen = false;
			}
		};

		document.addEventListener('click', handleClick, true);

		return {
			destroy() {
				document.removeEventListener('click', handleClick, true);
			}
		};
	}

	function formatFilterDate(dateStr?: string) {
		if (!dateStr) return '';
		return formatDate(dateStr, { day: 'numeric', month: 'short', year: 'numeric' });
	}

	function getFilterTypeLabel(type: string | undefined) {
		if (type === 'TICKET') return t('memories.tickets');
		if (type === '2SHOT') return t('memories.twoShots');
		return t('memories.allPhotos');
	}

	let filterLabel = $derived.by(() => {
		const typeLabel = getFilterTypeLabel(localFilters.type);
		if (localFilters.startDate && localFilters.endDate) {
			return `${typeLabel} (${formatFilterDate(localFilters.startDate)} - ${formatFilterDate(localFilters.endDate)})`;
		}
		return typeLabel;
	});

	onMount(() => {
		mounted = true;
		// Initial load only if empty or expired
		const currentCache = galleryStore.cache[JSON.stringify(filter)];

		if (memories.length === 0 || isCacheExpired(currentCache?.lastUpdated)) {
			loadMemories(1);
		}
	});

	async function loadMemories(pageIdx: number) {
		if (isLoading) return;

		// If not page 1 and no more, don't load
		if (pageIdx > 1 && !pagination.hasMore) return;

		try {
			// Use store action
			await galleryStore.load(pageIdx, filter);
		} catch {
			showToast(t('memories.errorTitle') || 'Failed to load memories', 'error');
		}
	}

	async function loadMemoriesWithFilter(newFilter: MemoryFiltersType) {
		// We call load with page 1 and new filter
		try {
			await galleryStore.load(1, newFilter);
		} catch {
			// Error handled in store/toast above or by subscription
		}
	}

	// Infinite scroll handler
	function handleIntersect() {
		if (!mounted || isLoading || !pagination.hasMore) return;
		loadMemories(pagination.page + 1);
	}

	// Scroll lock for lightbox
	$effect(() => {
		if (typeof document !== 'undefined') {
			document.body.style.overflow = selectedImage ? 'hidden' : 'unset';
		}
	});

	async function handleToggleFavorite(item: MemoryItem) {
		galleryStore.toggleFavorite(item.uniqueId);
		try {
			if (item.type === '2SHOT') {
				await ticketsStore.toggleTwoShotFavorite(item.ticketRef!);
			} else {
				await ticketsStore.toggleFavorite(item.ticketRef!);
			}
		} catch {
			galleryStore.toggleFavorite(item.uniqueId);
			showToast(t('common.error'), 'error');
		}
	}
</script>

<SEO title={t('memories.title')} path="/memories" description={t('seo.memories')} />

<!-- Lightbox -->
<Lightbox
	{selectedImage}
	onClose={() => (selectedImage = null)}
	onfavoriteToggle={handleToggleFavorite}
/>

<div class="max-w-[1600px] mx-auto px-4 sm:px-6 pt-4 sm:pt-6 pb-32">
	<!-- Header -->
	<div class="mb-0 sm:mb-8 relative z-30">
		<PageHeader
			icon={ImageIcon}
			title={t('memories.title')}
			subtitle={t('memories.subtitle')}
			theme="pink"
			actionItems={[
				{
					label: filterLabel,
					onClick: () => (isFilterOpen = !isFilterOpen),
					theme: isFilterOpen ? 'pink' : 'gray',
					filterToggle: true
				},
				{
					icon: FilterIcon,
					label: t('common.filters') || 'Filter',
					onClick: () => (isFilterOpen = !isFilterOpen),
					theme: isFilterOpen ? 'pink' : 'gray',
					filterToggle: true
				}
			]}
		/>

		{#if isFilterOpen}
			<div
				use:clickOutside
				transition:slide={{ duration: 200 }}
				class="fixed md:absolute top-[64px] md:top-full left-0 right-0 md:left-auto md:right-0 mt-2 md:mt-2 px-4 md:px-0 z-[7000]"
			>
				<MemoriesFilterCard
					bind:filters={localFilters}
					onClear={() => {
						isFilterOpen = false;
					}}
				/>
			</div>
		{/if}
	</div>

	<!-- Gallery Grid -->
	{#if error && memories.length === 0}
		<ErrorState
			title={t('memories.errorTitle') || 'Failed to load memories'}
			description={t('memories.errorDesc') || error || ''}
			onRetry={() => loadMemories(1)}
		/>
	{:else if isLoading && memories.length === 0}
		<div
			class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 md:gap-8 px-2 sm:px-4"
		>
			<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
			{#each Array(8) as _unused, index}
				{@const rotation = (index % 5) - 2}
				<div class="relative" style={`transform: rotate(${rotation}deg)`}>
					<PolaroidSkeleton />
				</div>
			{/each}
		</div>
	{:else if memories.length === 0}
		<EmptyState
			icon={ImageIcon}
			title={t('memories.noMemories')}
			description={t('upload.subtitle')}
		/>
	{:else}
		<div
			class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 md:gap-8 px-2 sm:px-4"
		>
			{#each memories as item, index (item.uniqueId)}
				{@const rotation = (index % 5) - 2}
				<MemoryCard
					{item}
					{rotation}
					onClick={(i) => (selectedImage = i)}
					onfavoriteToggle={handleToggleFavorite}
				/>
			{/each}
		</div>

		<!-- Sentinel for infinite scroll -->
		{#if pagination.hasMore}
			<div use:infiniteScroll onintersect={handleIntersect} class="w-full py-8 flex justify-center">
				{#if isLoading}
					<div
						class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 md:gap-8 px-2 sm:px-4 w-full"
					>
						<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
						{#each Array(4) as _, index}
							{@const rotation = (index % 5) - 2}
							<div class="relative" style={`transform: rotate(${rotation}deg)`}>
								<PolaroidSkeleton />
							</div>
						{/each}
					</div>
				{/if}
			</div>
		{:else if memories.length > 0}
			<NoMoreData theme="pink" />
		{/if}
	{/if}
</div>
