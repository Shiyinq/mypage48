<script lang="ts">
	import { Calendar, History, DollarSign, Armchair } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { Ticket } from '$lib/types';

	interface ShowStats {
		first: Ticket;
		last: Ticket;
		avgPrice: number;
		topRow: string;
		totalSpent: number;
	}

	export let stats: ShowStats;

	const { t } = useTranslation();
</script>

<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
	<!-- First Seen -->
	<div
		class="glass-panel p-4 rounded-2xl flex items-center gap-4 border-l-4 border-l-blue-400 dark:border-l-blue-500"
	>
		<div class="p-2 bg-blue-50 dark:bg-blue-900/30 text-blue-500 dark:text-blue-400 rounded-lg">
			<Calendar class="w-5 h-5" />
		</div>
		<div>
			<p class="text-[10px] text-gray-400 dark:text-gray-500 font-bold uppercase tracking-wider">
				{$t('shows.firstAttended')}
			</p>
			<p class="font-bold text-gray-800 dark:text-gray-200 text-sm">
				{new Date(stats.first.event.date).toLocaleDateString('id-ID', {
					day: 'numeric',
					month: 'short',
					year: '2-digit'
				})}
			</p>
		</div>
	</div>

	<!-- Last Seen -->
	<div
		class="glass-panel p-4 rounded-2xl flex items-center gap-4 border-l-4 border-l-purple-400 dark:border-l-purple-500"
	>
		<div
			class="p-2 bg-purple-50 dark:bg-purple-900/30 text-purple-500 dark:text-purple-400 rounded-lg"
		>
			<History class="w-5 h-5" />
		</div>
		<div>
			<p class="text-[10px] text-gray-400 dark:text-gray-500 font-bold uppercase tracking-wider">
				{$t('shows.lastAttended')}
			</p>
			<p class="font-bold text-gray-800 dark:text-gray-200 text-sm">
				{new Date(stats.last.event.date).toLocaleDateString('id-ID', {
					day: 'numeric',
					month: 'short',
					year: '2-digit'
				})}
			</p>
		</div>
	</div>

	<!-- Avg Price -->
	<div
		class="glass-panel p-4 rounded-2xl flex items-center gap-4 border-l-4 border-l-emerald-400 dark:border-l-emerald-500"
	>
		<div
			class="p-2 bg-emerald-50 dark:bg-emerald-900/30 text-emerald-500 dark:text-emerald-400 rounded-lg"
		>
			<DollarSign class="w-5 h-5" />
		</div>
		<div>
			<p class="text-[10px] text-gray-400 dark:text-gray-500 font-bold uppercase tracking-wider">
				{$t('shows.avgPrice')}
			</p>
			<p class="font-bold text-gray-800 dark:text-gray-200 text-sm">
				{new Intl.NumberFormat('id-ID', {
					style: 'currency',
					currency: 'IDR',
					maximumFractionDigits: 0,
					notation: 'compact'
				}).format(stats.avgPrice)}
			</p>
		</div>
	</div>

	<!-- Top Row -->
	<div
		class="glass-panel p-4 rounded-2xl flex items-center gap-4 border-l-4 border-l-orange-400 dark:border-l-orange-500"
	>
		<div
			class="p-2 bg-orange-50 dark:bg-orange-900/30 text-orange-500 dark:text-orange-400 rounded-lg"
		>
			<Armchair class="w-5 h-5" />
		</div>
		<div>
			<p class="text-[10px] text-gray-400 dark:text-gray-500 font-bold uppercase tracking-wider">
				{$t('shows.topRow')}
			</p>
			<p class="font-bold text-gray-800 dark:text-gray-200 text-sm">
				{$t('shows.row')}
				{stats.topRow}
			</p>
		</div>
	</div>
</div>
