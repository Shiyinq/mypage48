<script lang="ts">
	import { slide } from 'svelte/transition';
	import { Filter, Check } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	let {
		selectedLabels = $bindable([]),
		options = ['EVENT', 'SHOW', 'EXCLUSIVE', 'DREAM', 'LOVE', 'TRAINEE']
	} = $props<{
		selectedLabels: string[];
		options?: string[];
	}>();

	let isOpen = $state(false);

	function toggleLabel(label: string) {
		if (selectedLabels.includes(label)) {
			selectedLabels = selectedLabels.filter((l: string) => l !== label);
		} else {
			selectedLabels = [...selectedLabels, label];
		}
	}

	function clickOutside(node: HTMLElement) {
		const handleClick = (event: MouseEvent) => {
			const target = event.target as Element;
			if (node && !node.contains(target) && !target.closest('[data-filter-toggle="true"]')) {
				isOpen = false;
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

<div class="relative">
	<button
		data-filter-toggle="true"
		class="flex items-center gap-2 px-3 py-1.5 sm:py-2 rounded-full font-bold text-[10px] sm:text-xs shadow-sm border transition-all cursor-pointer h-8 sm:h-9 {selectedLabels.length >
		0
			? 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border-red-200 dark:border-red-800'
			: 'bg-white dark:bg-zinc-900 text-gray-600 dark:text-gray-300 border-gray-200 dark:border-zinc-700 hover:border-red-200 dark:hover:border-red-500/50 hover:text-red-600 dark:hover:text-red-400'}"
		onclick={() => (isOpen = !isOpen)}
	>
		<Filter size={16} />
		{t('common.filter') || 'Filter'}
		{#if selectedLabels.length > 0}
			<span
				class="ml-1 px-1.5 py-0.5 rounded-full bg-slate-100 text-slate-500 font-black text-[9px] dark:bg-zinc-800 dark:text-zinc-400"
			>
				{selectedLabels.length}
			</span>
		{/if}
	</button>

	{#if isOpen}
		<div
			use:clickOutside
			transition:slide={{ duration: 200 }}
			class="absolute right-0 top-full mt-2 w-56 sm:w-64 bg-white dark:bg-zinc-900 rounded-2xl shadow-xl border border-gray-100 dark:border-zinc-800 p-3 sm:p-4 z-50"
		>
			<div class="flex items-center justify-between mb-3">
				<h3 class="text-sm font-bold text-gray-900 dark:text-white">
					{t('theater.events.filterBy') || 'Filter By'}
				</h3>
				{#if selectedLabels.length > 0}
					<button
						class="text-xs text-red-500 hover:text-red-600 font-medium cursor-pointer"
						onclick={() => (selectedLabels = [])}
					>
						{t('common.clear') || 'Clear'}
					</button>
				{/if}
			</div>

			<div class="flex flex-col gap-1.5 max-h-64 overflow-y-auto custom-scrollbar pr-1">
				{#each options as option}
					<button
						class="flex items-center justify-between w-full px-3 py-2 text-xs sm:text-sm rounded-xl transition-colors cursor-pointer {selectedLabels.includes(
							option
						)
							? 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 font-bold'
							: 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-zinc-800 font-medium'}"
						onclick={() => toggleLabel(option)}
					>
						<span>{t(`theater.events.labels.${option.toLowerCase()}`) || option}</span>
						{#if selectedLabels.includes(option)}
							<Check size={16} />
						{/if}
					</button>
				{/each}
			</div>
		</div>
	{/if}
</div>
