<script lang="ts">
	import { Calendar, ChevronDown } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { MONTHS } from '$lib/constants/time';

	const { t } = useTranslation();

	export let isAllData: boolean;
	export let selectedYear: number;
	export let startMonth: number;
	export let endMonth: number;
	export let availableYears: number[];
</script>

<div
	class="p-4 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl shadow-lg flex flex-col gap-4"
>
	<!-- All Data Toggle -->
	<label class="flex items-center gap-3 cursor-pointer select-none">
		<div class="relative">
			<input type="checkbox" class="sr-only" bind:checked={isAllData} />
			<div
				class={`w-10 h-6 rounded-full transition-colors ${isAllData ? 'bg-red-500' : 'bg-gray-200 dark:bg-zinc-700'}`}
			></div>
			<div
				class={`absolute top-1 left-1 bg-white w-4 h-4 rounded-full transition-transform ${isAllData ? 'translate-x-4' : 'translate-x-0'}`}
			></div>
		</div>
		<span class="text-sm font-bold text-gray-700 dark:text-gray-200">
			{$t('common.allData')}
		</span>
	</label>

	<!-- Date Selection -->
	<div class="flex flex-col gap-3 {isAllData ? 'opacity-50 pointer-events-none' : ''}">
		<!-- Year Select -->
		<div class="relative group w-full">
			<select
				bind:value={selectedYear}
				disabled={isAllData}
				class="w-full appearance-none bg-white dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 pl-10 pr-10 py-2 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-red-500 cursor-pointer transition-colors disabled:cursor-not-allowed"
			>
				{#each availableYears as y}
					<option value={y}>{y}</option>
				{/each}
			</select>
			<Calendar
				class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 group-hover:text-red-500 transition-colors"
			/>
			<ChevronDown
				class="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none group-hover:text-red-500 transition-colors"
			/>
		</div>

		<!-- Months Range -->
		<div
			class="flex items-center bg-white dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 rounded-lg shadow-sm w-full overflow-hidden"
		>
			<div
				class="relative flex-1 border-r border-gray-200 dark:border-zinc-700 hover:bg-gray-50 dark:hover:bg-zinc-700 transition-colors"
			>
				<select
					bind:value={startMonth}
					disabled={isAllData}
					class="w-full appearance-none bg-transparent pl-8 pr-2 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 focus:outline-none cursor-pointer disabled:cursor-not-allowed"
				>
					{#each MONTHS as m, i}
						<option value={i}>{m.substring(0, 3)}</option>
					{/each}
				</select>
				<span
					class="absolute left-3 top-1/2 -translate-y-1/2 text-[10px] font-bold text-gray-400 uppercase tracking-wider pointer-events-none"
					>Fr</span
				>
			</div>
			<div class="relative flex-1 hover:bg-gray-50 dark:hover:bg-zinc-700 transition-colors">
				<select
					bind:value={endMonth}
					disabled={isAllData}
					class="w-full appearance-none bg-transparent pl-8 pr-2 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 focus:outline-none cursor-pointer disabled:cursor-not-allowed"
				>
					{#each MONTHS as m, i}
						<option value={i}>{m.substring(0, 3)}</option>
					{/each}
				</select>
				<span
					class="absolute left-3 top-1/2 -translate-y-1/2 text-[10px] font-bold text-gray-400 uppercase tracking-wider pointer-events-none"
					>To</span
				>
			</div>
		</div>
	</div>
</div>
