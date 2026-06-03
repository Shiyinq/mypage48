<script lang="ts">
	import { Calendar } from 'lucide-svelte';
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

	// Watch for store changes to update local temp state if changed externally
	$effect(() => {
		tempStart = liveHistoryFilterStore.customRange.start;
		tempEnd = liveHistoryFilterStore.customRange.end;
	});
</script>

<div class="flex items-center gap-2">
	<div class="relative flex items-center">
		<div class="absolute left-2.5 pointer-events-none text-slate-500 dark:text-zinc-400">
			<Calendar size={14} />
		</div>
		<select
			value={liveHistoryFilterStore.filterType}
			onchange={handleTypeChange}
			class="appearance-none bg-gray-100 hover:bg-gray-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-slate-700 dark:text-zinc-300 text-[11px] font-medium rounded-full pl-8 pr-7 py-1.5 border border-transparent dark:border-zinc-700/50 focus:outline-none focus:ring-2 focus:ring-red-500/50 transition-colors cursor-pointer"
		>
			<option value="this_week">{t('liveHistory.thisWeek')}</option>
			<option value="this_month">{t('liveHistory.thisMonth')}</option>
			<option value="this_year">{t('liveHistory.thisYear')}</option>
			<option value="all_time">{t('liveHistory.allTime')}</option>
			<option value="custom">{t('liveHistory.customRange')}</option>
		</select>
		<!-- Custom dropdown arrow -->
		<div class="absolute right-2.5 pointer-events-none text-slate-500 dark:text-zinc-400">
			<svg
				width="10"
				height="10"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="2"
				stroke-linecap="round"
				stroke-linejoin="round"
			>
				<path d="m6 9 6 6 6-6" />
			</svg>
		</div>
	</div>

	{#if liveHistoryFilterStore.filterType === 'custom'}
		<div
			class="flex items-center gap-1.5 bg-gray-100 dark:bg-zinc-800 px-2 py-1 rounded-full border border-transparent dark:border-zinc-700/50"
		>
			<input
				type="date"
				bind:value={tempStart}
				onchange={handleCustomDateChange}
				class="bg-transparent text-[11px] text-slate-700 dark:text-zinc-300 font-medium focus:outline-none w-[90px] cursor-pointer color-scheme-dark"
			/>
			<span class="text-slate-400 dark:text-zinc-500 text-[10px]">-</span>
			<input
				type="date"
				bind:value={tempEnd}
				onchange={handleCustomDateChange}
				class="bg-transparent text-[11px] text-slate-700 dark:text-zinc-300 font-medium focus:outline-none w-[90px] cursor-pointer color-scheme-dark"
			/>
		</div>
	{/if}
</div>

<style>
	/* Make the calendar icon in date inputs dark mode friendly */
	input[type='date'].color-scheme-dark {
		color-scheme: light dark;
	}

	input[type='date']::-webkit-calendar-picker-indicator {
		cursor: pointer;
		opacity: 0.6;
		padding: 0;
	}

	input[type='date']::-webkit-calendar-picker-indicator:hover {
		opacity: 1;
	}
</style>
