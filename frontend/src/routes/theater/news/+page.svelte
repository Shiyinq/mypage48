<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { Newspaper, Calendar, ChevronLeft, ChevronRight } from 'lucide-svelte';
	import { EmptyState, ErrorState } from '$lib/components';
	import { fade } from 'svelte/transition';
	import { getExternalMediaUrl } from '$lib/utils/media';

	import { EventCardSkeleton } from '$lib/components/skeletons';
	import {
		newsList,
		newsPagination,
		newsLoading,
		newsError,
		newsStore
	} from '$lib/stores/news.svelte';

	import { formatDate } from '$lib/i18n';
	const { t } = useTranslation();

	let mounted = $state(false);

	onMount(async () => {
		await newsStore.load();
		mounted = true;
	});

	let list = $derived(newsList.value);
	let isLoading = $derived(newsLoading.value);
	let error = $derived(newsError.value);

	async function handlePageChange(page: number) {
		newsStore.load(page);
		await tick();
		setTimeout(() => window.scrollTo({ top: 0, behavior: 'smooth' }), 10);
	}

	function generatePagination(current: number, total: number) {
		const delta = 4;
		const range = [];
		const rangeWithDots = [];
		let l;

		range.push(1);
		if (total <= 1) return range;

		for (let i = current - delta; i <= current + delta; i++) {
			if (i < total && i > 1) {
				range.push(i);
			}
		}
		range.push(total);

		for (let i of range) {
			if (l) {
				if (i - l === 2) {
					rangeWithDots.push(l + 1);
				} else if (i - l !== 1) {
					rangeWithDots.push('...');
				}
			}
			rangeWithDots.push(i);
			l = i;
		}

		return rangeWithDots;
	}
</script>

<SEO
	title={$t('theater.news.title') || 'News'}
	path="/theater/news"
	description={$t('theater.news.subtitle') || 'Latest news and updates from JKT48'}
/>

<div class="space-y-6">
	{#if (!mounted || isLoading) && list.length === 0}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
			{#each Array(8)}
				<EventCardSkeleton />
			{/each}
		</div>
	{:else if error && list.length === 0}
		<ErrorState
			title={$t('theater.news.errorTitle')}
			description={$t('theater.news.errorDesc')}
			onRetry={() => newsStore.load(1, 12, true)}
		/>
	{:else if list.length === 0}
		<EmptyState
			icon={Newspaper}
			title={$t('theater.news.emptyTitle')}
			description={$t('theater.news.empty')}
		/>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
			{#each list as item (item.news_id)}
				<a
					href={`/theater/news/${item.link}`}
					class="group flex flex-row md:flex-col bg-white dark:bg-zinc-900 shadow-sm hover:shadow-xl rounded-2xl border border-gray-100 dark:border-white/5 transition-all duration-300 overflow-hidden"
					in:fade={{ duration: 300 }}
				>
					<!-- Image / Placeholder -->
					<div
						class="relative w-[38%] md:w-full shrink-0 overflow-hidden bg-gray-100 dark:bg-zinc-800 aspect-square md:aspect-[4/3]"
					>
						{#if item.background_image}
							<img
								src={getExternalMediaUrl(item.background_image)}
								alt={item.title}
								class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
								loading="lazy"
							/>
						{:else}
							<div
								class="absolute inset-0 bg-gradient-to-br from-red-500/10 to-red-700/10 flex items-center justify-center"
							>
								<Newspaper class="w-10 h-10 md:w-16 md:h-16 text-red-500/30" />
							</div>
						{/if}
						<div
							class="absolute inset-0 bg-gradient-to-t from-black/20 md:from-black/60 via-transparent to-transparent"
						></div>

						<div class="absolute top-2 right-2 md:top-3 md:right-3 z-10">
							<span
								class="inline-flex items-center px-2 py-0.5 md:py-1 rounded-md text-[9px] md:text-[10px] font-bold tracking-wider uppercase shadow-sm {item.category.toLowerCase() ===
								'event'
									? 'bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400'
									: item.category.toLowerCase() === 'theater'
										? 'bg-cyan-100 dark:bg-cyan-500/20 text-cyan-600 dark:text-cyan-400'
										: 'bg-orange-100 dark:bg-orange-500/20 text-orange-600 dark:text-orange-400'}"
							>
								{item.category}
							</span>
						</div>
					</div>

					<!-- Content -->
					<div class="p-3 md:p-4 flex flex-col flex-1 justify-between w-[62%] md:w-full">
						<div>
							<div
								class="flex gap-1.5 items-center mb-1.5 md:mb-2 text-gray-500 dark:text-gray-400 text-[11px] md:text-xs font-semibold"
							>
								<Calendar class="w-3.5 h-3.5" />
								<span
									>{$formatDate(item.valid_date_from, {
										day: 'numeric',
										month: 'short',
										year: 'numeric'
									})}</span
								>
							</div>

							<h3
								class="font-bold text-gray-900 dark:text-white leading-snug mb-2 group-hover:text-red-500 transition-colors text-sm md:text-base line-clamp-3 md:line-clamp-3"
							>
								{item.title}
							</h3>
						</div>

						<div
							class="mt-auto md:pt-4 md:border-t flex items-center justify-between text-[11px] md:text-xs text-gray-500 dark:text-gray-400 font-medium md:border-gray-100 dark:border-white/5"
						>
							<span class="flex items-center gap-1 hover:text-red-500 transition-colors">
								{$t('theater.news.readMore')}
								<ChevronRight class="w-3 h-3" />
							</span>
						</div>
					</div>
				</a>
			{/each}
		</div>

		<!-- Numbered Pagination -->
		{#if $newsPagination && $newsPagination.last_page > 1}
			<div class="flex items-center justify-center mt-8 mb-20 md:mb-8 w-full">
				<div class="flex flex-wrap justify-center gap-1.5 md:gap-2 max-w-full">
					<!-- Previous Button -->
					<button
						class="w-9 h-9 md:w-10 md:h-10 flex items-center justify-center rounded-md bg-white dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-zinc-700 transition-colors"
						disabled={$newsPagination.current_page === 1}
						onclick={() => handlePageChange($newsPagination.current_page - 1)}
					>
						<ChevronLeft class="w-4 h-4 md:w-5 md:h-5" />
					</button>

					<!-- Page Numbers -->
					{#each generatePagination($newsPagination.current_page, $newsPagination.last_page) as page}
						{#if page === '...'}
							<span
								class="w-9 h-9 md:w-10 md:h-10 flex items-center justify-center text-xs md:text-sm text-gray-400"
								>...</span
							>
						{:else}
							<button
								class="w-9 h-9 md:w-10 md:h-10 flex items-center justify-center text-xs md:text-sm rounded-md border transition-colors cursor-pointer {page ===
								$newsPagination.current_page
									? 'bg-red-500 text-white border-red-500'
									: 'bg-white dark:bg-zinc-800 border-gray-200 dark:border-zinc-700 hover:bg-gray-50 dark:hover:bg-zinc-700'}"
								onclick={() => handlePageChange(Number(page))}
							>
								{page}
							</button>
						{/if}
					{/each}

					<!-- Next Button -->
					<button
						class="w-9 h-9 md:w-10 md:h-10 flex items-center justify-center rounded-md bg-white dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-zinc-700 transition-colors"
						disabled={$newsPagination.current_page === $newsPagination.last_page}
						onclick={() => handlePageChange($newsPagination.current_page + 1)}
					>
						<ChevronRight class="w-4 h-4 md:w-5 md:h-5" />
					</button>
				</div>
			</div>
		{/if}
	{/if}
</div>
