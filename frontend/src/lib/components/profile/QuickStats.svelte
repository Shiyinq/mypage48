<script lang="ts">
	import { Trophy, Star } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		totalShows: number;
		totalAchievements: number;
		loading?: boolean;
	}

	let { totalShows, totalAchievements, loading = true }: Props = $props();

	const { t } = useTranslation();
</script>

<div class="grid grid-cols-2 gap-4">
	<div class="glass-panel p-4 rounded-2xl flex flex-col items-center justify-center text-center">
		<div
			class="w-8 h-8 rounded-full bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 flex items-center justify-center mb-2"
		>
			<Trophy class="w-4 h-4" />
		</div>
		{#if loading}
			<span class="inline-block w-10 h-7 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></span>
		{:else}
			<span class="text-2xl font-black text-themed">{totalShows}</span>
		{/if}
		<span class="text-[10px] font-bold text-gray-400 uppercase"
			>{t('profile.stats.totalShows')}</span
		>
	</div>
	<div class="glass-panel p-4 rounded-2xl flex flex-col items-center justify-center text-center">
		<div
			class="w-8 h-8 rounded-full bg-yellow-50 dark:bg-yellow-900/20 text-yellow-600 dark:text-yellow-400 flex items-center justify-center mb-2"
		>
			<Star class="w-4 h-4" />
		</div>
		{#if loading}
			<span class="inline-block w-10 h-7 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></span>
		{:else}
			<span class="text-2xl font-black text-themed">{totalAchievements}</span>
		{/if}
		<span class="text-[10px] font-bold text-gray-400 uppercase"
			>{t('profile.stats.achievements')}</span
		>
	</div>
</div>
