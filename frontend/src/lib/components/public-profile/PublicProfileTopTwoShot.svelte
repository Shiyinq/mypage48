<script lang="ts">
	import { Camera } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { PublicProfileStats } from '$lib/types';

	interface Props {
		topTwoShots?: PublicProfileStats['topTwoShots'];
	}

	let { topTwoShots }: Props = $props();

	const { t } = useTranslation();

	function rankStyle(index: number): string {
		if (index === 0)
			return 'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/30 dark:text-yellow-500';
		if (index === 1) return 'bg-gray-200 text-gray-600 dark:bg-zinc-800 dark:text-gray-400';
		if (index === 2)
			return 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-500';
		return 'bg-pink-50 text-pink-500 dark:bg-pink-900/20';
	}
</script>

<div
	class="bg-white/90 dark:bg-zinc-900/90 backdrop-blur-xl border border-white/40 dark:border-white/10 rounded-3xl sm:rounded-[2rem] p-5 sm:p-6 flex flex-col h-full shadow-2xl shadow-pink-500/10 dark:shadow-pink-950/40 transition-all duration-300 hover:shadow-pink-500/15"
>
	<h3
		class="font-black text-[10px] sm:text-xs uppercase tracking-[0.2em] text-gray-400 mb-5 flex items-center gap-2"
	>
		<Camera class="w-4 h-4 text-pink-500" />
		{t('profile.publicActivity.topTwoShotMembers')}
	</h3>

	<div class="flex-1 overflow-y-auto pr-1 custom-scrollbar">
		{#if topTwoShots && topTwoShots.length > 0}
			<div class="space-y-3">
				{#each topTwoShots as twoshot, index}
					<div
						class="flex items-center gap-3 p-2.5 rounded-2xl bg-pink-50/40 dark:bg-pink-950/10 border border-pink-100/50 dark:border-pink-900/20"
					>
						<div
							class="flex-shrink-0 flex items-center justify-center w-7 h-7 rounded-full font-black text-xs {rankStyle(
								index
							)}"
						>
							{index + 1}
						</div>

						<div
							class="w-10 h-10 rounded-full overflow-hidden bg-gradient-to-br from-pink-50 to-pink-100 dark:from-pink-900/20 dark:to-zinc-800 flex-shrink-0 ring-2 ring-white dark:ring-zinc-800 shadow-sm"
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

						<div class="flex-1 min-w-0">
							<p
								class="text-sm font-bold text-gray-900 dark:text-gray-100 truncate leading-tight"
								title={twoshot.name}
							>
								{twoshot.name}
							</p>
							<div class="flex items-center gap-1 text-xs text-pink-500 font-bold mt-0.5">
								<Camera class="w-3 h-3" />
								{twoshot.count}x
							</div>
						</div>
					</div>
				{/each}
			</div>
		{:else}
			<div class="h-full flex flex-col items-center justify-center text-center text-gray-400 py-8">
				<div
					class="w-14 h-14 rounded-2xl bg-pink-50 dark:bg-pink-900/20 mb-3 flex items-center justify-center"
				>
					<Camera class="w-7 h-7 opacity-30 text-pink-500" />
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
