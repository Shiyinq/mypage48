<script lang="ts">
	import { Calendar, History, Clock } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { formatDate } from '$lib/i18n';
	import type { PublicRecentActivity } from '$lib/types';

	export let recentActivity: PublicRecentActivity[];

	const { t } = useTranslation();
</script>

<div
	class="bg-white/60 dark:bg-zinc-900/60 backdrop-blur-xl border border-white/40 dark:border-white/10 rounded-[2rem] p-6 flex flex-col h-full shadow-xl shadow-red-500/5"
>
	<h3
		class="font-black text-sm uppercase tracking-widest text-gray-400 mb-6 flex items-center gap-2"
	>
		<History class="w-4 h-4" />
		{$t('profile.recentActivity.title')}
	</h3>

	<div class="flex-1 overflow-y-auto pr-2 custom-scrollbar">
		{#if recentActivity && recentActivity.length > 0}
			<div class="space-y-6">
				{#each recentActivity as activity}
					<div class="flex gap-4 group">
						<!-- Timeline Column -->
						<div class="flex-shrink-0 relative flex flex-col items-center">
							<!-- Dot -->
							<div
								class="w-3 h-3 rounded-full mt-1.5 relative z-10
                {activity.type === '2-Shot'
									? 'bg-gradient-to-br from-pink-400 to-pink-600 shadow-md shadow-pink-500/30'
									: 'bg-gradient-to-br from-red-500 to-red-700 shadow-md shadow-red-500/30'}"
							></div>

							<!-- Line -->
							<div class="flex-1 w-[1px] bg-gray-200 dark:bg-zinc-800 my-1 group-last:hidden"></div>
						</div>

						<!-- Content Column -->
						<div class="flex-1 min-w-0 pb-1 group-last:pb-0">
							<p
								class="text-sm font-bold text-gray-900 dark:text-gray-100 line-clamp-1 leading-tight mb-1"
							>
								{activity.title}
							</p>
							<div class="flex items-center gap-1.5 text-xs text-gray-400 font-medium">
								<Clock class="w-3 h-3" />
								{$formatDate(activity.date, {
									day: 'numeric',
									month: 'short',
									year: 'numeric'
								})}
							</div>
						</div>
					</div>
				{/each}
			</div>
		{:else}
			<div class="h-full flex flex-col items-center justify-center text-center text-gray-400 py-8">
				<div
					class="w-16 h-16 rounded-2xl bg-gray-50 dark:bg-zinc-800/50 mb-4 flex items-center justify-center"
				>
					<Calendar class="w-8 h-8 opacity-30" />
				</div>
				<p class="text-xs font-bold uppercase tracking-wide opacity-50">
					{$t('profile.recentActivity.noActivity')}
				</p>
			</div>
		{/if}
	</div>
</div>

<style>
	.custom-scrollbar::-webkit-scrollbar {
		width: 4px;
	}
	.custom-scrollbar::-webkit-scrollbar-track {
		background: transparent;
	}
	.custom-scrollbar::-webkit-scrollbar-thumb {
		background: rgba(156, 163, 175, 0.2);
		border-radius: 4px;
	}
	.custom-scrollbar::-webkit-scrollbar-thumb:hover {
		background: rgba(156, 163, 175, 0.4);
	}
</style>
