<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { formatDate, formatTime } from '$lib/i18n';
	import {
		History,
		Calendar,
		ExternalLink,
		Clock,
		ChevronLeft,
		ChevronRight,
		Cake
	} from 'lucide-svelte';
	import { EmptyState, ErrorState } from '$lib/components';
	import { fade } from 'svelte/transition';
	import { EventHistorySkeleton } from '$lib/components/skeletons';
	import {
		eventsStore,
		historyEvents,
		isHistoryEventsLoading,
		historyPagination,
		historyError
	} from '$lib/stores/events.svelte';
	import SEO from '$lib/components/SEO.svelte';

	const { t } = useTranslation();

	onMount(async () => {
		await eventsStore.loadHistory(1);
	});

	let error = $derived(historyError.value);
	let eventsList = $derived(historyEvents.value);
	let loading = $derived(isHistoryEventsLoading.value);
	let paginationObj = $derived(historyPagination.value);

	async function handlePageChange(page: number) {
		eventsStore.loadHistory(page);
		await tick();
		setTimeout(() => {
			window.scrollTo({
				top: 0,
				behavior: 'smooth'
			});
		}, 10);
	}

	function generatePagination(current: number, total: number) {
		const delta = 2;
		const range = [];
		const rangeWithDots = [];
		let l;
		range.push(1);
		if (total <= 1) return range;
		for (let i = current - delta; i <= current + delta; i++) {
			if (i < total && i > 1) range.push(i);
		}
		range.push(total);
		for (let i of range) {
			if (l) {
				if (i - l === 2) rangeWithDots.push(l + 1);
				else if (i - l !== 1) rangeWithDots.push('...');
			}
			rangeWithDots.push(i);
			l = i;
		}
		return rangeWithDots;
	}
</script>

<SEO
	title={$t('theater.eventHistory.title')}
	path="/jkt48/event-history"
	description={$t('theater.eventHistory.subtitle')}
/>

<div class="space-y-16 pt-4 md:pt-6 pb-12">
	<div class="text-center space-y-4 mb-8">
		<h1
			class="text-3xl md:text-5xl font-black text-slate-900 dark:text-white tracking-tighter uppercase mb-3"
		>
			{$t('theater.eventHistory.title')}
		</h1>
		<p
			class="text-base md:text-lg text-slate-500 dark:text-slate-400 font-medium max-w-2xl mx-auto uppercase tracking-widest"
		>
			{$t('theater.eventHistory.subtitle')}
		</p>
	</div>

	{#if loading && eventsList.length === 0}
		<EventHistorySkeleton rows={10} />
	{:else if error}
		<ErrorState
			title={$t('theater.eventHistory.errorTitle') || 'Failed to load history'}
			description={$t('theater.eventHistory.errorDesc') || error || ''}
			onRetry={() => eventsStore.loadHistory(paginationObj.current_page)}
		/>
	{:else if eventsList.length === 0}
		<EmptyState
			icon={History}
			title={$t('theater.eventHistory.emptyTitle')}
			description={$t('theater.eventHistory.empty')}
		/>
	{:else}
		<div
			class="bg-white dark:bg-zinc-900 rounded-[2.5rem] overflow-hidden shadow-xl border border-gray-100 dark:border-zinc-800"
			in:fade={{ duration: 300 }}
		>
			<div class="overflow-x-auto">
				<table class="w-full text-left border-collapse">
					<thead>
						<tr
							class="bg-slate-50 dark:bg-zinc-800/50 border-b border-gray-100 dark:border-zinc-800 text-[10px] uppercase font-black tracking-[0.2em] text-slate-400"
						>
							<th class="p-6">{$t('common.date')}</th>
							<th class="p-6">{$t('theater.events.eventName')}</th>
							<th class="p-6">{$t('theater.eventHistory.table.type')}</th>
							<th class="p-6">{$t('theater.eventHistory.table.members')}</th>
							<th class="p-6 text-right">{$t('theater.eventHistory.table.link')}</th>
						</tr>
					</thead>
					<tbody class="divide-y divide-gray-50 dark:divide-zinc-800">
						{#each eventsList as event}
							<tr
								class="group hover:bg-slate-50/50 dark:hover:bg-zinc-800/30 transition-all duration-300"
							>
								<td class="p-6 whitespace-nowrap">
									<div class="flex flex-col">
										<span class="font-black text-slate-900 dark:text-white text-sm">
											{$formatDate(event.date, { day: 'numeric', month: 'short', year: 'numeric' })}
										</span>
										<span
											class="text-[10px] text-slate-400 font-bold uppercase tracking-wider flex items-center gap-1.5 mt-1"
										>
											<Clock class="w-3 h-3" />
											{$formatTime(event.date, { hour: '2-digit', minute: '2-digit' })}
										</span>
									</div>
								</td>
								<td class="p-6">
									<div class="flex items-center gap-4">
										<div
											class="w-16 h-10 rounded-xl overflow-hidden shadow-sm border border-gray-100 dark:border-zinc-800 shrink-0"
										>
											{#if event.imageUrl}
												<img
													src={event.imageUrl}
													alt="Event"
													class="w-full h-full object-cover transition-transform group-hover:scale-110 duration-500"
												/>
											{:else}
												<div
													class="w-full h-full bg-red-500/10 flex items-center justify-center text-red-500"
												>
													<Calendar size={16} />
												</div>
											{/if}
										</div>
										<div class="space-y-1">
											<div
												class="font-black text-slate-900 dark:text-white text-sm group-hover:text-red-600 transition-colors"
											>
												{event.title}
											</div>
											<div class="flex items-center gap-3">
												{#if (event.seitansaiMembers?.length ?? 0) > 0}
													<div
														class="flex items-center gap-1.5 text-[10px] text-pink-500 font-black uppercase tracking-wider"
													>
														<Cake size={12} />
														<span>{event.seitansaiMembers?.join(', ')}</span>
													</div>
												{/if}
											</div>
										</div>
									</div>
								</td>
								<td class="p-6 text-xs font-black uppercase tracking-widest text-slate-400">
									{event.type || event.label || '-'}
								</td>
								<td class="p-6 font-black text-slate-900 dark:text-white text-sm">
									{event.totalMembers > 1 ? event.totalMembers : '-'}
								</td>
								<td class="p-6 text-right">
									<a
										href={`https://jkt48.com${event.url}`}
										target="_blank"
										class="inline-flex p-3 rounded-full bg-slate-50 dark:bg-zinc-800 text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/10 transition-all"
									>
										<ExternalLink size={14} />
									</a>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			<!-- Pagination -->
			{#if paginationObj.last_page > 1}
				<div
					class="bg-slate-50 dark:bg-zinc-800/30 px-8 py-6 flex items-center justify-between border-t border-gray-50 dark:border-zinc-800"
				>
					<span class="text-[10px] font-black uppercase tracking-widest text-slate-400">
						Page {paginationObj.current_page} of {paginationObj.last_page}
					</span>
					<div class="flex gap-2">
						<button
							class="w-10 h-10 flex items-center justify-center rounded-full bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-all hover:border-red-600 hover:text-red-600 shadow-sm"
							disabled={paginationObj.current_page === 1}
							onclick={() => handlePageChange(paginationObj.current_page - 1)}
						>
							<ChevronLeft size={18} />
						</button>
						{#each generatePagination(paginationObj.current_page, paginationObj.last_page) as page}
							<button
								class="w-10 h-10 flex items-center justify-center text-xs font-black rounded-full border transition-all {page ===
								paginationObj.current_page
									? 'bg-red-600 text-white border-red-600 shadow-lg shadow-red-500/30'
									: 'bg-white dark:bg-zinc-900 border-gray-100 dark:border-zinc-800 text-slate-500 hover:border-red-600 hover:text-red-600 shadow-sm'} {typeof page ===
								'number'
									? 'cursor-pointer'
									: 'cursor-default'}"
								onclick={() => typeof page === 'number' && handlePageChange(page)}
								disabled={typeof page !== 'number'}
							>
								{page}
							</button>
						{/each}
						<button
							class="w-10 h-10 flex items-center justify-center rounded-full bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-all hover:border-red-600 hover:text-red-600 shadow-sm"
							disabled={paginationObj.current_page === paginationObj.last_page}
							onclick={() => handlePageChange(paginationObj.current_page + 1)}
						>
							<ChevronRight size={18} />
						</button>
					</div>
				</div>
			{/if}
		</div>
	{/if}
</div>
