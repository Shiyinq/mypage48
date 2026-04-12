<script lang="ts">
	import { Ticket, Camera, Armchair, Heart, TrendingUp } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { PublicProfileStats } from '$lib/types';

	export let stats: PublicProfileStats;
	export let year: number | null = null;

	const { t } = useTranslation();

	// Default to current year if not provided
	$: displayYear = year || new Date().getFullYear();
</script>

<div class="lg:col-span-2 grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-2 gap-4">
	<!-- Total Shows - Large Card -->
	<div
		class="col-span-2 relative overflow-hidden bg-white/60 dark:bg-zinc-900/60 backdrop-blur-xl border border-white/40 dark:border-white/10 rounded-3xl sm:rounded-[2rem] p-5 sm:p-6 shadow-xl shadow-red-500/5 group hover:scale-[1.01] transition-transform duration-300"
	>
		<div class="relative z-10 flex flex-col h-full justify-between gap-6">
			<div class="flex items-center gap-2 text-red-500/80 dark:text-red-400/80">
				<div class="p-2 rounded-full bg-red-50 dark:bg-red-900/10">
					<TrendingUp class="w-4 h-4" />
				</div>
				<span class="text-sm font-bold uppercase tracking-widest"
					>{$t('profile.publicActivity.yearSummary', { year: displayYear })}</span
				>
			</div>
			<div class="flex items-end justify-between">
				<div>
					<div
						class="text-6xl sm:text-8xl font-black tracking-tighter mb-1 text-transparent bg-clip-text bg-gradient-to-br from-red-600 to-purple-600 dark:from-red-400 dark:to-purple-400 leading-none"
					>
						{stats.totalShows}
					</div>
					<div class="font-bold text-gray-400 text-sm uppercase tracking-widest ml-1">
						{$t('profile.stats.totalShows')}
					</div>
				</div>
				<div class="opacity-10 dark:opacity-[0.05] transform rotate-12 mb-2 mr-2">
					<Ticket class="w-24 h-24" />
				</div>
			</div>
		</div>
	</div>

	<!-- 2-Shot Count -->
	<div
		class="col-span-1 bg-white/60 dark:bg-zinc-900/60 backdrop-blur-xl border border-white/40 dark:border-white/10 rounded-3xl sm:rounded-[2rem] p-5 sm:p-6 flex flex-col justify-center items-center text-center gap-4 relative overflow-hidden group hover:bg-white/70 dark:hover:bg-zinc-900/70 transition-colors shadow-lg shadow-pink-500/5"
	>
		<div
			class="w-12 h-12 rounded-2xl bg-gradient-to-br from-pink-50 to-white dark:from-pink-900/20 dark:to-zinc-800 shadow-sm text-pink-500 flex items-center justify-center group-hover:scale-110 transition-transform duration-300"
		>
			<Camera class="w-6 h-6" />
		</div>
		<div>
			<span class="text-4xl font-black text-gray-900 dark:text-white block leading-none mb-2">
				{stats.totalTwoShots}
			</span>
			<span class="text-xs font-bold text-gray-400 uppercase tracking-widest block">
				{$t('dashboard.twoShot.twoShotTitle')}
			</span>
		</div>
	</div>

	<!-- Top Row -->
	<div
		class="col-span-1 bg-white/60 dark:bg-zinc-900/60 backdrop-blur-xl border border-white/40 dark:border-white/10 rounded-3xl sm:rounded-[2rem] p-5 sm:p-6 flex flex-col justify-center items-center text-center gap-4 relative overflow-hidden group hover:bg-white/70 dark:hover:bg-zinc-900/70 transition-colors shadow-lg shadow-purple-500/5"
	>
		<div
			class="w-12 h-12 rounded-2xl bg-gradient-to-br from-purple-50 to-white dark:from-purple-900/20 dark:to-zinc-800 shadow-sm text-purple-500 flex items-center justify-center group-hover:scale-110 transition-transform duration-300"
		>
			<Armchair class="w-6 h-6" />
		</div>
		<div>
			<span class="text-4xl font-black text-gray-900 dark:text-white block leading-none mb-2">
				{stats.topRow || '-'}
			</span>
			<span class="text-xs font-bold text-gray-400 uppercase tracking-widest block">
				{$t('dashboard.theater.topRow')}
			</span>
		</div>
	</div>

	<!-- Top Show - Wide Card -->
	<div
		class="col-span-2 bg-white/60 dark:bg-zinc-900/60 backdrop-blur-xl border border-white/40 dark:border-white/10 rounded-3xl sm:rounded-[2rem] p-5 sm:p-6 text-gray-900 dark:text-white shadow-lg shadow-yellow-500/5 relative overflow-hidden group hover:scale-[1.01] transition-transform duration-300"
	>
		<div class="relative z-10 flex items-center gap-6">
			<div
				class="w-16 h-16 rounded-2xl bg-gradient-to-br from-yellow-50 to-white dark:from-yellow-900/20 dark:to-zinc-800 shadow-sm flex-shrink-0 flex items-center justify-center"
			>
				<Heart class="w-8 h-8 text-yellow-500 fill-yellow-500 ml-0.5 mt-0.5" />
			</div>
			<div class="flex-1 min-w-0">
				<div class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-1">
					{$t('dashboard.theater.topShow')}
				</div>
				<div
					class="font-black leading-tight text-xl sm:text-2xl line-clamp-2 md:truncate mb-1"
					title={stats.topShow || 'No Data'}
				>
					{stats.topShow || '-'}
				</div>
				{#if stats.topShowCount}
					<div
						class="inline-flex items-center px-2 py-0.5 rounded-full bg-gray-100 dark:bg-zinc-800 text-xs font-bold text-gray-500 dark:text-gray-400"
					>
						{$t('profile.publicActivity.watchedTimes', { count: stats.topShowCount })}
					</div>
				{/if}
			</div>
		</div>
	</div>
</div>
