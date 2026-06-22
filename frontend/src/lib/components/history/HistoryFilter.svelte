<script lang="ts">
	import { LayoutGrid, List, Calendar, X, ChevronDown, Search, Filter } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { fly } from 'svelte/transition';
	import { onMount } from 'svelte';
	import { ticketsStore } from '$lib/stores';
	import { logger } from '$lib/utils/logger';

	interface Props {
		filters?: import('$lib/types').TicketFilters;
		viewMode?: 'GRID' | 'TABLE';
		showViewToggle?: boolean;
		dropdownPlacement?: 'left' | 'right';
		isSidebar?: boolean;
		showTwoShotToggle?: boolean;
		showFilters?: boolean;
		hideFilterButton?: boolean;
		hideViewToggleOnMobile?: boolean;
		activeFilterCount?: number;
		onfilterChange?: (filters: import('$lib/types').TicketFilters) => void;
		cardOnly?: boolean;
	}

	let {
		filters = {},
		viewMode = $bindable('GRID'),
		showViewToggle = true,
		dropdownPlacement = 'right',
		isSidebar = false,
		showTwoShotToggle = true,
		showFilters = $bindable(false),
		hideViewToggleOnMobile = false,
		activeFilterCount = $bindable(0),
		onfilterChange,
		cardOnly = false
	}: Props = $props();

	const { t } = useTranslation();

	let availableTitles: string[] = $state([]);
	let isLoadingTitles = $state(false);

	// Local state for debouncing
	let title = $state('');
	let hasTwoShot = $state(false);
	let isFavorite = $state(false);
	let startDate = $state('');
	let endDate = $state('');
	let selectedDays: string[] = $state([]);

	// Initialize from filters prop
	$effect.pre(() => {
		title = filters.title || '';
		hasTwoShot = filters.hasTwoShot || false;
		isFavorite = filters.isFavorite || false;
		startDate = filters.startDate || '';
		endDate = filters.endDate || '';
		selectedDays = filters.days || [];
	});

	const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

	onMount(async () => {
		try {
			isLoadingTitles = true;
			availableTitles = await ticketsStore.getAvailableTitles();
		} catch (e) {
			logger.error('Failed to load ticket titles', e, { context: 'HistoryFilter' });
		} finally {
			isLoadingTitles = false;
		}
	});

	function updateFilters() {
		const newFilters: import('$lib/types').TicketFilters = {};
		if (title) newFilters.title = title;
		if (hasTwoShot) newFilters.hasTwoShot = true;
		if (isFavorite) newFilters.isFavorite = true;
		if (startDate) newFilters.startDate = startDate;
		if (endDate) newFilters.endDate = endDate;
		if (selectedDays.length > 0) newFilters.days = selectedDays;

		onfilterChange?.(newFilters);
	}

	function toggleDay(day: string) {
		if (selectedDays.includes(day)) {
			selectedDays = selectedDays.filter((d) => d !== day);
		} else {
			selectedDays = [...selectedDays, day];
		}
		updateFilters();
	}

	function clearFilters() {
		title = '';
		hasTwoShot = false;
		isFavorite = false;
		startDate = '';
		endDate = '';
		selectedDays = [];
		updateFilters();
		showFilters = false;
	}

	function clickOutside(node: HTMLElement) {
		const handleClick = (event: MouseEvent) => {
			if (
				node &&
				!node.contains(event.target as Node) &&
				!filterButton?.contains(event.target as Node) &&
				!(event.target as Element).closest('[data-filter-toggle="true"]') &&
				!(event.target as Element).closest('[data-filter-card="true"]')
			) {
				showFilters = false;
			}
		};

		document.addEventListener('click', handleClick, true);

		return {
			destroy() {
				document.removeEventListener('click', handleClick, true);
			}
		};
	}

	let filterButton: HTMLButtonElement | undefined = $state();

	$effect(() => {
		activeFilterCount =
			(hasTwoShot ? 1 : 0) +
			(isFavorite ? 1 : 0) +
			(startDate ? 1 : 0) +
			(endDate ? 1 : 0) +
			selectedDays.length;
	});
</script>

<div class="flex flex-col gap-4 w-full relative">
	{#if !cardOnly}
		<div class="flex items-center gap-3 w-full">
			<!-- Title Dropdown -->
			<div class="relative flex-1 group">
				<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none">
					{#if isLoadingTitles}
						<div
							class="w-4 h-4 border-2 border-gray-300 border-t-red-500 rounded-full animate-spin"
						></div>
					{:else}
						<Search class="w-4 h-4" />
					{/if}
				</div>

				<select
					id="history-setlist-select"
					name="setlist"
					bind:value={title}
					onchange={updateFilters}
					class="w-full pl-10 pr-10 py-2 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-full text-sm font-medium text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent shadow-sm transition-all appearance-none cursor-pointer"
					aria-label={t('common.allSetlists') || 'All Setlists'}
				>
					<option value="">{t('common.allSetlists') || 'All Setlists'}</option>
					{#each availableTitles as t}
						<option value={t}>{t}</option>
					{/each}
				</select>

				<ChevronDown
					class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"
				/>
			</div>

			<!-- Filter Toggle Button -->
			<!-- Filter Toggle Button (Hidden on Mobile) -->
			<button
				bind:this={filterButton}
				onclick={() => (showFilters = !showFilters)}
				data-filter-toggle="true"
				class={`flex items-center gap-2 px-4 py-2 h-9 rounded-full transition-all border shadow-sm cursor-pointer relative font-bold text-xs ${showFilters || activeFilterCount > 0 ? 'bg-red-50 border-red-200 text-red-600' : 'bg-white dark:bg-zinc-900 border-gray-200 dark:border-zinc-700 text-gray-500 hover:text-gray-700'}`}
				title="Advanced Filters"
			>
				<Filter class="w-4 h-4" />
				<span>{t('common.filters') || 'Filters'}</span>
				{#if activeFilterCount > 0}
					<span
						class="absolute -top-1 -right-1 flex h-3 w-3 items-center justify-center rounded-full bg-red-500"
					>
						<span
							class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"
						></span>
						<span class="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
					</span>
				{/if}
			</button>

			<!-- View Toggle -->
			{#if showViewToggle}
				<div
					class={`flex bg-white dark:bg-zinc-900 p-1 rounded-full border border-gray-200 dark:border-zinc-700 shadow-sm shrink-0 ${hideViewToggleOnMobile ? 'hidden md:flex' : ''}`}
				>
					<button
						onclick={() => (viewMode = 'GRID')}
						class={`p-2 rounded-full transition-all cursor-pointer ${viewMode === 'GRID' ? 'bg-red-50 dark:bg-red-500/20 text-red-600 shadow-sm' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
						title="Grid View"
					>
						<LayoutGrid class="w-4 h-4" />
					</button>
					<button
						onclick={() => (viewMode = 'TABLE')}
						class={`p-2 rounded-full transition-all cursor-pointer ${viewMode === 'TABLE' ? 'bg-red-50 dark:bg-red-500/20 text-red-600 shadow-sm' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
						title="Table View"
					>
						<List class="w-4 h-4" />
					</button>
				</div>
			{/if}
		</div>
	{/if}

	<!-- Advanced Filters Panel -->
	{#if showFilters}
		<div
			use:clickOutside
			data-filter-card="true"
			transition:fly={{ y: -10, duration: 200 }}
			class={`fixed md:absolute top-[72px] md:top-full left-4 right-4 md:left-auto md:right-0 mt-0 md:mt-2 p-4 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-2xl md:rounded-xl shadow-lg flex flex-col gap-5 z-[7000] 
                ${isSidebar ? 'md:left-0 md:right-0 w-auto' : 'md:w-auto md:min-w-[400px]'} 
                ${!isSidebar && dropdownPlacement === 'right' ? 'md:right-0' : 'md:left-0'}`}
		>
			<div
				class={`flex gap-4 ${isSidebar ? 'flex-col' : 'flex-col sm:flex-row sm:flex-wrap sm:items-center items-start'}`}
			>
				{#if cardOnly}
					<!-- Title Dropdown (Mobile Card Only) -->
					<div class="relative flex-1 w-full group">
						<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none">
							{#if isLoadingTitles}
								<div
									class="w-4 h-4 border-2 border-gray-300 border-t-red-500 rounded-full animate-spin"
								></div>
							{:else}
								<Search class="w-4 h-4" />
							{/if}
						</div>

						<select
							id="history-mobile-setlist-select"
							name="setlist"
							bind:value={title}
							onchange={updateFilters}
							class="w-full pl-10 pr-10 py-2.5 bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-xl text-sm font-bold text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent shadow-sm transition-all appearance-none cursor-pointer"
							aria-label={t('common.allSetlists') || 'All Setlists'}
						>
							<option value="">{t('common.allSetlists') || 'All Setlists'}</option>
							{#each availableTitles as listTitle}
								<option value={listTitle}>{listTitle}</option>
							{/each}
						</select>

						<ChevronDown
							class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none"
						/>
					</div>
				{/if}

				<!-- 2-Shot Toggle -->
				{#if showTwoShotToggle}
					<label
						for="filter-has-twoshot"
						class="flex items-center gap-3 cursor-pointer select-none group"
					>
						<div class="relative">
							<input
								id="filter-has-twoshot"
								name="has_two_shot"
								type="checkbox"
								class="sr-only"
								bind:checked={hasTwoShot}
								onchange={updateFilters}
							/>
							<div
								class={`w-10 h-6 rounded-full transition-colors ${hasTwoShot ? (isSidebar ? 'bg-red-500' : 'bg-red-500') : 'bg-gray-200 dark:bg-zinc-700 group-hover:bg-gray-300'}`}
							></div>
							<div
								class={`absolute top-1 left-1 bg-white w-4 h-4 rounded-full transition-transform shadow-sm ${hasTwoShot ? 'translate-x-4' : 'translate-x-0'}`}
							></div>
						</div>
						<span class="text-sm font-bold text-gray-700 dark:text-gray-300"
							>{t('common.hasTwoShot')}</span
						>
					</label>
				{/if}

				<label
					for="filter-is-favorite"
					class="flex items-center gap-3 cursor-pointer select-none group"
				>
					<div class="relative">
						<input
							id="filter-is-favorite"
							name="is_favorite"
							type="checkbox"
							class="sr-only"
							bind:checked={isFavorite}
							onchange={updateFilters}
						/>
						<div
							class={`w-10 h-6 rounded-full transition-colors ${isFavorite ? (isSidebar ? 'bg-red-500' : 'bg-red-500') : 'bg-gray-200 dark:bg-zinc-700 group-hover:bg-gray-300'}`}
						></div>
						<div
							class={`absolute top-1 left-1 bg-white w-4 h-4 rounded-full transition-transform shadow-sm ${isFavorite ? 'translate-x-4' : 'translate-x-0'}`}
						></div>
					</div>
					<span class="text-sm font-bold text-gray-700 dark:text-gray-300">
						{t('common.favorite') || 'Favorite'}
					</span>
				</label>

				<!-- Date Range -->
				<div class={isSidebar ? 'flex flex-col gap-2 w-full' : 'flex flex-col gap-1 w-full'}>
					{#if isSidebar}
						<div class="text-[10px] uppercase font-black text-gray-400 tracking-wider mb-0.5">
							{t('common.dateRange')}
						</div>
					{/if}
					<div
						class={isSidebar
							? 'flex flex-col items-stretch gap-2'
							: 'flex flex-row items-center gap-2 w-full'}
					>
						<!-- Start Date -->
						<div
							class={`flex items-center bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-lg shadow-sm overflow-hidden flex-1 min-w-0 px-2 py-1.5 sm:px-3 sm:py-2 gap-1.5 sm:gap-2 transition-all focus-within:ring-2 focus-within:border-transparent ${isSidebar ? 'focus-within:ring-red-500' : 'focus-within:ring-red-500'}`}
						>
							<label
								for="filter-start-date"
								class="text-[9px] sm:text-[10px] font-bold text-gray-500 uppercase tracking-wider shrink-0 cursor-pointer"
								>{t('common.fromShort') || 'Dari'}</label
							>
							<div class="relative w-full flex items-center min-w-0">
								<input
									id="filter-start-date"
									name="start_date"
									type="date"
									bind:value={startDate}
									onchange={updateFilters}
									class="w-full min-w-0 pr-4 sm:pr-0 bg-transparent text-[10px] sm:text-xs font-medium text-gray-700 dark:text-gray-300 focus:outline-none cursor-pointer color-scheme-dark z-10"
									aria-label={t('common.fromShort') || 'Dari'}
								/>
								<Calendar
									class="absolute right-0 w-3 h-3 sm:w-3.5 sm:h-3.5 text-gray-400 pointer-events-none"
								/>
							</div>
						</div>

						<!-- End Date -->
						<div
							class={`flex items-center bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-lg shadow-sm overflow-hidden flex-1 min-w-0 px-2 py-1.5 sm:px-3 sm:py-2 gap-1.5 sm:gap-2 transition-all focus-within:ring-2 focus-within:border-transparent ${isSidebar ? 'focus-within:ring-red-500' : 'focus-within:ring-red-500'}`}
						>
							<label
								for="filter-end-date"
								class="text-[9px] sm:text-[10px] font-bold text-gray-500 uppercase tracking-wider shrink-0 cursor-pointer"
								>{t('common.toShort') || 'Ke'}</label
							>
							<div class="relative w-full flex items-center min-w-0">
								<input
									id="filter-end-date"
									name="end_date"
									type="date"
									bind:value={endDate}
									onchange={updateFilters}
									class="w-full min-w-0 pr-4 sm:pr-0 bg-transparent text-[10px] sm:text-xs font-medium text-gray-700 dark:text-gray-300 focus:outline-none cursor-pointer color-scheme-dark z-10"
									aria-label={t('common.toShort') || 'Ke'}
								/>
								<Calendar
									class="absolute right-0 w-3 h-3 sm:w-3.5 sm:h-3.5 text-gray-400 pointer-events-none"
								/>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Days Selector -->
			<div class={isSidebar ? 'flex flex-col gap-2' : 'flex flex-col gap-1.5'}>
				{#if isSidebar}
					<div class="text-[10px] uppercase font-black text-gray-400 tracking-wider">
						{t('common.days')}
					</div>
				{/if}
				<div class={isSidebar ? 'grid grid-cols-4 gap-1.5' : 'flex flex-wrap gap-1.5'}>
					{#each daysOfWeek as day}
						<button
							onclick={() => toggleDay(day)}
							class={`transition-all cursor-pointer text-center font-bold px-3 py-1.5 border ${
								isSidebar ? 'rounded-lg text-[10px]' : 'rounded-full text-xs'
							} ${
								selectedDays.includes(day)
									? isSidebar
										? 'bg-red-50 dark:bg-red-500/10 border-red-200 dark:border-red-800 text-red-600 dark:text-red-400'
										: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-600 dark:text-red-400'
									: 'bg-transparent border-gray-100 dark:border-zinc-800 text-gray-500 dark:text-gray-400 hover:border-gray-200 hover:text-gray-700 dark:hover:text-gray-200'
							}`}
						>
							{isSidebar
								? t(`time.days.${day.toLowerCase()}`).substring(0, 3)
								: t(`time.days.${day.toLowerCase()}`)}
						</button>
					{/each}
				</div>
			</div>

			<!-- Clear Filters -->
			<div
				class={`flex justify-end pt-1 border-t border-gray-50 dark:border-white/5 ${isSidebar ? '' : 'mt-2'}`}
			>
				<button
					onclick={clearFilters}
					class={`text-[10px] font-bold flex items-center gap-1 transition-colors uppercase tracking-wider cursor-pointer ${isSidebar ? 'text-gray-400 hover:text-red-500' : 'text-red-500 hover:text-red-600'}`}
				>
					<X class="w-3 h-3" />
					{t('common.clearFilters')}
				</button>
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
