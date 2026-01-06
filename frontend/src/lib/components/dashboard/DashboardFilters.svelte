<script lang="ts">
	import { Calendar, ChevronDown, Filter, X } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { MONTHS } from '$lib/constants/time';

	const { t } = useTranslation();

	/**
	 * Dashboard filter panel component
	 */
	export let isOpen: boolean;
	export let isAllData: boolean;
	export let selectedYear: number;
	export let startMonth: number;
	export let endMonth: number;
	export let availableYears: number[];

	function close() {
		isOpen = false;
	}

	function toggleAllData() {
		isAllData = !isAllData;
	}
</script>

<div class="glass-panel p-4 rounded-3xl animate-fade-in">
	<div class="flex items-start justify-between mb-4 md:mb-0 md:items-center gap-4">
		<div class="flex items-center gap-3">
			<div
				class="bg-red-50 dark:bg-red-500/20 p-2.5 rounded-xl text-red-600 dark:text-red-400 shadow-sm ring-1 ring-red-100 dark:ring-red-500/30"
			>
				<Filter class="w-5 h-5" />
			</div>
			<div>
				<h2 class="font-bold text-gray-800 dark:text-gray-100 text-lg leading-none">
					{$t('dashboard.filterTitle')}
				</h2>
				<p class="text-xs text-gray-400 font-medium mt-1">
					{$t('dashboard.filterSubtitle')}
				</p>
			</div>
		</div>
		<button
			on:click={close}
			class="p-2 hover:bg-red-50 dark:hover:bg-white/5 text-gray-400 hover:text-red-500 dark:hover:text-red-400 rounded-full transition-colors cursor-pointer"
		>
			<X class="w-5 h-5" />
		</button>
	</div>

	<!-- All Data Toggle -->
	<div class="mt-4 flex items-center gap-3">
		<button
			on:click={toggleAllData}
			class={`relative flex items-center px-4 py-2.5 rounded-xl font-bold text-sm transition-all w-full justify-center gap-2 cursor-pointer ${isAllData ? 'bg-red-600 text-white shadow-lg shadow-red-200 dark:shadow-red-900/20' : 'bg-gray-100 dark:bg-white/5 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-white/10'}`}
		>
			<span
				class={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${isAllData ? 'border-white bg-white' : 'border-gray-400'}`}
			>
				{#if isAllData}
					<span class="w-2 h-2 rounded-full bg-red-600"></span>
				{/if}
			</span>
			{$t('common.allData')}
		</button>
	</div>

	<div
		class="mt-4 md:mt-4 grid grid-cols-1 md:grid-cols-2 gap-3 w-full {isAllData
			? 'opacity-50 pointer-events-none'
			: ''}"
	>
		<div class="relative group w-full">
			<select
				bind:value={selectedYear}
				disabled={isAllData}
				class="w-full appearance-none bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 pl-10 pr-10 py-2.5 rounded-xl text-sm font-bold text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-red-500 shadow-sm cursor-pointer hover:border-red-200 dark:hover:border-red-500/50 transition-colors disabled:cursor-not-allowed disabled:bg-gray-100 dark:disabled:bg-gray-900"
			>
				{#each availableYears as y}
					<option value={y}>{y}</option>
				{/each}
			</select>
			<Calendar class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-red-400" />
			<ChevronDown
				class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none group-hover:text-red-400 transition-colors"
			/>
		</div>

		<div
			class="flex items-center bg-white dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-xl shadow-sm w-full overflow-hidden h-[42px]"
		>
			<div
				class="relative flex-1 h-full border-r border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
			>
				<select
					bind:value={startMonth}
					disabled={isAllData}
					class="w-full h-full appearance-none bg-transparent pl-9 pr-2 text-xs font-bold text-gray-700 dark:text-gray-200 focus:outline-none cursor-pointer disabled:cursor-not-allowed"
				>
					{#each MONTHS as m, i}
						<option value={i}>{m.substring(0, 3)}</option>
					{/each}
				</select>
				<span
					class="absolute left-3 top-1/2 -translate-y-1/2 text-[10px] font-extrabold text-gray-400 uppercase tracking-wider pointer-events-none"
					>Fr</span
				>
			</div>

			<div class="relative flex-1 h-full hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
				<select
					bind:value={endMonth}
					disabled={isAllData}
					class="w-full h-full appearance-none bg-transparent pl-9 pr-2 text-xs font-bold text-gray-700 focus:outline-none cursor-pointer disabled:cursor-not-allowed"
				>
					{#each MONTHS as m, i}
						<option value={i}>{m.substring(0, 3)}</option>
					{/each}
				</select>
				<span
					class="absolute left-3 top-1/2 -translate-y-1/2 text-[10px] font-extrabold text-gray-400 uppercase tracking-wider pointer-events-none"
					>To</span
				>
			</div>
		</div>
	</div>
</div>
