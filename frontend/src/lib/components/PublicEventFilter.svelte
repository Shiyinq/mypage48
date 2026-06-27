<script lang="ts">
	import { Filter, Check } from 'lucide-svelte';
	import { slide } from 'svelte/transition';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	let {
		selectedLabels = $bindable<string[]>([]),
		options = ['SHOW', 'EVENT', 'EXCLUSIVE', 'LOVE', 'DREAM', 'PASSION', 'TRAINEE']
	} = $props<{
		selectedLabels: string[];
		options?: string[];
	}>();

	let isFilterOpen = $state(false);

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

<div class="relative flex-1 sm:flex-none">
	<button
		data-filter-toggle="true"
		class="flex w-full sm:w-auto h-[46px] sm:h-[50px] items-center justify-center gap-2 px-4 sm:px-5 rounded-full bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md border border-gray-100 dark:border-zinc-800 text-slate-700 dark:text-slate-200 font-bold text-[13px] sm:text-sm shadow-sm hover:bg-white dark:hover:bg-zinc-900 hover:border-red-200 hover:text-red-600 transition-all cursor-pointer group"
		onclick={() => (isFilterOpen = !isFilterOpen)}
	>
		<Filter
			class="w-4 sm:w-4.5 h-4 sm:h-4.5 text-gray-400 group-hover:text-red-500 transition-colors"
		/>
		{t('common.filter') || 'Filter'}
		{#if selectedLabels.length > 0}
			<span
				class="ml-1 w-4 h-4 rounded-full bg-red-500 text-white flex items-center justify-center text-[9px] leading-none"
			>
				{selectedLabels.length}
			</span>
		{/if}
	</button>

	{#if isFilterOpen}
		<div
			use:clickOutside
			transition:slide={{ duration: 200 }}
			class="absolute top-full left-0 md:left-auto md:right-0 mt-2 z-[7000]"
		>
			<div
				class="w-56 bg-white dark:bg-zinc-900 rounded-2xl shadow-xl border border-gray-100 dark:border-zinc-800 p-3"
			>
				<div class="flex items-center justify-between mb-2 px-1">
					<h3 class="text-xs font-bold text-gray-900 dark:text-white uppercase tracking-wider">
						{t('theater.events.filterBy') || 'Filter By'}
					</h3>
					{#if selectedLabels.length > 0}
						<button
							class="text-[10px] text-red-500 hover:text-red-600 font-bold uppercase tracking-wider cursor-pointer"
							onclick={() => (selectedLabels = [])}
						>
							{t('common.clear') || 'Clear'}
						</button>
					{/if}
				</div>
				<div class="flex flex-col gap-1 max-h-72 overflow-y-auto custom-scrollbar pr-1">
					{#each options as option}
						<button
							class="flex items-center justify-between w-full px-3 py-2 text-[11px] rounded-xl transition-colors cursor-pointer {selectedLabels.includes(
								option
							)
								? 'bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 font-black'
								: 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-zinc-800 font-bold'}"
							onclick={() => toggleLabel(option)}
						>
							<span>{t(`theater.events.labels.${option.toLowerCase()}`) || option}</span>
							{#if selectedLabels.includes(option)}
								<Check class="w-3.5 h-3.5" />
							{/if}
						</button>
					{/each}
				</div>
			</div>
		</div>
	{/if}
</div>
