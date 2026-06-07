<script lang="ts">
	import { Ticket, Camera, Armchair, TrendingUp, ListMusic } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { PublicProfileStats } from '$lib/types';

	interface Props {
		stats: PublicProfileStats;
		year?: number | null;
	}

	let { stats, year = null }: Props = $props();

	const { t } = useTranslation();
</script>

<div
	class="bg-white/90 dark:bg-zinc-900/90 backdrop-blur-xl border border-white/40 dark:border-white/10 rounded-3xl sm:rounded-[2rem] p-5 sm:p-6 flex flex-col h-full shadow-2xl shadow-red-500/10 dark:shadow-red-950/40 transition-all duration-300 hover:shadow-red-500/15"
>
	<h3
		class="font-black text-[10px] sm:text-xs uppercase tracking-[0.2em] text-gray-400 mb-5 flex items-center gap-2"
	>
		<TrendingUp class="w-4 h-4 text-red-500" />
		{#if year}
			{t('profile.publicActivity.yearSummary', { year })}
		{:else}
			{t('profile.publicActivity.summary')}
		{/if}
	</h3>

	<div class="flex-1 flex flex-col gap-3">
		<!-- Total Shows -->
		<div
			class="flex items-center gap-3 p-3 rounded-2xl bg-red-50/60 dark:bg-red-950/20 border border-red-100/60 dark:border-red-900/20"
		>
			<div
				class="w-10 h-10 rounded-xl bg-gradient-to-br from-red-100 to-white dark:from-red-900/30 dark:to-zinc-800 text-red-500 flex items-center justify-center flex-shrink-0 shadow-sm"
			>
				<Ticket class="w-5 h-5" />
			</div>
			<div class="min-w-0 flex-1">
				<div
					class="text-2xl sm:text-3xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-br from-red-600 to-red-400 leading-none"
				>
					{stats.totalShows}
				</div>
				<div
					class="text-[9px] sm:text-[10px] font-bold text-gray-400 uppercase tracking-widest mt-1"
				>
					{t('profile.stats.totalShows')}
				</div>
			</div>
		</div>

		<!-- Top Row -->
		<div
			class="flex items-center gap-3 p-3 rounded-2xl bg-purple-50/60 dark:bg-purple-950/20 border border-purple-100/60 dark:border-purple-900/20"
		>
			<div
				class="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-100 to-white dark:from-purple-900/30 dark:to-zinc-800 text-purple-500 flex items-center justify-center flex-shrink-0 shadow-sm"
			>
				<Armchair class="w-5 h-5" />
			</div>
			<div class="min-w-0 flex-1">
				<div class="flex items-baseline gap-1.5">
					<div
						class="text-2xl sm:text-3xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-br from-purple-600 to-purple-400 leading-none"
					>
						{stats.topRow || '-'}
					</div>
					{#if stats.topRowCount}
						<span
							class="text-[9px] font-bold text-purple-500 bg-purple-100 dark:bg-purple-900/30 px-1.5 py-0.5 rounded-full border border-purple-200 dark:border-purple-800/50"
						>
							{stats.topRowCount}x
						</span>
					{/if}
				</div>
				<div
					class="text-[9px] sm:text-[10px] font-bold text-gray-400 uppercase tracking-widest mt-1"
				>
					{t('dashboard.theater.topRow')}
				</div>
			</div>
		</div>

		<!-- 2-Shot Total -->
		<div
			class="flex items-center gap-3 p-3 rounded-2xl bg-pink-50/60 dark:bg-pink-950/20 border border-pink-100/60 dark:border-pink-900/20"
		>
			<div
				class="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-100 to-white dark:from-pink-900/30 dark:to-zinc-800 text-pink-500 flex items-center justify-center flex-shrink-0 shadow-sm"
			>
				<Camera class="w-5 h-5" />
			</div>
			<div class="min-w-0 flex-1">
				<div
					class="text-2xl sm:text-3xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-br from-pink-600 to-pink-400 leading-none"
				>
					{stats.totalTwoShots}
				</div>
				<div
					class="text-[9px] sm:text-[10px] font-bold text-gray-400 uppercase tracking-widest mt-1"
				>
					{t('dashboard.twoShot.twoShotTitle')}
				</div>
			</div>
		</div>

		<!-- Top Setlist -->
		<div
			class="flex items-center gap-3 p-3 rounded-2xl bg-amber-50/60 dark:bg-amber-950/20 border border-amber-100/60 dark:border-amber-900/20"
		>
			<div
				class="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-100 to-white dark:from-amber-900/30 dark:to-zinc-800 text-amber-600 dark:text-amber-500 flex items-center justify-center flex-shrink-0 shadow-sm"
			>
				<ListMusic class="w-5 h-5" />
			</div>
			<div class="min-w-0 flex-1">
				<div class="flex items-baseline gap-1.5">
					<div
						class="text-sm sm:text-base font-black tracking-tight text-transparent bg-clip-text bg-gradient-to-br from-amber-700 to-amber-500 leading-tight truncate"
						title={stats.topShow || undefined}
					>
						{stats.topShow || '-'}
					</div>
					{#if stats.topShowCount}
						<span
							class="flex-shrink-0 text-[9px] font-bold text-amber-600 dark:text-amber-500 bg-amber-100 dark:bg-amber-900/30 px-1.5 py-0.5 rounded-full border border-amber-200 dark:border-amber-800/50"
						>
							{stats.topShowCount}x
						</span>
					{/if}
				</div>
				<div
					class="text-[9px] sm:text-[10px] font-bold text-gray-400 uppercase tracking-widest mt-1"
				>
					{t('dashboard.theater.topShow')}
				</div>
			</div>
		</div>
	</div>
</div>
