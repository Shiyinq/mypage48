<script lang="ts">
	import { Calendar, ChevronDown } from 'lucide-svelte';
	import { liveHistoryFilterStore, type FilterType } from '$lib/stores/liveHistoryFilter.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	let tempStart = $state(liveHistoryFilterStore.customRange.start);
	let tempEnd = $state(liveHistoryFilterStore.customRange.end);

	function handleTypeChange(e: Event) {
		const select = e.target as HTMLSelectElement;
		liveHistoryFilterStore.setFilterType(select.value as FilterType);
	}

	function handleCustomDateChange() {
		if (tempStart && tempEnd) {
			liveHistoryFilterStore.setCustomRange(tempStart, tempEnd);
		}
	}

	$effect(() => {
		tempStart = liveHistoryFilterStore.customRange.start;
		tempEnd = liveHistoryFilterStore.customRange.end;
	});
</script>

<div
	class="p-4 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl shadow-lg flex flex-col gap-4 w-full md:w-[360px]"
>
	<!-- Filter Selection -->
	<div class="flex flex-col gap-2">
		<label
			for="filter-select"
			class="md:hidden text-xs font-bold text-gray-400 uppercase tracking-wider"
			>{t('common.filters')}</label
		>
		<div class="relative group">
			<select
				id="filter-select"
				bind:value={liveHistoryFilterStore.filterType}
				onchange={handleTypeChange}
				class="w-full appearance-none bg-gray-50 hover:bg-gray-100 dark:bg-zinc-800 dark:hover:bg-zinc-700 border border-gray-200 dark:border-zinc-700 pl-4 pr-10 py-2.5 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-red-500 cursor-pointer transition-colors"
			>
				<option value="this_week">{t('liveHistory.thisWeek')}</option>
				<option value="this_month">{t('liveHistory.thisMonth')}</option>
				<option value="this_year">{t('liveHistory.thisYear')}</option>
				<option value="all_time">{t('liveHistory.allTime')}</option>
				<option value="custom">{t('liveHistory.customRange')}</option>
			</select>
			<ChevronDown
				class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none group-hover:text-red-500 transition-colors"
			/>
		</div>
	</div>

	<!-- Custom Date Range -->
	{#if liveHistoryFilterStore.filterType === 'custom'}
		<div class="flex flex-col gap-2">
			<span class="text-xs font-bold text-gray-400 uppercase tracking-wider"
				>{t('liveHistory.customRange')}</span
			>
			<div class="flex flex-col sm:flex-row items-center gap-2">
				<div
					class="flex items-center bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 rounded-lg shadow-sm overflow-hidden flex-1 w-full px-3 py-2 gap-2"
				>
					<span class="text-[10px] font-bold text-gray-500 uppercase tracking-wider shrink-0"
						>{t('common.fromShort')}</span
					>
					<div class="relative w-full flex items-center">
						<input
							type="date"
							bind:value={tempStart}
							onchange={handleCustomDateChange}
							class="w-full bg-transparent text-xs font-medium text-gray-700 dark:text-gray-300 focus:outline-none cursor-pointer color-scheme-dark z-10"
						/>
						<Calendar class="absolute right-0 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
					</div>
				</div>
				<div
					class="flex items-center bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 rounded-lg shadow-sm overflow-hidden flex-1 w-full px-3 py-2 gap-2"
				>
					<span class="text-[10px] font-bold text-gray-500 uppercase tracking-wider shrink-0"
						>{t('common.toShort')}</span
					>
					<div class="relative w-full flex items-center">
						<input
							type="date"
							bind:value={tempEnd}
							onchange={handleCustomDateChange}
							class="w-full bg-transparent text-xs font-medium text-gray-700 dark:text-gray-300 focus:outline-none cursor-pointer color-scheme-dark z-10"
						/>
						<Calendar class="absolute right-0 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
					</div>
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	input[type='date'].color-scheme-dark {
		color-scheme: light dark;
	}

	input[type='date']::-webkit-calendar-picker-indicator {
		cursor: pointer;
		opacity: 0;
		width: 100%;
		height: 100%;
		position: absolute;
		right: 0;
		top: 0;
		margin: 0;
		padding: 0;
	}
</style>
