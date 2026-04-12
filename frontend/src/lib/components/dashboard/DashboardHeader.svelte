<script lang="ts">
	import { LayoutDashboard, Filter } from 'lucide-svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { MONTHS } from '$lib/constants';

	const { t } = useTranslation();

	interface Props {
		/**
		 * Dashboard header component when filter panel is closed
		 */
		filter: any;
		onOpenFilter: () => void;
		isOpen?: boolean;
	}

	let { filter, onOpenFilter, isOpen = false }: Props = $props();

	function getFilterLabel(filter: any, tParams: any) {
		if (filter.isAllData) return tParams('common.allData');

		const startMonthKey = MONTHS[filter.startMonth].substring(0, 3).toLowerCase();
		const endMonthKey = MONTHS[filter.endMonth].substring(0, 3).toLowerCase();

		const startMonthStr = tParams(`time.monthsShort.${startMonthKey}`);
		const endMonthStr = tParams(`time.monthsShort.${endMonthKey}`);

		if (filter.startMonth === 0 && filter.endMonth === 11) {
			return `${filter.selectedYear}`;
		}

		return `${startMonthStr} - ${endMonthStr} ${filter.selectedYear}`;
	}
	let displayLabel = $derived(filter ? getFilterLabel(filter, $t) : '');
</script>

<PageHeader
	title={$t('dashboard.title')}
	subtitle={$t('dashboard.subtitle')}
	icon={LayoutDashboard}
	theme="red"
>
	{#snippet actions()}
		<div class="flex items-center gap-2">
			<span
				class="text-[10px] sm:text-xs font-black text-gray-700 dark:text-gray-200 bg-white dark:bg-zinc-800 px-3 py-1.5 rounded-full border border-gray-100 dark:border-white/5 shadow-sm whitespace-nowrap flex items-center justify-center h-8 sm:h-9"
			>
				{displayLabel}
			</span>
			<button
				onclick={onOpenFilter}
				data-filter-toggle="true"
				class={`flex items-center gap-2 px-4 py-1.5 sm:py-2 rounded-full font-bold text-xs shadow-sm border transition-all cursor-pointer h-8 sm:h-9 ${
					isOpen
						? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800 text-red-600 dark:text-red-400'
						: 'bg-white dark:bg-zinc-900 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-zinc-700 hover:border-red-200 dark:hover:border-red-500/50 hover:text-red-600 dark:hover:text-red-400'
				}`}
			>
				<Filter class="w-4 h-4" />
				<span class="hidden sm:inline">{$t('common.filters')}</span>
			</button>
		</div>
	{/snippet}
</PageHeader>
