<script lang="ts">
	import { onMount } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { createSorter } from '$lib/stores/sorter.svelte';
	import { sorterNavbarStore } from '$lib/stores/sorterNavbar.svelte';

	import { Calendar, Trash2, Eye, History, Loader2 } from 'lucide-svelte';
	import { fade, fly } from 'svelte/transition';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';

	const { t, locale } = useTranslation();
	const sorter = createSorter(t, '/theater/sorter');

	let deleteConfirmId = $state<string | null>(null);

	function parseUTCDate(dateStr: string) {
		const timePart = dateStr.split('T')[1] || '';
		if (!dateStr.endsWith('Z') && !timePart.includes('+') && !timePart.includes('-')) {
			return new Date(dateStr + 'Z');
		}
		return new Date(dateStr);
	}

	function formatDate(dateStr: string) {
		try {
			const d = parseUTCDate(dateStr);
			const localeMap: Record<string, string> = {
				id: 'id-ID',
				en: 'en-US',
				ja: 'ja-JP'
			};
			return d.toLocaleString(localeMap[locale.value] || 'id-ID', {
				dateStyle: 'medium',
				timeStyle: 'short'
			});
		} catch {
			return dateStr;
		}
	}

	function confirmDelete(id: string) {
		deleteConfirmId = id;
	}

	function cancelDelete() {
		deleteConfirmId = null;
	}

	function executeDelete(id: string) {
		sorter.deleteSavedHistory(id);
		deleteConfirmId = null;
	}

	onMount(() => {
		sorter.loadSavedHistories(true);
	});

	$effect(() => {
		sorterNavbarStore.update({
			pageType: 'history-list'
		});
		return () => {
			sorterNavbarStore.reset();
		};
	});
</script>

<SEO
	title={`${t('theater.sorter.history') || 'Riwayat Sorter'} - Oshi Sorter`}
	path="/theater/sorter/history"
	description={t('theater.sorter.subtitle')}
/>

<svelte:head></svelte:head>

<div
	class="w-full flex flex-col items-center justify-start min-h-[calc(100svh-64px)] pt-4 md:pt-8 pb-12 overflow-hidden"
>
	<div in:fade={{ duration: 300 }} class="w-full max-w-5xl mx-auto px-4 pb-12">
		{#if sorter.loadingHistory}
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
				{#each Array(3) as _}
					<div
						class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl p-5 min-h-[190px] flex flex-col justify-between animate-pulse"
					>
						<div class="space-y-4">
							<!-- Top: Date and delete skeleton -->
							<div class="flex items-center justify-between">
								<div class="flex items-center gap-1.5">
									<div class="w-3.5 h-3.5 bg-zinc-200 dark:bg-zinc-850 rounded-full"></div>
									<div class="h-3 w-24 bg-zinc-200 dark:bg-zinc-850 rounded-full"></div>
								</div>
								<div class="h-4 w-4 bg-zinc-200 dark:bg-zinc-850 rounded-md"></div>
							</div>
							<!-- Title skeleton -->
							<div class="h-5 w-2/3 bg-zinc-200 dark:bg-zinc-850 rounded-lg"></div>
							<!-- Description skeleton -->
							<div class="space-y-2">
								<div class="h-3 w-full bg-zinc-100 dark:bg-zinc-850/60 rounded-md"></div>
								<div class="h-3 w-5/6 bg-zinc-100 dark:bg-zinc-850/60 rounded-md"></div>
							</div>
						</div>
						<!-- Bottom: Filters & Button skeleton -->
						<div
							class="flex items-center justify-between pt-4 border-t border-zinc-100 dark:border-zinc-800/80 mt-4"
						>
							<div class="flex gap-1">
								<div class="h-4 w-12 bg-zinc-200 dark:bg-zinc-850 rounded-full"></div>
								<div class="h-4 w-12 bg-zinc-200 dark:bg-zinc-850 rounded-full"></div>
							</div>
							<div class="h-7 w-20 bg-zinc-200 dark:bg-zinc-850 rounded-xl"></div>
						</div>
					</div>
				{/each}
			</div>
		{:else if sorter.savedHistories.length === 0}
			<div
				class="flex flex-col items-center justify-center text-center p-8 sm:p-16 border-2 border-dashed border-zinc-200 dark:border-zinc-800 rounded-3xl bg-white/50 dark:bg-zinc-900/50 backdrop-blur-md"
			>
				<div
					class="w-16 h-16 bg-rose-50 dark:bg-rose-500/10 rounded-full flex items-center justify-center mb-4"
				>
					<History class="w-8 h-8 text-rose-500" />
				</div>
				<h3 class="text-lg font-black text-themed tracking-tight mb-2 uppercase">
					{t('theater.sorter.noHistoryTitle') || 'Belum Ada Riwayat'}
				</h3>
				<p
					class="text-xs font-medium text-zinc-400 dark:text-zinc-500 max-w-sm leading-relaxed mb-6"
				>
					{t('theater.sorter.noHistoryDesc') ||
						'Selesaikan sorter dan simpan hasilnya untuk melihat riwayat peringkat oshi terbaikmu di sini.'}
				</p>
			</div>
		{:else}
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
				{#each sorter.savedHistories as item, i (item._id)}
					<!-- svelte-ignore a11y_click_events_have_key_events -->
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<div
						in:fly={{ y: 20, delay: i * 50, duration: 400 }}
						onclick={() => sorter.viewHistoryDetail(item)}
						class="group relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl p-5 hover:border-rose-400 dark:hover:border-rose-500/50 transition-all hover:scale-[1.01] hover:shadow-xl hover:shadow-rose-500/[0.02] flex flex-col justify-between min-h-[190px] cursor-pointer"
					>
						<div class="space-y-3">
							<!-- Top: Date and delete icon -->
							<div
								class="flex items-center justify-between text-[10px] font-bold text-zinc-400 dark:text-zinc-500 uppercase tracking-wider"
							>
								<div class="flex items-center gap-1.5">
									<Calendar size={12} class="text-rose-500" />
									<span>{formatDate(item.created_at)}</span>
								</div>

								{#if deleteConfirmId === item._id}
									<div class="flex items-center gap-2" in:fade>
										<button
											onclick={(e) => {
												e.stopPropagation();
												executeDelete(item._id);
											}}
											class="px-2 py-0.5 bg-red-600 hover:bg-red-700 text-white rounded font-black text-[9px] cursor-pointer"
										>
											{t('theater.sorter.confirmYes').toUpperCase()}
										</button>
										<button
											onclick={(e) => {
												e.stopPropagation();
												cancelDelete();
											}}
											class="px-2 py-0.5 bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 rounded font-black text-[9px] cursor-pointer"
										>
											{t('theater.sorter.confirmCancel').toUpperCase()}
										</button>
									</div>
								{:else}
									<button
										onclick={(e) => {
											e.stopPropagation();
											confirmDelete(item._id);
										}}
										class="text-zinc-400 hover:text-red-600 dark:hover:text-red-400 p-1 rounded-lg transition-colors cursor-pointer bg-transparent border-none"
										title={t('theater.sorter.deleteHistory') || 'Hapus Riwayat'}
									>
										<Trash2 size={13} />
									</button>
								{/if}
							</div>

							<!-- Middle: Title & Description -->
							<div class="space-y-1">
								<h4
									class="font-black text-themed text-base group-hover:text-rose-500 transition-colors uppercase tracking-tight line-clamp-1 leading-snug"
								>
									{item.title}
								</h4>
								{#if item.description}
									<p
										class="text-xs font-semibold text-zinc-500 dark:text-zinc-400 line-clamp-2 leading-relaxed"
									>
										{item.description}
									</p>
								{/if}
							</div>
						</div>

						<!-- Bottom: Filters & View Button -->
						<div
							class="flex items-end justify-between pt-4 border-t border-zinc-100 dark:border-zinc-800/80 mt-4"
						>
							<!-- Filters pills -->
							<div class="flex flex-wrap gap-1 max-w-[70%]">
								{#each item.filters as gen}
									<span
										class="px-2 py-0.5 rounded-full text-[9px] font-black tracking-wider uppercase bg-rose-50/80 dark:bg-rose-500/10 border border-rose-100/50 dark:border-rose-900/30 text-rose-500 dark:text-rose-400 select-none"
									>
										{t('theater.sorter.genLabel', { gen })}
									</span>
								{/each}
							</div>

							<!-- Action -->
							<button
								onclick={(e) => {
									e.stopPropagation();
									sorter.viewHistoryDetail(item);
								}}
								class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-zinc-50 dark:bg-zinc-800 hover:bg-rose-500 hover:text-white border border-zinc-200 dark:border-zinc-700 hover:border-rose-600 transition-all font-black text-xs cursor-pointer group-hover:shadow-md group-hover:shadow-rose-500/10"
							>
								<Eye size={12} />
								<span>{t('theater.sorter.detail').toUpperCase()}</span>
							</button>
						</div>
					</div>
				{/each}
			</div>

			{#if sorter.historyHasMore}
				<div
					class="w-full h-20 flex items-center justify-center mt-6"
					use:infiniteScroll={{ rootMargin: '300px' }}
					onintersect={() => {
						if (!sorter.loadingHistory) sorter.loadSavedHistories(false);
					}}
				>
					{#if sorter.loadingHistory}
						<Loader2 class="w-6 h-6 text-rose-500 animate-spin" />
					{/if}
				</div>
			{/if}
		{/if}
	</div>
</div>
