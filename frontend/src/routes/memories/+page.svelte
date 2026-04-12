<script lang="ts">
	import { isAuthenticated, showToast } from '$lib/stores';
	import { onMount } from 'svelte';
	import { Image as ImageIcon } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { PageHeader, EmptyState, ErrorState } from '$lib/components';
	import { Lightbox, MemoryFilters, MemoryCard, type FilterType } from '$lib/components/memories';
	import { PolaroidSkeleton } from '$lib/components/skeletons';
	import type { MemoryItem } from '$lib/types';
	import { galleryStore, isGalleryLoading } from '$lib/stores/memories';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';
	import { isCacheExpired } from '$lib/utils/cache';

	const { t } = useTranslation();

	// Store data via derived runes
	let galleryState = $derived($galleryStore);
	let memories = $derived(galleryState.list);
	let pagination = $derived(galleryState.pagination);
	let filter = $derived(galleryState.filter);
	let error = $derived(galleryState.error);

	let selectedImage: MemoryItem | null = $state(null);
	let mounted = $state(false);

	onMount(() => {
		mounted = true;
		// Initial load only if empty or expired
		const currentCache = galleryState.cache[filter];

		if (memories.length === 0 || isCacheExpired(currentCache.lastUpdated)) {
			loadMemories(1);
		}
	});

	async function loadMemories(page: number) {
		if ($isGalleryLoading) return;

		// If not page 1 and no more, don't load
		if (page > 1 && !pagination.hasMore) return;

		try {
			// Use store action
			await galleryStore.load(page, filter);
		} catch {
			showToast($t('memories.errorTitle') || 'Failed to load memories', 'error');
		}
	}

	function handleFilterChange(newFilter: FilterType) {
		if (filter === newFilter) return;

		// Reset load
		loadMemoriesWithFilter(newFilter);
	}

	async function loadMemoriesWithFilter(newFilter: FilterType) {
		// We call load with page 1 and new filter
		// Store handles cache check
		try {
			await galleryStore.load(1, newFilter);
		} catch {
			// Error handled in store/toast above or by subscription
		}
	}

	// Infinite scroll handler
	function handleIntersect() {
		if (!mounted || $isGalleryLoading || !pagination.hasMore) return;
		loadMemories(pagination.page + 1);
	}

	// Scroll lock for lightbox
	$effect(() => {
		if (typeof document !== 'undefined') {
			document.body.style.overflow = selectedImage ? 'hidden' : 'unset';
		}
	});
</script>

<SEO title={$t('memories.title')} path="/memories" description={$t('seo.memories')} />

<!-- Lightbox -->
<Lightbox {selectedImage} onClose={() => (selectedImage = null)} />

<div class="max-w-7xl mx-auto px-4 sm:px-6 pt-4 sm:pt-6 pb-32 animate-fade-in">
	<!-- Header -->
	<div class="mb-8">
		<PageHeader
			icon={ImageIcon}
			title={$t('memories.title')}
			subtitle={$t('memories.subtitle')}
			theme="pink"
		>
			{#snippet actions()}
				<div>
					<MemoryFilters
						filter={galleryState.filter}
						onchange={(newFilter) => handleFilterChange(newFilter)}
					/>
				</div>
			{/snippet}
		</PageHeader>
	</div>

	<!-- Gallery Grid -->
	{#if error && memories.length === 0}
		<ErrorState
			title={$t('memories.errorTitle') || 'Failed to load memories'}
			description={$t('memories.errorDesc') || error || ''}
			onRetry={() => loadMemories(1)}
		/>
	{:else if $isGalleryLoading && memories.length === 0}
		<div
			class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-10 px-2 sm:px-4"
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
			title={$t('memories.noMemories')}
			description={$t('upload.subtitle')}
		/>
	{:else}
		<div
			class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-10 px-2 sm:px-4"
		>
			{#each memories as item, index (item.uniqueId)}
				{@const rotation = (index % 5) - 2}
				<MemoryCard {item} {rotation} onClick={(i) => (selectedImage = i)} />
			{/each}
		</div>

		<!-- Sentinel for infinite scroll -->
		{#if pagination.hasMore}
			<div use:infiniteScroll onintersect={handleIntersect} class="w-full py-8 flex justify-center">
				{#if $isGalleryLoading}
					<div
						class="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-10 px-2 sm:px-4 w-full"
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
		{/if}
	{/if}
</div>
