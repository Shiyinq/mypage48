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
	import { galleryStore } from '$lib/stores/memories';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';

	const { t } = useTranslation();

	// State
	$: state = $galleryStore;
	$: memories = state.list;
	$: pagination = state.pagination;
	$: filter = state.filter;

	let selectedImage: MemoryItem | null = null;
	let isLoadingMore = false;
	let mounted = false;
	let error = false;

	onMount(() => {
		mounted = true;
		// Initial load only if empty
		if (memories.length === 0) {
			loadMemories(1);
		}
	});

	async function loadMemories(page: number) {
		if (isLoadingMore) return;

		// If not page 1 and no more, don't load
		if (page > 1 && !pagination.hasMore) return;

		isLoadingMore = true;

		try {
			error = false;
			// Use store action
			await galleryStore.load(page, filter);
		} catch (e) {
			console.error('Failed to load memories:', e);
			error = true;
			showToast($t('memories.errorTitle') || 'Failed to load memories', 'error');
		} finally {
			isLoadingMore = false;
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
			isLoadingMore = true;
			await galleryStore.load(1, newFilter);
		} catch (e) {
			error = true;
		} finally {
			isLoadingMore = false;
		}
	}

	// Infinite scroll handler
	function handleIntersect() {
		if (!mounted || isLoadingMore || !pagination.hasMore) return;
		loadMemories(pagination.page + 1);
	}

	// Scroll lock for lightbox
	$: if (typeof document !== 'undefined') {
		document.body.style.overflow = selectedImage ? 'hidden' : 'unset';
	}

	$: isLoading = !mounted || ($isAuthenticated && memories.length === 0 && isLoadingMore);
</script>

<SEO title={$t('memories.title')} path="/memories" description={$t('seo.memories')} />

<!-- Lightbox -->
<Lightbox {selectedImage} onClose={() => (selectedImage = null)} />

<div class="max-w-7xl mx-auto p-4 pb-32 animate-fade-in">
	<!-- Header -->
	<div class="mb-8">
		<PageHeader
			icon={ImageIcon}
			title={$t('memories.title')}
			subtitle={$t('memories.subtitle')}
			theme="pink"
		>
			<div slot="actions">
				<MemoryFilters filter={state.filter} on:change={(e) => handleFilterChange(e.detail)} />
			</div>
		</PageHeader>
	</div>

	<!-- Gallery Grid -->
	{#if error && memories.length === 0}
		<ErrorState
			title={$t('memories.errorTitle') || 'Failed to load memories'}
			description={$t('memories.errorDesc') || 'Something went wrong while fetching your memories.'}
			onRetry={() => loadMemories(1)}
		/>
	{:else if isLoading}
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8 md:gap-10 px-4">
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
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8 md:gap-10 px-4">
			{#each memories as item, index (item.uniqueId)}
				{@const rotation = (index % 5) - 2}
				<MemoryCard {item} {rotation} onClick={(i) => (selectedImage = i)} />
			{/each}
		</div>

		<!-- Sentinel for infinite scroll -->
		{#if pagination.hasMore}
			<div
				use:infiniteScroll
				on:intersect={handleIntersect}
				class="w-full py-8 flex justify-center"
			>
				{#if isLoadingMore}
					<div
						class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8 md:gap-10 px-4 w-full"
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
