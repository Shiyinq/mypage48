<script lang="ts">
	import { TrendingUp, Music, Zap } from 'lucide-svelte';
	import type { ProfileRecentActivity } from '$lib/types';
	import { useTranslation } from '$lib/i18n/useTranslation';

	export let recentActivity: ProfileRecentActivity[] = [];
	export let loading: boolean = true;

	const { t, locale } = useTranslation();

	$: formatActivityDate = (dateStr: string) => {
		const date = new Date(dateStr);
		const now = new Date();
		const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));
		const lang = $locale;

		if (diffDays === 0) return $t('time.relative.today');
		if (diffDays === 1) return $t('time.relative.yesterday');
		if (diffDays < 7) return $t('time.relative.daysAgo', { count: diffDays });
		if (diffDays < 30) return $t('time.relative.weeksAgo', { count: Math.floor(diffDays / 7) });

		const localeMap: Record<string, string> = { id: 'id-ID', ja: 'ja-JP', en: 'en-US' };
		return date.toLocaleDateString(localeMap[lang] || 'en-US', {
			month: 'short',
			day: 'numeric'
		});
	};
</script>

<div class="glass-panel p-6 rounded-3xl">
	<h4 class="font-bold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
		<TrendingUp class="w-4 h-4 text-red-500" />
		{$t('profile.recentActivity.title')}
	</h4>

	<div
		class="space-y-4 relative before:absolute before:left-[19px] before:top-2 before:bottom-2 before:w-0.5 before:bg-gray-100 before:dark:bg-zinc-800"
	>
		{#if loading}
			<!-- Skeleton Loading for Activity Items -->
			<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
			{#each [1, 2, 3] as _unused}
				<div class="flex gap-4 relative z-10">
					<div
						class="w-10 h-10 rounded-full flex-shrink-0 bg-gray-200 dark:bg-zinc-700 animate-pulse"
					></div>
					<div
						class="flex-1 bg-white/50 dark:bg-zinc-800/50 p-3 rounded-xl border border-gray-50 dark:border-zinc-700"
					>
						<div class="flex justify-between items-start mb-2">
							<div class="h-4 bg-gray-200 dark:bg-zinc-700 rounded w-2/3 animate-pulse"></div>
							<div class="h-3 bg-gray-200 dark:bg-zinc-700 rounded w-16 animate-pulse"></div>
						</div>
						<div class="h-3 bg-gray-200 dark:bg-zinc-700 rounded w-1/3 animate-pulse"></div>
					</div>
				</div>
			{/each}
		{:else if recentActivity.length === 0}
			<div class="text-center py-8 text-gray-500">
				<Music class="w-8 h-8 mx-auto mb-2 text-gray-300" />
				<p class="text-sm">{$t('profile.recentActivity.noActivity')}</p>
				<p class="text-xs text-gray-400">{$t('profile.recentActivity.startTracking')}</p>
			</div>
		{:else}
			{#each recentActivity as show}
				<div class="flex gap-4 relative z-10">
					<div
						class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 border-4 border-white dark:border-zinc-950 shadow-sm {show.hasTwoShot
							? 'bg-yellow-100 dark:bg-yellow-950 text-yellow-600 dark:text-yellow-400'
							: 'bg-red-100 dark:bg-red-950 text-red-600 dark:text-red-400'}"
					>
						{#if show.hasTwoShot}
							<Zap class="w-4 h-4" />
						{:else}
							<Music class="w-4 h-4" />
						{/if}
					</div>
					<div
						class="flex-1 bg-white/50 dark:bg-zinc-800/50 p-3 rounded-xl border border-gray-50 dark:border-zinc-700 hover:bg-white dark:hover:bg-zinc-800 transition-colors"
					>
						<div class="flex justify-between items-start">
							<p class="text-sm font-bold text-gray-800 dark:text-gray-200">
								{show.hasTwoShot
									? $t('profile.recentActivity.twoShotAt')
									: $t('profile.recentActivity.attended')} '{show.title}'
							</p>
							<span class="text-[10px] font-medium text-gray-400"
								>{formatActivityDate(show.date)}</span
							>
						</div>
						<p class="text-xs text-gray-500 mt-0.5">
							Row {show.section}-{show.number}
							{#if show.twoShotMember}
								• {show.twoShotMember}
							{/if}
						</p>
					</div>
				</div>
			{/each}
		{/if}
	</div>
</div>
