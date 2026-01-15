<script lang="ts">
	import { onMount } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { History, Calendar, ExternalLink, Clock, ChevronLeft, ChevronRight } from 'lucide-svelte';
	import { EmptyState, ErrorState } from '$lib/components';
	import { fade } from 'svelte/transition';

	import { EventHistorySkeleton } from '$lib/components/skeletons';
	import {
		eventsStore,
		historyEvents,
		historyLoading,
		historyPagination,
		historyError
	} from '$lib/stores/events';

	const { t } = useTranslation();

	onMount(async () => {
		await eventsStore.loadHistory(1);
	});

	$: isLoading = $historyLoading;
	$: error = $historyError;

	function handlePageChange(page: number) {
		eventsStore.loadHistory(page);
	}

	function formatDate(dateStr: string) {
		const date = new Date(dateStr);
		return date.toLocaleDateString('en-GB', {
			day: 'numeric',
			month: 'short',
			year: '2-digit'
		});
	}

	function formatTime(dateStr: string) {
		const date = new Date(dateStr);
		return date.toLocaleTimeString('en-US', {
			hour: '2-digit',
			minute: '2-digit',
			hour12: false
		});
	}

	function generatePagination(current: number, total: number) {
		const delta = 2;
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
	title={$t('theater.eventHistory.title')}
	path="/theater/events/history"
	description={$t('theater.eventHistory.subtitle')}
/>

<div class="space-y-6">
	{#if isLoading}
		<EventHistorySkeleton rows={10} />
	{:else if error}
		<ErrorState
			title={$t('theater.eventHistory.errorTitle') || 'Failed to load history'}
			description={$t('theater.eventHistory.errorDesc') || error || ''}
			onRetry={() => eventsStore.loadHistory($historyPagination.current_page)}
		/>
	{:else if $historyEvents.length === 0}
		<EmptyState
			icon={History}
			title={$t('theater.eventHistory.emptyTitle')}
			description={$t('theater.eventHistory.empty')}
		/>
	{:else}
		<div class="glass-panel rounded-3xl overflow-hidden shadow-sm" in:fade={{ duration: 300 }}>
			<div class="overflow-x-auto">
				<table class="w-full text-left border-collapse">
					<thead>
						<tr
							class="bg-gray-50/80 dark:bg-zinc-800/80 border-b border-gray-200 dark:border-zinc-700 text-xs uppercase tracking-wider text-gray-500 dark:text-gray-400 font-bold"
						>
							<th class="p-4">{$t('common.date')}</th>
							<th class="p-4">{$t('theater.events.eventName')}</th>
							<th class="p-4">{$t('theater.eventHistory.table.type')}</th>
							<th class="p-4">{$t('theater.eventHistory.table.members')}</th>
							<th class="p-4 text-right">{$t('theater.eventHistory.table.link')}</th>
						</tr>
					</thead>
					<tbody
						class="bg-white/50 dark:bg-zinc-900/50 divide-y divide-gray-100 dark:divide-zinc-700"
					>
						{#each $historyEvents as event}
							<tr
								class="group border-b border-gray-100 dark:border-zinc-700 hover:bg-orange-50/30 dark:hover:bg-orange-900/10 transition-colors"
							>
								<td class="p-4 whitespace-nowrap">
									<div class="flex flex-col">
										<span class="font-bold text-gray-800 dark:text-gray-200 text-sm">
											{formatDate(event.date)}
										</span>
										<span
											class="text-xs text-gray-400 dark:text-gray-500 flex items-center gap-1 mt-0.5"
										>
											<Clock class="w-3 h-3" />
											{formatTime(event.date)}
										</span>
									</div>
								</td>
								<td class="p-4">
									<div class="flex items-center gap-3">
										<div
											class="w-12 h-8 rounded bg-gray-100 dark:bg-zinc-800 overflow-hidden flex-shrink-0 border border-gray-200 dark:border-zinc-700"
										>
											{#if event.imageUrl}
												<img
													src={event.imageUrl}
													alt="Setlist"
													class="w-full h-full object-cover"
												/>
											{:else}
												<div class="w-full h-full flex items-center justify-center">
													<Calendar class="w-4 h-4 text-gray-400" />
												</div>
											{/if}
										</div>
										<div class="font-bold text-gray-800 dark:text-gray-200 text-sm">
											{event.title}
										</div>
									</div>
								</td>
								<td class="p-4 text-themed-secondary">
									{#if event.team?.img}
										<div class="flex items-center">
											<img
												src={`https://jkt48.com${event.team.img}`}
												alt={event.team.id || 'Team'}
												class="w-10 h-10 object-contain"
											/>
										</div>
									{:else if event.label}
										<div class="flex items-center">
											<img
												src={`https://jkt48.com${event.label}`}
												alt="Type"
												class="w-10 h-10 object-contain"
											/>
										</div>
									{:else}
										<div class="text-gray-400 w-10 text-center">-</div>
									{/if}
								</td>
								<td class="p-4 text-themed-secondary font-medium">
									{event.totalMembers > 0 ? event.totalMembers : '-'}
								</td>
								<td class="p-4 text-right">
									<a
										href={`https://jkt48.com${event.url}`}
										target="_blank"
										class="inline-flex p-2 text-gray-400 hover:text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-lg transition-colors"
									>
										<ExternalLink class="w-4 h-4" />
									</a>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			<!-- Numbered Pagination -->
			{#if $historyPagination.last_page > 1}
				<div
					class="bg-gray-50 dark:bg-zinc-800/50 border-t border-gray-100 dark:border-zinc-800 px-6 py-4 flex items-center justify-between"
				>
					<span class="text-xs text-themed-secondary">
						{$t('theater.eventHistory.pagination.pageOf', {
							current: $historyPagination.current_page,
							last: $historyPagination.last_page
						})}
					</span>
					<div class="flex gap-2">
						<!-- Previous Button -->
						<button
							class="w-8 h-8 flex items-center justify-center rounded-md bg-white dark:bg-zinc-900 border border-gray-200 disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-zinc-800 transition-colors"
							disabled={$historyPagination.current_page === 1}
							on:click={() => handlePageChange($historyPagination.current_page - 1)}
						>
							<ChevronLeft class="w-4 h-4" />
						</button>

						<!-- Page Numbers -->
						{#each generatePagination($historyPagination.current_page, $historyPagination.last_page) as page}
							{#if page === '...'}
								<span class="w-8 h-8 flex items-center justify-center text-xs text-gray-400"
									>...</span
								>
							{:else}
								<button
									class="w-8 h-8 flex items-center justify-center text-xs rounded-md border transition-colors cursor-pointer {page ===
									$historyPagination.current_page
										? 'bg-orange-500 text-white border-orange-500'
										: 'bg-white dark:bg-zinc-900 border-gray-200 dark:border-zinc-700 hover:bg-gray-50 dark:hover:bg-zinc-800'}"
									on:click={() => handlePageChange(Number(page))}
								>
									{page}
								</button>
							{/if}
						{/each}

						<!-- Next Button -->
						<button
							class="w-8 h-8 flex items-center justify-center rounded-md bg-white dark:bg-zinc-900 border border-gray-200 disabled:opacity-50 cursor-pointer disabled:cursor-not-allowed hover:bg-gray-50 dark:hover:bg-zinc-800 transition-colors"
							disabled={$historyPagination.current_page === $historyPagination.last_page}
							on:click={() => handlePageChange($historyPagination.current_page + 1)}
						>
							<ChevronRight class="w-4 h-4" />
						</button>
					</div>
				</div>
			{/if}
		</div>
	{/if}
</div>
