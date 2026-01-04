<script lang="ts">
	import { Ticket, Camera, Armchair, Heart } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { PublicProfileStats } from '$lib/types';

	export let stats: PublicProfileStats;

	const { t } = useTranslation();
</script>

<div class="lg:col-span-2 grid grid-cols-2 gap-4">
	<!-- Show Count -->
	<div
		class="glass-panel p-5 rounded-3xl flex flex-col items-center justify-center text-center gap-2"
	>
		<div
			class="w-10 h-10 rounded-2xl bg-red-50 dark:bg-red-900/20 text-red-500 flex items-center justify-center mb-1"
		>
			<Ticket class="w-5 h-5" />
		</div>
		<span class="text-5xl font-black text-gray-900 dark:text-white">{stats.totalShows}</span>
		<span class="text-xs font-bold text-gray-400 uppercase tracking-wider"
			>{$t('profile.stats.totalShows')}</span
		>
	</div>

	<!-- 2-Shot Count -->
	<div
		class="glass-panel p-5 rounded-3xl flex flex-col items-center justify-center text-center gap-2"
	>
		<div
			class="w-10 h-10 rounded-2xl bg-pink-50 dark:bg-pink-900/20 text-pink-500 flex items-center justify-center mb-1"
		>
			<Camera class="w-5 h-5" />
		</div>
		<span class="text-5xl font-black text-gray-900 dark:text-white">{stats.totalTwoShots}</span>
		<span class="text-xs font-bold text-gray-400 uppercase tracking-wider"
			>{$t('dashboard.twoShot.twoShotTitle')}</span
		>
	</div>

	<!-- Top Row -->
	<div
		class="glass-panel p-5 rounded-3xl flex flex-col items-center justify-center text-center gap-2"
	>
		<div
			class="w-10 h-10 rounded-2xl bg-purple-50 dark:bg-purple-900/20 text-purple-500 flex items-center justify-center mb-1"
		>
			<Armchair class="w-5 h-5" />
		</div>
		<span class="text-5xl font-black text-gray-900 dark:text-white">{stats.topRow || '-'}</span>
		{#if stats.topRowCount}
			<span class="text-lg font-extrabold text-gray-500 dark:text-gray-400 mt-1">
				{stats.topRowCount}
				{$t('dashboard.theater.times')}
			</span>
		{/if}
		<span class="text-xs font-bold text-gray-400 uppercase tracking-wider"
			>{$t('dashboard.theater.topRow')}</span
		>
	</div>

	<!-- Top Show -->
	<div
		class="glass-panel p-5 rounded-3xl flex flex-col items-center justify-center text-center gap-2"
	>
		<div
			class="w-10 h-10 rounded-2xl bg-yellow-50 dark:bg-yellow-900/20 text-yellow-500 flex items-center justify-center mb-1"
		>
			<Heart class="w-5 h-5" />
		</div>
		<span
			class="font-black text-gray-900 dark:text-white line-clamp-2 leading-tight px-2 {(
				stats.topShow || ''
			).length > 25
				? 'text-sm'
				: (stats.topShow || '').length > 15
					? 'text-lg'
					: 'text-2xl sm:text-3xl'}">{stats.topShow || '-'}</span
		>
		{#if stats.topShowCount}
			<span class="text-lg font-extrabold text-gray-500 dark:text-gray-400 mt-2">
				{stats.topShowCount}
				{$t('dashboard.theater.times')}
			</span>
		{/if}
		<span class="text-xs font-bold text-gray-400 uppercase tracking-wider"
			>{$t('dashboard.theater.topShow')}</span
		>
	</div>
</div>
