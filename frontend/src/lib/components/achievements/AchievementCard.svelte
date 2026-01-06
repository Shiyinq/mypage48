<script lang="ts">
	import type { AchievementItem } from '$lib/types';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { Lock, Check, Trophy } from 'lucide-svelte';
	import type { ComponentType } from 'svelte';

	export let achievement: AchievementItem;
	export let icon: ComponentType = Trophy;

	const { t } = useTranslation();
</script>

<div
	class={`relative border-2 rounded-3xl p-5 flex items-center gap-5 transition-all duration-300 h-full ${
		achievement.isUnlocked
			? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-400 dark:border-yellow-500/50 shadow-sm hover:shadow-md hover:scale-[1.01]'
			: 'bg-gray-50 dark:bg-zinc-900 border-gray-200 dark:border-zinc-700 opacity-70 grayscale'
	}`}
>
	<!-- Icon Box -->
	<div
		class={`w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0 ${
			achievement.isUnlocked
				? 'bg-white dark:bg-zinc-800 shadow-sm text-yellow-600'
				: 'bg-gray-200 dark:bg-zinc-700 text-gray-400'
		}`}
	>
		{#if achievement.isUnlocked}
			<svelte:component this={icon} class="w-8 h-8 fill-current" />
		{:else}
			<Lock class="w-6 h-6" />
		{/if}
	</div>

	<div class="flex-1">
		<h3 class={`text-lg font-bold ${achievement.isUnlocked ? 'text-themed' : 'text-themed-muted'}`}>
			{achievement.title}
		</h3>
		<p class="text-xs text-themed-secondary font-medium">{achievement.description}</p>

		<!-- Progress Bar for Locked Items -->
		{#if !achievement.isUnlocked && achievement.progress}
			<div class="mt-2">
				<div class="text-[10px] font-bold text-gray-400 mb-1 text-right">
					{achievement.progress}
				</div>
				<div class="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
					<div
						class="h-full bg-gray-400 rounded-full"
						style={`width: ${
							achievement.progress.includes('/')
								? (parseInt(achievement.progress.split('/')[0]) /
										parseInt(achievement.progress.split('/')[1].replace(/[^0-9]/g, ''))) *
									100
								: 0
						}%`}
					></div>
				</div>
			</div>
		{/if}
	</div>

	<!-- Status Badge -->
	{#if achievement.isUnlocked}
		<div
			class="absolute top-4 right-4 bg-yellow-400 text-yellow-900 text-[10px] font-bold px-3 py-1 rounded-full flex items-center gap-1 shadow-sm"
		>
			{$t('achievements.unlocked')}
			<Check class="w-3 h-3" />
		</div>
	{/if}
</div>
