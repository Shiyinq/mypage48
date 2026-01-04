<script lang="ts">
	import { isAuthenticated, showToast } from '$lib/stores';
	import { onMount } from 'svelte';
	import { Image as ImageIcon } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { PageHeader, EmptyState, ErrorState } from '$lib/components';
	import { Lightbox, MemoryFilters, MemoryCard, type FilterType } from '$lib/components/memories';
	import type { MemoryItem, PaginationState } from '$lib/types';
	import { memoriesApi } from '$lib/apis/memories';

	const { t } = useTranslation();

	// State
	let memories: MemoryItem[] = [];
	let pagination: PaginationState = { page: 0, hasMore: true };
	let filter: FilterType = 'ALL';
	let selectedImage: MemoryItem | null = null;
	let isLoadingMore = false;
	let mounted = false;
	let error = false;

	// Cached data for each filter to avoid refetching
	let cachedData: Record<
		FilterType,
		{ memories: MemoryItem[]; pagination: PaginationState } | null
	> = {
		ALL: null,
		TICKET: null,
		'2SHOT': null
	};

	onMount(() => {
		mounted = true;
		loadMemories(1);
	});

	async function loadMemories(page: number) {
		if (isLoadingMore) return;
		isLoadingMore = true;

		try {
			error = false;
			const res = await memoriesApi.getMemories(page, 20, filter);

			if (page === 1) {
				memories = res.data;
			} else {
				memories = [...memories, ...res.data];
			}

			pagination = {
				page,
				hasMore: res.meta.current_page < res.meta.last_page
			};

			// Cache the current state
			cachedData[filter] = { memories, pagination };
		} catch (e) {
			console.error('Failed to load memories:', e);
			error = true;
			showToast($t('memories.errorTitle') || 'Failed to load memories', 'error');
		} finally {
			isLoadingMore = false;
		}
	}

	let previousFilter: FilterType = 'ALL';

	function handleFilterChange(newFilter: FilterType) {
		if (previousFilter === newFilter) return;
		previousFilter = newFilter;

		// Check cache first
		const cached = cachedData[newFilter];
		if (cached) {
			memories = cached.memories;
			pagination = cached.pagination;
		} else {
			// Reset and fetch
			memories = [];
			pagination = { page: 0, hasMore: true };
			loadMemories(1);
		}
	}

	function handleScroll() {
		if (!mounted || isLoadingMore || !pagination.hasMore) return;

		const threshold = 300;
		const position = window.innerHeight + window.scrollY;
		const height = document.documentElement.scrollHeight;

		if (position > height - threshold) {
			loadMemories(pagination.page + 1);
		}
	}

	// Scroll lock for lightbox
	$: if (typeof document !== 'undefined') {
		document.body.style.overflow = selectedImage ? 'hidden' : 'unset';
	}

	$: isLoading = !mounted || ($isAuthenticated && memories.length === 0 && isLoadingMore);
</script>

<SEO title={$t('memories.title')} path="/memories" description={$t('seo.memories')} />
<svelte:window on:scroll={handleScroll} />

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
				<MemoryFilters bind:filter on:change={(e) => handleFilterChange(e.detail)} />
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
					<div
						class="bg-white dark:bg-zinc-900 p-3 pb-12 shadow-md border border-gray-100 dark:border-zinc-700 rounded-sm"
					>
						<div class="aspect-[4/5] w-full bg-gray-200 dark:bg-zinc-800 animate-pulse mb-4"></div>
						<div class="px-2">
							<div
								class="h-4 bg-gray-200 dark:bg-zinc-800 rounded animate-pulse w-3/4 mx-auto mb-2"
							></div>
							<div
								class="h-3 bg-gray-200 dark:bg-zinc-800 rounded animate-pulse w-1/2 mx-auto"
							></div>
						</div>
					</div>
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

		<!-- Loading more skeleton -->
		{#if isLoadingMore && memories.length > 0}
			<div
				class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8 md:gap-10 px-4 mt-8"
			>
				<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
				{#each Array(4) as _, index}
					{@const rotation = (index % 5) - 2}
					<div class="relative" style={`transform: rotate(${rotation}deg)`}>
						<div
							class="bg-white dark:bg-zinc-900 p-3 pb-12 shadow-md border border-gray-100 dark:border-zinc-700 rounded-sm"
						>
							<div
								class="aspect-[4/5] w-full bg-gray-200 dark:bg-zinc-800 animate-pulse mb-4"
							></div>
							<div class="px-2">
								<div
									class="h-4 bg-gray-200 dark:bg-zinc-800 rounded animate-pulse w-3/4 mx-auto mb-2"
								></div>
								<div
									class="h-3 bg-gray-200 dark:bg-zinc-800 rounded animate-pulse w-1/2 mx-auto"
								></div>
							</div>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	{/if}
</div>
