<script lang="ts">
	import {
		LayoutGrid,
		List,
		Calendar,
		X,
		ChevronDown,
		Search,
		SlidersHorizontal
	} from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { slide } from 'svelte/transition';
	import { onMount } from 'svelte';
	import { ticketsStore } from '$lib/stores';
	import { logger } from '$lib/utils/logger';

	interface Props {
		filters?: import('$lib/types').TicketFilters;
		viewMode?: 'GRID' | 'TABLE';
		showViewToggle?: boolean;
		dropdownPlacement?: 'left' | 'right';
		isSidebar?: boolean;
		onfilterChange?: (filters: import('$lib/types').TicketFilters) => void;
	}

	let {
		filters = {},
		viewMode = $bindable('GRID'),
		showViewToggle = true,
		dropdownPlacement = 'right',
		isSidebar = false,
		onfilterChange
	}: Props = $props();

	const { t } = useTranslation();

	let showFilters = $state(false);
	let availableTitles: string[] = $state([]);
	let isLoadingTitles = $state(false);

	// Local state for debouncing
	let title = $state('');
	let hasTwoShot = $state(false);
	let startDate = $state('');
	let endDate = $state('');
	let selectedDays: string[] = $state([]);

	// Initialize from filters prop
	$effect.pre(() => {
		title = filters.title || '';
		hasTwoShot = filters.hasTwoShot || false;
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
				!filterButton?.contains(event.target as Node)
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

	let activeFilterCount = $derived(
		(hasTwoShot ? 1 : 0) + (startDate ? 1 : 0) + (endDate ? 1 : 0) + selectedDays.length
	);
</script>

<div class="flex flex-col gap-4 w-full relative">
	<div class="flex items-center gap-3 w-full">
		<!-- Title Dropdown -->
		<div class="relative flex-1 group">
			<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none">
				{#if isLoadingTitles}
					<div
						class="w-4 h-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin"
					></div>
				{:else}
					<Search class="w-4 h-4" />
				{/if}
			</div>

			<select
				bind:value={title}
				onchange={updateFilters}
				class="w-full pl-10 pr-10 py-2 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-full text-sm font-medium text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm transition-all appearance-none cursor-pointer"
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
		<button
			bind:this={filterButton}
			onclick={() => (showFilters = !showFilters)}
			class={`p-2 rounded-full transition-all border shadow-sm cursor-pointer relative ${showFilters || activeFilterCount > 0 ? 'bg-blue-50 border-blue-200 text-blue-600' : 'bg-white dark:bg-zinc-900 border-gray-200 dark:border-zinc-700 text-gray-500 hover:text-gray-700'}`}
			title="Advanced Filters"
		>
			<SlidersHorizontal class="w-4 h-4" />
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
				class="flex bg-white dark:bg-zinc-900 p-1 rounded-full border border-gray-200 dark:border-zinc-700 shadow-sm shrink-0"
			>
				<button
					onclick={() => (viewMode = 'GRID')}
					class={`p-2 rounded-full transition-all cursor-pointer ${viewMode === 'GRID' ? 'bg-blue-50 dark:bg-blue-500/20 text-blue-600 shadow-sm' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
					title="Grid View"
				>
					<LayoutGrid class="w-4 h-4" />
				</button>
				<button
					onclick={() => (viewMode = 'TABLE')}
					class={`p-2 rounded-full transition-all cursor-pointer ${viewMode === 'TABLE' ? 'bg-blue-50 dark:bg-blue-500/20 text-blue-600 shadow-sm' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
					title="Table View"
				>
					<List class="w-4 h-4" />
				</button>
			</div>
		{/if}
	</div>

	<!-- Advanced Filters Panel -->
	{#if showFilters}
		<div
			use:clickOutside
			transition:slide={{ duration: 200 }}
			class={`absolute top-full mt-2 p-4 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl shadow-lg flex flex-col gap-5 z-50 
                ${isSidebar ? 'left-0 right-0 w-auto' : 'w-[calc(100vw-2rem)] md:w-auto md:min-w-[400px]'} 
                ${!isSidebar && dropdownPlacement === 'right' ? 'right-0' : 'left-0'}`}
		>
			<div class={`flex gap-4 ${isSidebar ? 'flex-col' : 'flex-wrap items-center'}`}>
				<!-- 2-Shot Toggle -->
				<label class="flex items-center gap-3 cursor-pointer select-none group">
					<div class="relative">
						<input
							type="checkbox"
							class="sr-only"
							bind:checked={hasTwoShot}
							onchange={updateFilters}
						/>
						<div
							class={`w-10 h-6 rounded-full transition-colors ${hasTwoShot ? (isSidebar ? 'bg-red-500' : 'bg-blue-500') : 'bg-gray-200 dark:bg-zinc-700 group-hover:bg-gray-300'}`}
						></div>
						<div
							class={`absolute top-1 left-1 bg-white w-4 h-4 rounded-full transition-transform shadow-sm ${hasTwoShot ? 'translate-x-4' : 'translate-x-0'}`}
						></div>
					</div>
					<span class="text-sm font-bold text-gray-700 dark:text-gray-300"
						>{t('common.hasTwoShot')}</span
					>
				</label>

				<!-- Date Range -->
				<div class={isSidebar ? 'flex flex-col gap-2 w-full' : 'flex flex-col gap-1'}>
					{#if isSidebar}
						<div class="text-[10px] uppercase font-black text-gray-400 tracking-wider mb-0.5">
							{t('common.dateRange')}
						</div>
					{/if}
					<div class={isSidebar ? 'flex flex-col items-stretch gap-2' : 'flex items-center gap-2'}>
						<div class="relative flex-1">
							<Calendar
								class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none"
							/>
							<input
								type="date"
								bind:value={startDate}
								onchange={updateFilters}
								class={`w-full text-xs bg-gray-50 dark:bg-zinc-800/50 border border-gray-100 dark:border-zinc-700 rounded-lg pl-8 pr-2 py-2 focus:ring-2 outline-none cursor-pointer transition-all placeholder:text-gray-300 ${isSidebar ? 'focus:ring-red-500/20 focus:border-red-500' : 'focus:ring-blue-500/20 focus:border-blue-500'}`}
							/>
						</div>
						{#if !isSidebar}
							<span class="text-gray-400 px-1">-</span>
						{/if}
						<div class="relative flex-1">
							<Calendar
								class="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400 pointer-events-none"
							/>
							<input
								type="date"
								bind:value={endDate}
								onchange={updateFilters}
								class={`w-full text-xs bg-gray-50 dark:bg-zinc-800/50 border border-gray-100 dark:border-zinc-700 rounded-lg pl-8 pr-2 py-2 focus:ring-2 outline-none cursor-pointer transition-all placeholder:text-gray-300 ${isSidebar ? 'focus:ring-red-500/20 focus:border-red-500' : 'focus:ring-blue-500/20 focus:border-blue-500'}`}
							/>
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
										: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-600 dark:text-blue-400'
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
