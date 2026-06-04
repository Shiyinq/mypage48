<script lang="ts">
	import { ChevronLeft, Filter } from 'lucide-svelte';
	import type { ComponentType } from 'svelte';
	import { slide } from 'svelte/transition';
	import HistoryDateFilter from './HistoryDateFilter.svelte';
	import { liveHistoryFilterStore } from '$lib/stores/liveHistoryFilter.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	interface Props {
		title: string;
		subtitle?: string;
		icon: ComponentType;
		iconColor?: string;
		showDateFilter?: boolean;
		onBack?: () => void;
	}

	let {
		title,
		subtitle = '',
		icon: Icon,
		iconColor = 'text-red-500',
		showDateFilter = false,
		onBack
	}: Props = $props();

	let isFilterOpen = $state(false);

	let displayLabel = $derived.by(() => {
		const type = liveHistoryFilterStore.filterType;
		if (type === 'this_week') return t('liveHistory.thisWeek');
		if (type === 'this_month') return t('liveHistory.thisMonth');
		if (type === 'this_year') return t('liveHistory.thisYear');
		if (type === 'all_time') return t('liveHistory.allTime');
		if (type === 'custom') {
			const start = liveHistoryFilterStore.customRange.start;
			const end = liveHistoryFilterStore.customRange.end;
			if (start && end) return `${start} / ${end}`;
			return t('liveHistory.customRange');
		}
		return '';
	});

	function handleBack() {
		if (onBack) {
			onBack();
		} else {
			history.back();
		}
	}

	function clickOutside(node: HTMLElement) {
		const handleClick = (event: MouseEvent) => {
			const target = event.target as Element;
			if (node && !node.contains(target) && !target.closest('[data-filter-toggle="true"]')) {
				isFilterOpen = false;
			}
		};
		document.addEventListener('click', handleClick, true);
		return {
			destroy() {
				document.removeEventListener('click', handleClick, true);
			}
		};
	}
</script>

<div
	class="relative w-full z-[10000] shrink-0 border-b border-gray-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md"
>
	<div class="h-14 flex items-center justify-between px-4">
		<button
			onclick={handleBack}
			class="flex items-center gap-3 cursor-pointer group text-left min-w-0 flex-1"
		>
			<div
				class="flex items-center justify-center w-8 h-8 rounded-full group-hover:bg-gray-100 dark:group-hover:bg-zinc-800 text-slate-600 dark:text-zinc-400 transition-colors shrink-0"
			>
				<ChevronLeft size={20} />
			</div>
			<div class="flex flex-col min-w-0">
				<h1
					class="text-sm font-bold text-slate-900 dark:text-white truncate flex items-center gap-1.5"
				>
					<Icon size={14} class={iconColor} />
					{title}
				</h1>
				{#if subtitle}
					<p class="text-[10px] text-slate-500 dark:text-zinc-400 truncate font-medium">
						{subtitle}
					</p>
				{/if}
			</div>
		</button>

		{#if showDateFilter}
			<div class="flex items-center gap-2">
				<span
					class="hidden md:flex text-[10px] sm:text-xs font-black text-gray-700 dark:text-gray-200 bg-white dark:bg-zinc-800 px-3 py-1.5 rounded-full border border-gray-100 dark:border-white/5 shadow-sm whitespace-nowrap items-center justify-center h-8 sm:h-9"
				>
					{displayLabel}
				</span>
				<button
					onclick={() => (isFilterOpen = !isFilterOpen)}
					data-filter-toggle="true"
					class={`flex items-center justify-center rounded-full font-bold transition-all cursor-pointer border
						${
							isFilterOpen
								? 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border-red-100 dark:border-red-800 sm:border-red-200'
								: 'bg-gray-50 dark:bg-zinc-800 text-gray-500 dark:text-gray-400 border-gray-100 dark:border-zinc-700 sm:bg-white sm:dark:bg-zinc-900 sm:text-gray-600 sm:dark:text-gray-300 sm:border-gray-200 hover:border-red-200 dark:hover:border-red-500/50 hover:text-red-600 dark:hover:text-red-400'
						}
						w-8 h-8 shadow-none sm:w-auto sm:h-9 sm:px-4 sm:py-2 sm:gap-2 sm:text-xs sm:shadow-sm`}
				>
					<Filter class="w-4 h-4 shrink-0" />
					<span class="hidden sm:inline">{t('common.filters')}</span>
				</button>
			</div>
		{/if}
	</div>

	{#if showDateFilter && isFilterOpen}
		<div
			use:clickOutside
			transition:slide={{ duration: 200 }}
			class="absolute top-full left-0 right-0 md:left-auto md:right-4 mt-2 px-4 md:px-0 z-[7000]"
		>
			<HistoryDateFilter />
		</div>
	{/if}
</div>
