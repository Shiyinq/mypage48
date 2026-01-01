<script lang="ts">
	import { Calendar } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	export let recentActivity: any[];

	const { t } = useTranslation();
</script>

<div class="glass-panel p-6 rounded-3xl flex flex-col h-full">
	<h3 class="font-black text-xl tracking-tight text-gray-900 dark:text-white mb-6">
		{$t('profile.recentActivity.title')}
	</h3>

	<div class="flex-1 overflow-y-auto pr-2 custom-scrollbar">
		{#if recentActivity && recentActivity.length > 0}
			<div class="flex flex-col">
				{#each recentActivity as activity}
					<div class="flex items-stretch gap-4 group">
						<!-- Timeline Column -->
						<div class="flex-shrink-0 relative w-4 flex flex-col items-center">
							<!-- Line -->
							<div
								class="absolute top-2 bottom-0 w-0.5 bg-gray-300 dark:bg-zinc-700 -z-10 group-last:hidden"
							></div>

							<!-- Dot -->
							<div class="mt-1.5 relative z-10 bg-white dark:bg-gray-900 rounded-full">
								{#if activity.type === '2-Shot'}
									<div
										class="w-2.5 h-2.5 rounded-full bg-pink-500 ring-4 ring-pink-50 dark:ring-pink-900/20"
									></div>
								{:else}
									<div
										class="w-2.5 h-2.5 rounded-full bg-red-600 ring-4 ring-red-50 dark:ring-red-900/20"
									></div>
								{/if}
							</div>
						</div>

						<!-- Content Column -->
						<div
							class="flex-1 min-w-0 pb-6 border-b border-gray-100 dark:border-zinc-800/50 group-last:border-0 group-last:pb-0"
						>
							<p class="text-sm font-bold text-gray-900 dark:text-white line-clamp-1">
								{activity.title}
							</p>
							<p class="text-xs text-gray-400 font-medium mt-0.5">
								{new Date(activity.date).toLocaleDateString(undefined, {
									day: 'numeric',
									month: 'short',
									year: 'numeric'
								})}
							</p>
						</div>
					</div>
				{/each}
			</div>
		{:else}
			<div class="h-full flex flex-col items-center justify-center text-center text-gray-400 py-8">
				<Calendar class="w-8 h-8 mb-2 opacity-50" />
				<p class="text-xs">{$t('profile.recentActivity.noActivity')}</p>
			</div>
		{/if}
	</div>
</div>
