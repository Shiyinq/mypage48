<script lang="ts">
	import { LayoutDashboard, Filter } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	/**
	 * Dashboard header component when filter panel is closed
	 */
	export let filterLabel: string;
	export let onOpenFilter: () => void;
</script>

<div class="flex items-center justify-between animate-fade-in">
	<div class="flex items-center gap-3">
		<div
			class="p-3 rounded-2xl bg-red-50 dark:bg-red-500/20 text-red-600 dark:text-red-400 shadow-lg shadow-red-100 dark:shadow-red-900/30 border-2 border-white dark:border-gray-800 transform -rotate-6"
		>
			<LayoutDashboard class="w-6 h-6" />
		</div>
		<div>
			<h2 class="text-2xl font-bold text-themed leading-none relative w-fit">
				{$t('dashboard.title')}
				<span
					class="absolute -bottom-1 left-0 w-full h-2 bg-red-200/60 dark:bg-red-500/30 -z-10 transform -skew-x-12 rounded-sm"
				></span>
			</h2>
			<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">{$t('dashboard.subtitle')}</p>
		</div>
	</div>
	<div class="flex items-center gap-2">
		<span
			class="text-xs font-bold text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-zinc-900 px-3 py-1.5 rounded-full border border-gray-200 dark:border-zinc-700"
		>
			{filterLabel}
		</span>
		<button
			on:click={onOpenFilter}
			class="flex items-center gap-2 px-4 py-2 rounded-full bg-white dark:bg-zinc-900 text-gray-600 dark:text-gray-300 font-bold text-xs shadow-sm border border-gray-200 dark:border-zinc-700 hover:border-red-200 dark:hover:border-red-500/50 hover:text-red-600 dark:hover:text-red-400 transition-all cursor-pointer"
		>
			<Filter class="w-4 h-4" />
			<span class="hidden sm:inline">{$t('common.filters')}</span>
		</button>
	</div>
</div>
