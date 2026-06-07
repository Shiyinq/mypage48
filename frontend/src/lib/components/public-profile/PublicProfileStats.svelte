<script lang="ts">
	import { Ticket, Camera, Armchair, Heart, TrendingUp } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { PublicProfileStats } from '$lib/types';

	interface Props {
		stats: PublicProfileStats;
		year?: number | null;
	}

	let { stats, year = null }: Props = $props();

	const { t } = useTranslation();
</script>

<div class="lg:col-span-2">
	<!-- Unified Summary Card -->
	<div
		class="relative overflow-hidden bg-white/90 dark:bg-zinc-900/90 backdrop-blur-xl border border-white/40 dark:border-white/10 rounded-3xl sm:rounded-[2rem] shadow-2xl shadow-red-500/10 dark:shadow-red-950/40 group hover:scale-[1.01] transition-all duration-300"
	>
		<!-- Background tickets decoration -->
		<div
			class="absolute -right-8 -bottom-8 opacity-[0.03] dark:opacity-[0.02] transform -rotate-12 pointer-events-none"
		>
			<Ticket class="w-64 h-64" />
		</div>

		<!-- TOP SECTION: HEADER & 3-COLUMN STATS -->
		<div class="p-6 sm:p-8">
			<!-- Card Header -->
			<div
				class="relative z-10 flex items-center justify-center gap-2 mb-8 text-red-500/80 dark:text-red-400/80"
			>
				<TrendingUp class="w-4 h-4" />
				<span
					class="text-[10px] font-black uppercase tracking-[0.3em] text-gray-500 dark:text-gray-400"
				>
					{#if year}
						{t('profile.publicActivity.yearSummary', { year })}
					{:else}
						{t('profile.publicActivity.summary')}
					{/if}
				</span>
			</div>

			<div class="relative z-10 grid grid-cols-3 gap-y-0 items-start sm:items-center">
				<!-- Total Shows -->
				<div
					class="col-span-1 flex flex-col items-center border-r border-gray-100 dark:border-white/5 pb-0 px-1 sm:px-4"
				>
					<div
						class="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-red-50 to-white dark:from-red-900/20 dark:to-zinc-800 shadow-sm text-red-500 flex items-center justify-center mb-3 sm:mb-4 group-hover:scale-110 transition-transform duration-300"
					>
						<Ticket class="w-4 h-4 sm:w-5 sm:h-5" />
					</div>
					<div class="text-center w-full">
						<div
							class="text-3xl sm:text-5xl lg:text-6xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-br from-red-600 to-red-400 leading-none mb-1.5 sm:mb-3 px-1"
						>
							{stats.totalShows}
						</div>
						<div
							class="text-[7px] xs:text-[8px] sm:text-[10px] font-bold text-gray-400 uppercase tracking-widest leading-tight"
						>
							{t('profile.stats.totalShows')}
						</div>
					</div>
				</div>

				<!-- Top Row -->
				<div
					class="col-span-1 flex flex-col items-center border-r border-gray-100 dark:border-white/5 px-1 sm:px-4"
				>
					<div
						class="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-purple-50 to-white dark:from-purple-900/20 dark:to-zinc-800 shadow-sm text-purple-500 flex items-center justify-center mb-3 sm:mb-4 group-hover:scale-110 transition-transform duration-300"
					>
						<Armchair class="w-4 h-4 sm:w-5 sm:h-5" />
					</div>
					<div class="text-center w-full px-1">
						<div class="flex items-baseline justify-center gap-0.5 sm:gap-1 mb-1.5 sm:mb-3 px-1">
							<div
								class="text-3xl sm:text-5xl lg:text-6xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-br from-purple-600 to-purple-400 leading-none"
							>
								{stats.topRow || '-'}
							</div>
							{#if stats.topRowCount}
								<div
									class="text-[7px] sm:text-[10px] font-bold text-purple-500 bg-purple-50 dark:bg-purple-900/20 px-1.5 py-0.5 rounded-full border border-purple-100 dark:border-purple-800/50"
								>
									{stats.topRowCount}x
								</div>
							{/if}
						</div>
						<div
							class="text-[7px] xs:text-[8px] sm:text-[10px] font-bold text-gray-400 uppercase tracking-widest text-center leading-tight"
						>
							{t('dashboard.theater.topRow')}
						</div>
					</div>
				</div>

				<!-- 2-Shot -->
				<div class="col-span-1 flex flex-col items-center px-1 sm:px-4">
					<div
						class="w-8 h-8 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-pink-50 to-white dark:from-pink-900/20 dark:to-zinc-800 shadow-sm text-pink-500 flex items-center justify-center mb-3 sm:mb-4 group-hover:scale-110 transition-transform duration-300"
					>
						<Camera class="w-4 h-4 sm:w-5 sm:h-5" />
					</div>
					<div class="text-center w-full px-1">
						<div
							class="text-3xl sm:text-5xl lg:text-6xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-br from-pink-600 to-pink-400 leading-none mb-1.5 sm:mb-3 px-1"
						>
							{stats.totalTwoShots}
						</div>
						<div
							class="text-[7px] xs:text-[8px] sm:text-[10px] font-bold text-gray-400 uppercase tracking-widest leading-tight"
						>
							{t('dashboard.twoShot.twoShotTitle')}
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- BOTTOM SECTION: TOP SHOW (Unified Row) -->
		<div class="relative z-10 border-t border-gray-100 dark:border-white/5 p-4 sm:p-6 group/bottom">
			<div class="flex items-center gap-4 sm:gap-6">
				<div
					class="w-12 h-12 sm:w-16 sm:h-16 rounded-2xl bg-gradient-to-br from-yellow-50 to-white dark:from-yellow-900/20 dark:to-zinc-800 shadow-sm flex-shrink-0 flex items-center justify-center"
				>
					<Heart class="w-6 h-6 sm:w-8 sm:h-8 text-yellow-500 fill-yellow-500 ml-0.5 mt-0.5" />
				</div>
				<div class="flex-1 min-w-0">
					<div
						class="text-[9px] sm:text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-0.5 sm:mb-1"
					>
						{t('dashboard.theater.topShow')}
					</div>
					<div
						class="font-black leading-none text-lg sm:text-xl lg:text-2xl mb-0.5 text-gray-900 dark:text-white"
						title={stats.topShow || 'No Data'}
					>
						{stats.topShow || '-'}
					</div>
					{#if stats.topShowCount}
						<div
							class="inline-flex items-center px-2 py-0.5 rounded-full bg-white dark:bg-zinc-800 text-[9px] sm:text-[10px] font-bold text-gray-500 dark:text-gray-400 border border-gray-100 dark:border-zinc-700"
						>
							{t('profile.publicActivity.watchedTimes', { count: stats.topShowCount })}
						</div>
					{/if}
				</div>
			</div>
		</div>
	</div>
</div>
