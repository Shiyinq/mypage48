<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
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
	import SEO from '$lib/components/SEO.svelte';

	const { t } = useTranslation();

	const basePath = '/jkt48/news';

	let mounted = $state(false);

	onMount(async () => {
		await newsStore.load();
		mounted = true;
	});

	let list = $derived(newsList.value);
	let pagination = $derived(newsPagination.value);
	let isLoading = $derived(newsLoading.value);
	let error = $derived(newsError.value);

	async function handlePageChange(pageIdx: number) {
		newsStore.load(pageIdx);
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

		for (const i of range) {
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
	path="/jkt48/news"
	description={$t('seo.news')}
	articles={list}
/>

<div class="space-y-12 pt-4 md:pt-6 pb-12 px-0 sm:px-0">
	<div class="text-center space-y-4 mb-8">
		<h1
			class="text-3xl md:text-5xl font-black text-slate-900 dark:text-white tracking-tighter uppercase mb-3"
		>
			{$t('theater.news.title') || 'News'}
		</h1>
		<p
			class="text-base md:text-lg text-slate-500 dark:text-slate-400 font-medium max-w-2xl mx-auto uppercase tracking-widest leading-relaxed"
		>
			{$t('theater.news.subtitle') || 'Latest updates and announcements'}
		</p>
	</div>

	{#if (!mounted || isLoading) && list.length === 0}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
			{#each Array(8) as _}
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
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
			{#each list as item (item.news_id)}
				<a
					href={`${basePath}/${item.link}`}
					class="group flex flex-row md:flex-col bg-white dark:bg-zinc-900 shadow-sm hover:shadow-2xl hover:-translate-y-1 rounded-[2rem] border border-gray-100 dark:border-white/5 transition-all duration-500 overflow-hidden"
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
								class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
								loading="lazy"
							/>
						{:else}
							<div
								class="absolute inset-0 bg-gradient-to-br from-red-500/10 to-red-700/10 flex items-center justify-center"
							>
								<Newspaper class="w-10 h-10 md:w-16 md:h-16 text-red-500/20" />
							</div>
						{/if}
						<div
							class="absolute inset-0 bg-gradient-to-t from-black/20 md:from-black/60 via-transparent to-transparent"
						></div>

						<div class="absolute top-4 right-4 z-10">
							<span
								class="inline-flex items-center px-3 py-1 rounded-full text-[10px] font-black tracking-widest uppercase shadow-lg {item.category.toLowerCase() ===
								'event'
									? 'bg-red-600 text-white'
									: item.category.toLowerCase() === 'theater'
										? 'bg-cyan-600 text-white'
										: 'bg-orange-600 text-white'}"
							>
								{item.category}
							</span>
						</div>
					</div>

					<!-- Content -->
					<div class="p-4 md:p-6 flex flex-col flex-1 justify-between w-[62%] md:w-full">
						<div>
							<div
								class="flex gap-2 items-center mb-3 text-slate-400 dark:text-slate-500 text-xs font-bold uppercase tracking-wider"
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
								class="font-black text-slate-900 dark:text-white leading-tight mb-4 group-hover:text-red-600 transition-colors text-base md:text-lg line-clamp-3"
							>
								{item.title}
							</h3>
						</div>

						<div
							class="mt-auto pt-4 border-t flex items-center justify-between text-xs text-slate-400 font-bold uppercase tracking-widest border-gray-50 dark:border-white/5"
						>
							<span class="flex items-center gap-2 group-hover:text-red-600 transition-colors">
								{$t('theater.news.readMore')}
								<ChevronRight class="w-4 h-4 group-hover:translate-x-1 transition-transform" />
							</span>
						</div>
					</div>
				</a>
			{/each}
		</div>

		<!-- Numbered Pagination -->
		{#if pagination && pagination.last_page > 1}
			<div class="flex items-center justify-center mt-12 mb-12 w-full">
				<div class="flex flex-wrap justify-center gap-2 max-w-full">
					<!-- Previous Button -->
					<button
						class="w-10 h-10 flex items-center justify-center rounded-full bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed hover:bg-red-50 dark:hover:bg-red-900/10 hover:text-red-600 hover:border-red-200 transition-all shadow-sm"
						disabled={pagination.current_page === 1}
						onclick={() => handlePageChange(pagination.current_page - 1)}
					>
						<ChevronLeft class="w-5 h-5" />
					</button>

					<!-- Page Numbers -->
					{#each generatePagination(pagination.current_page, pagination.last_page) as page}
						{#if page === '...'}
							<span
								class="w-10 h-10 flex items-center justify-center text-sm font-bold text-gray-400"
								>...</span
							>
						{:else}
							<button
								class="w-10 h-10 flex items-center justify-center text-sm font-bold rounded-full border transition-all cursor-pointer {page ===
								pagination.current_page
									? 'bg-red-600 text-white border-red-600 shadow-lg shadow-red-500/30'
									: 'bg-white dark:bg-zinc-900 border-gray-100 dark:border-zinc-800 text-gray-500 hover:text-red-600 hover:border-red-200 shadow-sm'}"
								onclick={() => handlePageChange(Number(page))}
							>
								{page}
							</button>
						{/if}
					{/each}

					<!-- Next Button -->
					<button
						class="w-10 h-10 flex items-center justify-center rounded-full bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed hover:bg-red-50 dark:hover:bg-red-900/10 hover:text-red-600 hover:border-red-200 transition-all shadow-sm"
						disabled={pagination.current_page === pagination.last_page}
						onclick={() => handlePageChange(pagination.current_page + 1)}
					>
						<ChevronRight class="w-5 h-5" />
					</button>
				</div>
			</div>
		{/if}
	{/if}
</div>
