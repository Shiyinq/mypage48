<script lang="ts">
	import { Ticket, Camera, Armchair, TrendingUp } from 'lucide-svelte';
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

		<!-- BOTTOM SECTION: TOP 2-SHOT -->
		<div class="relative z-10 border-t border-gray-100 dark:border-white/5 p-4 sm:p-5 group/bottom">
			<div class="flex items-center gap-2 mb-3">
				<Camera class="w-4 h-4 text-pink-500" />
				<h4 class="text-[10px] sm:text-xs font-black uppercase tracking-[0.2em] text-gray-400">
					{t('profile.publicActivity.topTwoShotMembers')}
				</h4>
			</div>

			<div class="flex flex-row items-center gap-3 overflow-x-auto pb-2 custom-scrollbar">
				{#if stats.topTwoShots && stats.topTwoShots.length > 0}
					{#each stats.topTwoShots as twoshot, index}
						<div
							class="flex-shrink-0 flex items-center gap-2 bg-white/50 dark:bg-zinc-800/50 rounded-full pr-4 p-1 border border-gray-100 dark:border-white/5 relative shadow-sm hover:shadow-md transition-shadow"
						>
							<!-- Ranking badge -->
							<div
								class="absolute -top-1.5 -left-1.5 w-5 h-5 rounded-full bg-white dark:bg-zinc-900 flex items-center justify-center shadow-sm z-10 text-[9px] font-black
								{index === 0
									? 'text-yellow-500 border border-yellow-200 dark:border-yellow-900/50'
									: index === 1
										? 'text-gray-400 border border-gray-200 dark:border-gray-700'
										: index === 2
											? 'text-orange-500 border border-orange-200 dark:border-orange-900/50'
											: 'text-gray-400 border border-gray-200 dark:border-gray-700'}"
							>
								{index + 1}
							</div>

							<!-- Image -->
							<div
								class="w-10 h-10 sm:w-12 sm:h-12 rounded-full overflow-hidden bg-gradient-to-br from-pink-50 to-pink-100 dark:from-pink-900/20 dark:to-zinc-800 flex-shrink-0 shadow-inner"
							>
								{#if twoshot.imageUrl}
									<img
										src={twoshot.imageUrl_small || twoshot.imageUrl}
										alt={twoshot.name}
										class="w-full h-full object-cover"
									/>
								{:else}
									<div
										class="w-full h-full flex items-center justify-center text-sm font-black text-pink-400/50"
									>
										{twoshot.name.charAt(0)}
									</div>
								{/if}
							</div>

							<!-- Info -->
							<div class="flex flex-col min-w-0 max-w-[90px] sm:max-w-[110px]">
								<span
									class="text-xs sm:text-sm font-bold text-gray-900 dark:text-white truncate"
									title={twoshot.name}
								>
									{twoshot.name}
								</span>
								<span class="text-[10px] font-black text-pink-500 flex items-center gap-1">
									<Camera class="w-3 h-3" />
									{twoshot.count}x
								</span>
							</div>
						</div>
					{/each}
				{:else}
					<div
						class="text-xs font-bold text-gray-400 uppercase tracking-widest opacity-50 px-2 py-4"
					>
						{t('profile.recentActivity.noActivity')}
					</div>
				{/if}
			</div>
		</div>
	</div>
</div>
