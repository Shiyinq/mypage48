<script lang="ts">
	import type { SetlistDetailStats } from '$lib/apis/setlists';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { MapPin, DollarSign } from 'lucide-svelte';
	import { formatCurrency } from '$lib/utils/formatting';

	interface Props {
		stats: SetlistDetailStats;
	}

	let { stats }: Props = $props();

	const { t } = useTranslation();
</script>

<div class="grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4">
	<div
		class="bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 p-4 md:p-5 rounded-2xl hover:shadow-lg hover:shadow-purple-500/5 hover:-translate-y-1 transition-all duration-300 group"
	>
		<div class="flex items-start justify-between mb-3 md:mb-4">
			<div
				class="p-2 md:p-2.5 bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400 rounded-lg md:rounded-xl group-hover:scale-110 transition-transform"
			>
				<MapPin class="w-4 h-4 md:w-5 md:h-5" />
			</div>
			<span
				class="text-[10px] md:text-xs font-bold text-purple-600/50 dark:text-purple-400/50 uppercase tracking-wider"
			>
				{t('shows.topRow')}
			</span>
		</div>
		<div class="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white">
			{stats.topRow || '-'}
		</div>
		<div class="text-[11px] md:text-sm text-gray-500 dark:text-gray-400 mt-1 line-clamp-1">
			{t('shows.mostFrequentedRow') || 'Most frequented row'}
		</div>
	</div>

	<div
		class="bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 p-4 md:p-5 rounded-2xl hover:shadow-lg hover:shadow-green-500/5 hover:-translate-y-1 transition-all duration-300 group"
	>
		<div class="flex items-start justify-between mb-3 md:mb-4">
			<div
				class="p-2 md:p-2.5 bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 rounded-lg md:rounded-xl group-hover:scale-110 transition-transform"
			>
				<DollarSign class="w-4 h-4 md:w-5 md:h-5" />
			</div>
			<span
				class="text-[10px] md:text-xs font-bold text-green-600/50 dark:text-green-400/50 uppercase tracking-wider"
			>
				{t('dashboard.theater.totalExpenses')}
			</span>
		</div>
		<div class="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white truncate">
			{formatCurrency(stats.totalSpent)}
		</div>
		<div class="text-[11px] md:text-sm text-gray-500 dark:text-gray-400 mt-1 line-clamp-1">
			{t('shows.investmentInMemories') || 'Investment in memories'}
		</div>
	</div>
</div>
