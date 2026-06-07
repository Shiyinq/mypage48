<script lang="ts">
	import { Calendar, ListMusic, Eye } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		showCounts?: Record<string, number>;
	}

	let { showCounts }: Props = $props();

	const { t } = useTranslation();

	// Convert Record to sorted Array, take top 5
	let topSetlists = $derived(
		Object.entries(showCounts || {})
			.sort((a, b) => b[1] - a[1])
			.slice(0, 5)
			.map(([title, count]) => ({ title, count }))
	);
</script>

<div
	class="bg-white/90 dark:bg-zinc-900/90 backdrop-blur-xl border border-white/40 dark:border-white/10 rounded-3xl sm:rounded-[2rem] p-5 sm:p-6 flex flex-col h-full shadow-2xl shadow-red-500/10 dark:shadow-red-950/40 transition-all duration-300 hover:shadow-red-500/15"
>
	<h3
		class="font-black text-sm uppercase tracking-widest text-gray-400 mb-6 flex items-center gap-2"
	>
		<ListMusic class="w-4 h-4" />
		{t('profile.publicActivity.topSetlists')}
	</h3>

	<div class="flex-1 overflow-y-auto pr-2 custom-scrollbar">
		{#if topSetlists && topSetlists.length > 0}
			<div class="space-y-4 sm:space-y-6">
				{#each topSetlists as setlist, index}
					<div class="flex gap-4 items-center group">
						<!-- Rank Column -->
						<div
							class="flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full font-black text-sm {index ===
							0
								? 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-500'
								: index === 1
									? 'bg-gray-200 text-gray-600 dark:bg-zinc-800 dark:text-gray-400'
									: index === 2
										? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-500'
										: 'bg-red-50 text-red-500 dark:bg-red-900/20'}"
						>
							{index + 1}
						</div>

						<!-- Content Column -->
						<div class="flex-1 min-w-0">
							<p
								class="text-sm font-bold text-gray-900 dark:text-gray-100 break-words leading-tight mb-1"
							>
								{setlist.title}
							</p>
							<div class="flex items-center gap-1.5 text-xs text-gray-400 font-medium">
								<Eye class="w-3 h-3" />
								{t('profile.publicActivity.watchedTimes', { count: setlist.count })}
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
					{t('profile.recentActivity.noActivity')}
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
