<script lang="ts">
	import type { SetlistDetailStats, WatchedStats } from '$lib/apis/setlists';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { formatDate } from '$lib/i18n';
	import { MapPin, Camera, DollarSign, Calendar, Clock, Trophy } from 'lucide-svelte';
	import { formatCurrency } from '$lib/utils/formatting';

	interface Props {
		stats: SetlistDetailStats;
		watched: WatchedStats;
	}

	let { stats, watched }: Props = $props();

	const { t } = useTranslation();
</script>

<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 md:gap-4">
	<!-- Top Row -->
	<div
		class="bg-white dark:bg-zinc-900 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800 hover:shadow-md hover:shadow-purple-500/5 hover:-translate-y-0.5 transition-all duration-300 group"
	>
		<div class="flex items-center gap-3.5">
			<div
				class="p-3 bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400 rounded-xl shrink-0 group-hover:scale-110 transition-transform"
			>
				<MapPin class="w-5 h-5 md:w-6 md:h-6" />
			</div>
			<div class="flex-1 min-w-0">
				<div class="flex flex-wrap items-baseline gap-1.5 md:gap-2 mb-0.5">
					<div
						class="text-xl md:text-2xl font-black text-gray-900 dark:text-white leading-none flex items-center gap-2"
					>
						{stats.topRow || '-'}
						{#if stats.topRow}
							<span
								class="text-[10px] md:text-xs font-semibold text-purple-600 dark:text-purple-400 bg-purple-100 dark:bg-purple-900/30 px-1.5 py-0.5 rounded-md"
							>
								{stats.topRowCount}x
							</span>
						{/if}
					</div>
				</div>
				<div
					class="text-[11px] md:text-xs text-gray-500 dark:text-gray-400 font-medium mt-1 truncate"
				>
					{t('shows.mostFrequentedRow') || 'Most frequented row'}
				</div>
			</div>
		</div>
	</div>

	<!-- Total 2-Shot -->
	<div
		class="bg-white dark:bg-zinc-900 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800 hover:shadow-md hover:shadow-pink-500/5 hover:-translate-y-0.5 transition-all duration-300 group"
	>
		<div class="flex items-center gap-3.5">
			<div
				class="p-3 bg-pink-50 dark:bg-pink-900/20 text-pink-600 dark:text-pink-400 rounded-xl shrink-0 group-hover:scale-110 transition-transform"
			>
				<Camera class="w-5 h-5 md:w-6 md:h-6" />
			</div>
			<div class="flex-1 min-w-0">
				<div class="flex flex-wrap items-baseline gap-1.5 md:gap-2 mb-0.5">
					<div class="text-xl md:text-2xl font-black text-gray-900 dark:text-white leading-none">
						{stats.total2Shot}
					</div>
				</div>
				<div
					class="text-[11px] md:text-xs text-gray-500 dark:text-gray-400 font-medium mt-1 truncate"
				>
					{t('theater.setlists.twoShotObtained')}
				</div>
			</div>
		</div>
	</div>

	<!-- Total Expense -->
	<div
		class="bg-white dark:bg-zinc-900 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800 hover:shadow-md hover:shadow-green-500/5 hover:-translate-y-0.5 transition-all duration-300 group"
	>
		<div class="flex items-center gap-3.5">
			<div
				class="p-3 bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 rounded-xl shrink-0 group-hover:scale-110 transition-transform"
			>
				<DollarSign class="w-5 h-5 md:w-6 md:h-6" />
			</div>
			<div class="flex-1 min-w-0">
				<div class="flex flex-wrap items-baseline gap-1.5 md:gap-2 mb-0.5">
					<div
						class="text-xl md:text-2xl font-black text-gray-900 dark:text-white leading-none break-all"
					>
						{formatCurrency(stats.totalSpent)}
					</div>
				</div>
				<div
					class="text-[11px] md:text-xs text-gray-500 dark:text-gray-400 font-medium mt-1 truncate"
				>
					{t('shows.investmentInMemories') || 'Investment in memories'}
				</div>
			</div>
		</div>
	</div>

	<!-- First Show -->
	<div
		class="bg-white dark:bg-zinc-900 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800 hover:shadow-md hover:shadow-emerald-500/5 hover:-translate-y-0.5 transition-all duration-300 group"
	>
		<div class="flex items-center gap-3.5">
			<div
				class="p-3 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 rounded-xl shrink-0 group-hover:scale-110 transition-transform"
			>
				<Calendar class="w-5 h-5 md:w-6 md:h-6" />
			</div>
			<div class="flex-1 min-w-0">
				<div
					class="text-[15px] sm:text-base md:text-lg font-black text-gray-900 dark:text-white leading-none mb-1.5 truncate"
				>
					{stats.firstDate
						? formatDate(stats.firstDate, { day: 'numeric', month: 'short', year: 'numeric' })
						: '-'}
					{#if stats.firstSeat}<span class="text-gray-500 dark:text-gray-400 font-bold ml-0.5"
							>{t('theater.setlists.seat')} {stats.firstSeat}</span
						>{/if}
				</div>
				<div
					class="text-[11px] md:text-xs text-gray-500 dark:text-gray-400 font-medium mt-0.5 truncate"
				>
					{t('theater.setlists.firstShow')}
				</div>
			</div>
		</div>
	</div>

	<!-- Latest Show -->
	<div
		class="bg-white dark:bg-zinc-900 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800 hover:shadow-md hover:shadow-blue-500/5 hover:-translate-y-0.5 transition-all duration-300 group"
	>
		<div class="flex items-center gap-3.5">
			<div
				class="p-3 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 rounded-xl shrink-0 group-hover:scale-110 transition-transform"
			>
				<Clock class="w-5 h-5 md:w-6 md:h-6" />
			</div>
			<div class="flex-1 min-w-0">
				<div
					class="text-[15px] sm:text-base md:text-lg font-black text-gray-900 dark:text-white leading-none mb-1.5 truncate"
				>
					{stats.lastDate
						? formatDate(stats.lastDate, { day: 'numeric', month: 'short', year: 'numeric' })
						: '-'}
					{#if stats.lastSeat}<span class="text-gray-500 dark:text-gray-400 font-bold ml-0.5"
							>{t('theater.setlists.seat')} {stats.lastSeat}</span
						>{/if}
				</div>
				<div
					class="text-[11px] md:text-xs text-gray-500 dark:text-gray-400 font-medium mt-0.5 truncate"
				>
					{t('theater.setlists.latestShow')}
				</div>
			</div>
		</div>
	</div>

	<!-- Attendance Rate -->
	<div
		class="bg-white dark:bg-zinc-900 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800 hover:shadow-md hover:shadow-yellow-500/5 hover:-translate-y-0.5 transition-all duration-300 group"
	>
		<div class="flex items-center gap-3.5">
			<div
				class="p-3 bg-yellow-50 dark:bg-yellow-900/20 text-yellow-600 dark:text-yellow-400 rounded-xl shrink-0 group-hover:scale-110 transition-transform"
			>
				<Trophy class="w-5 h-5 md:w-6 md:h-6" />
			</div>
			<div class="flex-1 min-w-0">
				<div class="text-xl md:text-2xl font-black text-gray-900 dark:text-white leading-none mb-1">
					{watched.percentage}%
				</div>
				<div
					class="text-[11px] md:text-xs text-gray-500 dark:text-gray-400 font-medium mt-0.5 truncate"
				>
					{t('theater.setlists.attendanceRate')}
					{t('theater.setlists.ofMax')}
				</div>
			</div>
		</div>
	</div>
</div>
