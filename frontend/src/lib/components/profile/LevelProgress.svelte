<script lang="ts">
	import { Info, Sparkles } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Level {
		current: string;
		xp: number;
		nextLevelXp: number;
		nextRankTitle: string;
	}

	export let level: Level;
	export let progressPercent: number;
	export let loading: boolean = true;

	const { t } = useTranslation();
</script>

<div class="glass-panel p-6 rounded-3xl relative">
	<div class="flex justify-between items-end mb-2">
		<div>
			<div class="flex items-center gap-1.5 mb-0.5">
				<p class="text-xs font-bold text-gray-400 dark:text-gray-500 uppercase">
					{$t('profile.level.currentRank')}
				</p>
				<div class="relative group">
					<Info
						class="w-3.5 h-3.5 text-gray-300 cursor-help hover:text-red-400 transition-colors"
					/>
					<div
						class="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 px-2.5 py-1 bg-gray-800 text-white text-[10px] font-medium rounded-md shadow-lg opacity-0 group-hover:opacity-100 transition-all pointer-events-none whitespace-nowrap z-20"
					>
						1 XP = 1 Show
						<div
							class="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-4 border-transparent border-t-gray-800"
						></div>
					</div>
				</div>
			</div>
			{#if loading}
				<div class="h-8 w-32 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse mt-1"></div>
			{:else}
				<h3 class="text-2xl font-black idol-text-gradient">{level.current}</h3>
			{/if}
		</div>
		<div class="text-right">
			{#if loading}
				<div class="h-3 w-16 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse ml-auto"></div>
			{:else}
				<p class="text-xs font-bold text-gray-500 dark:text-gray-400">
					<span class="text-red-600">{level.xp}</span> / {level.nextLevelXp} XP
				</p>
			{/if}
		</div>
	</div>

	{#if loading}
		<div class="h-3 w-full bg-gray-200 dark:bg-zinc-700 rounded-full animate-pulse mb-4"></div>
		<div class="h-9 w-full bg-gray-200 dark:bg-zinc-700 rounded-lg animate-pulse"></div>
	{:else}
		<!-- Progress Bar -->
		<div
			class="h-3 w-full bg-gray-100 dark:bg-zinc-800 rounded-full overflow-hidden shadow-inner mb-4"
		>
			<div class="h-full idol-gradient rounded-full relative" style="width: {progressPercent}%">
				<div
					class="absolute inset-0 bg-[linear-gradient(45deg,rgba(255,255,255,0.2)_25%,transparent_25%,transparent_50%,rgba(255,255,255,0.2)_50%,rgba(255,255,255,0.2)_75%,transparent_75%,transparent)] bg-[length:1rem_1rem] animate-[pulse_1s_linear_infinite]"
				></div>
			</div>
		</div>

		<div
			class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 font-medium bg-gray-50 dark:bg-zinc-800 p-2 rounded-lg border border-gray-100 dark:border-zinc-700"
		>
			<Sparkles class="w-3.5 h-3.5 text-yellow-500" />
			<span>
				<span class="font-bold text-gray-700 dark:text-gray-200"
					>{level.nextLevelXp - level.xp} XP</span
				>
				{$t('profile.level.needed')}
				{$t('profile.level.for')}
				<span class="font-bold text-gray-700 dark:text-gray-200">{level.nextRankTitle}</span>
			</span>
		</div>
	{/if}
</div>
