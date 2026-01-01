<script lang="ts">
	import { Lock, Check } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { Milestone } from '$lib/utils/achievements';

	export let milestone: Milestone;

	const { t } = useTranslation();
</script>

<div
	class={`relative border-2 rounded-3xl p-5 flex items-center gap-5 transition-all duration-300 h-full ${
		milestone.isUnlocked
			? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-400 dark:border-yellow-500/50 shadow-sm hover:shadow-md hover:scale-[1.01]'
			: 'bg-gray-50 dark:bg-zinc-900 border-gray-200 dark:border-zinc-700 opacity-70 grayscale'
	}`}
>
	<!-- Icon Box -->
	<div
		class={`w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0 ${
			milestone.isUnlocked
				? 'bg-white dark:bg-zinc-800 shadow-sm text-yellow-600'
				: 'bg-gray-200 dark:bg-zinc-700 text-gray-400'
		}`}
	>
		{#if milestone.isUnlocked}
			<svelte:component this={milestone.icon} class="w-8 h-8 fill-current" />
		{:else}
			<Lock class="w-6 h-6" />
		{/if}
	</div>

	<div class="flex-1">
		<h3 class={`text-lg font-bold ${milestone.isUnlocked ? 'text-themed' : 'text-themed-muted'}`}>
			{milestone.title}
		</h3>
		<p class="text-xs text-themed-secondary font-medium">{milestone.description}</p>

		<!-- Progress Bar for Locked Items -->
		{#if !milestone.isUnlocked && milestone.progress}
			<div class="mt-2">
				<div class="text-[10px] font-bold text-gray-400 mb-1 text-right">{milestone.progress}</div>
				<div class="w-full h-1.5 bg-gray-200 rounded-full overflow-hidden">
					<div
						class="h-full bg-gray-400 rounded-full"
						style={`width: ${
							milestone.progress.includes('/')
								? (parseInt(milestone.progress.split('/')[0]) /
										parseInt(milestone.progress.split('/')[1])) *
									100
								: 0
						}%`}
					></div>
				</div>
			</div>
		{/if}
	</div>

	<!-- Status Badge -->
	{#if milestone.isUnlocked}
		<div
			class="absolute top-4 right-4 bg-yellow-400 text-yellow-900 text-[10px] font-bold px-3 py-1 rounded-full flex items-center gap-1 shadow-sm"
		>
			{$t('achievements.unlocked')}
			<Check class="w-3 h-3" />
		</div>
	{/if}
</div>
