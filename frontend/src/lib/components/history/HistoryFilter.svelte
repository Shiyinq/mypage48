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
	import { createEventDispatcher, onMount } from 'svelte';
	import { ticketsStore } from '$lib/stores';

	export let filters: import('$lib/types').TicketFilters = {};
	export let viewMode: 'GRID' | 'TABLE' = 'GRID';

	const dispatch = createEventDispatcher<{
		filterChange: import('$lib/types').TicketFilters;
	}>();

	const { t } = useTranslation();

	let showFilters = false;
	let availableTitles: string[] = [];
	let isLoadingTitles = false;

	// Local state for debouncing
	let title = filters.title || '';
	let hasTwoShot = filters.hasTwoShot || false;
	let startDate = filters.startDate || '';
	let endDate = filters.endDate || '';
	let selectedDays: string[] = filters.days || [];

	const daysOfWeek = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

	onMount(async () => {
		try {
			isLoadingTitles = true;
			availableTitles = await ticketsStore.getAvailableTitles();
		} catch (e) {
			console.error('Failed to load ticket titles', e);
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

		dispatch('filterChange', newFilters);
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

	let filterButton: HTMLButtonElement;

	$: activeFilterCount =
		(hasTwoShot ? 1 : 0) + (startDate ? 1 : 0) + (endDate ? 1 : 0) + selectedDays.length;
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
				on:change={updateFilters}
				class="w-full pl-10 pr-10 py-2 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-full text-sm font-medium text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm transition-all appearance-none cursor-pointer"
			>
				<option value="">{$t('common.allSetlists') || 'All Setlists'}</option>
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
			on:click={() => (showFilters = !showFilters)}
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
		<div
			class="flex bg-white dark:bg-zinc-900 p-1 rounded-full border border-gray-200 dark:border-zinc-700 shadow-sm"
		>
			<button
				on:click={() => (viewMode = 'GRID')}
				class={`p-2 rounded-full transition-all cursor-pointer ${viewMode === 'GRID' ? 'bg-blue-50 dark:bg-blue-500/20 text-blue-600 shadow-sm' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
				title="Grid View"
			>
				<LayoutGrid class="w-4 h-4" />
			</button>
			<button
				on:click={() => (viewMode = 'TABLE')}
				class={`p-2 rounded-full transition-all cursor-pointer ${viewMode === 'TABLE' ? 'bg-blue-50 dark:bg-blue-500/20 text-blue-600 shadow-sm' : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'}`}
				title="Table View"
			>
				<List class="w-4 h-4" />
			</button>
		</div>
	</div>

	<!-- Advanced Filters Panel -->
	{#if showFilters}
		<div
			use:clickOutside
			transition:slide={{ duration: 200 }}
			class="absolute top-full right-0 mt-2 p-4 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl shadow-lg flex flex-col gap-4 z-50 w-[calc(100vw-2rem)] md:w-auto md:min-w-[500px]"
		>
			<div class="flex flex-wrap gap-4 items-center">
				<!-- 2-Shot Toggle -->
				<label class="flex items-center gap-2 cursor-pointer select-none">
					<div class="relative">
						<input
							type="checkbox"
							class="sr-only"
							bind:checked={hasTwoShot}
							on:change={updateFilters}
						/>
						<div
							class={`w-10 h-6 rounded-full transition-colors ${hasTwoShot ? 'bg-blue-500' : 'bg-gray-200 dark:bg-zinc-700'}`}
						></div>
						<div
							class={`absolute top-1 left-1 bg-white w-4 h-4 rounded-full transition-transform ${hasTwoShot ? 'translate-x-4' : 'translate-x-0'}`}
						></div>
					</div>
					<span class="text-sm font-medium text-gray-700 dark:text-gray-300"
						>{$t('common.hasTwoShot')}</span
					>
				</label>

				<!-- Date Range -->
				<div class="flex flex-wrap items-center gap-2">
					<Calendar class="w-4 h-4 text-gray-400" />
					<input
						type="date"
						bind:value={startDate}
						on:change={updateFilters}
						class="text-sm bg-transparent border border-gray-200 dark:border-zinc-700 rounded-lg px-2 py-1 focus:ring-2 focus:ring-blue-500 outline-none cursor-pointer"
					/>
					<span class="text-gray-400">-</span>
					<input
						type="date"
						bind:value={endDate}
						on:change={updateFilters}
						class="text-sm bg-transparent border border-gray-200 dark:border-zinc-700 rounded-lg px-2 py-1 focus:ring-2 focus:ring-blue-500 outline-none cursor-pointer"
					/>
				</div>
			</div>

			<!-- Days Selector -->
			<div class="flex flex-wrap gap-2">
				{#each daysOfWeek as day}
					<button
						on:click={() => toggleDay(day)}
						class={`px-3 py-1 rounded-full text-xs font-medium border transition-colors cursor-pointer ${
							selectedDays.includes(day)
								? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800 text-blue-600 dark:text-blue-400'
								: 'bg-transparent border-gray-200 dark:border-zinc-700 text-gray-600 dark:text-gray-400 hover:border-gray-300'
						}`}
					>
						{$t(`time.days.${day.toLowerCase()}`)}
					</button>
				{/each}
			</div>

			<!-- Clear Filters -->
			<div class="flex justify-end">
				<button
					on:click={clearFilters}
					class="text-xs text-red-500 hover:text-red-600 font-medium flex items-center gap-1 cursor-pointer"
				>
					<X class="w-3 h-3" />
					{$t('common.clearFilters')}
				</button>
			</div>
		</div>
	{/if}
</div>
