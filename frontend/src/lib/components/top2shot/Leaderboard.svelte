<script lang="ts">
	import { TrendingUp, Camera, User } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { TopTwoShotMember } from '$lib/types';

	export let ranking: TopTwoShotMember[] = [];
	export let totalCount: number = 0;
	export let topMemberCount: number = 1;

	const { t } = useTranslation();

	const formatCompact = (val: number) =>
		new Intl.NumberFormat('id-ID', {
			style: 'currency',
			currency: 'IDR',
			notation: 'compact'
		}).format(val);
</script>

<div
	class="bg-white dark:bg-zinc-800 rounded-3xl border border-gray-100 dark:border-zinc-700 shadow-sm overflow-hidden"
>
	<div
		class="p-6 border-b border-gray-100 dark:border-zinc-700 flex justify-between items-center bg-gray-50/50 dark:bg-zinc-800/50"
	>
		<div>
			<h3 class="font-bold text-gray-800 dark:text-gray-200 text-lg">
				{$t('top2shot.rankingTitle')}
			</h3>
			<p class="text-xs text-gray-500 dark:text-gray-400">
				{$t('top2shot.rankingSubtitle')}
			</p>
		</div>
		<div
			class="bg-pink-100 dark:bg-pink-900/30 text-pink-600 dark:text-pink-400 px-3 py-1 rounded-full text-xs font-bold flex items-center gap-1"
		>
			<TrendingUp class="w-3 h-3" />
			{totalCount}
			{$t('top2shot.totalPhotos')}
		</div>
	</div>

	<div class="divide-y divide-gray-50 dark:divide-zinc-700">
		{#each ranking as member, index}
			<div
				class="p-4 flex items-center gap-4 hover:bg-gray-50 dark:hover:bg-zinc-700/50 transition-colors group"
			>
				<!-- Rank Number -->
				<div
					class={`w-8 h-8 flex-shrink-0 flex items-center justify-center font-black text-sm rounded-full ${
						index === 0
							? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
							: index === 1
								? 'bg-gray-200 dark:bg-zinc-700 text-gray-600 dark:text-gray-300'
								: index === 2
									? 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400'
									: 'text-gray-400'
					}`}
				>
					{index + 1}
				</div>

				<!-- Avatar -->
				<div
					class="w-12 h-12 rounded-full bg-gray-100 dark:bg-zinc-700 flex-shrink-0 overflow-hidden border border-gray-100 dark:border-zinc-600"
				>
					{#if member.image}
						<img src={member.image} alt={member.name} class="w-full h-full object-cover" />
					{:else}
						<div
							class="w-full h-full flex items-center justify-center text-gray-300 dark:text-gray-500"
						>
							<User class="w-5 h-5" />
						</div>
					{/if}
				</div>

				<!-- Info -->
				<div class="flex-1 min-w-0">
					<h4 class="font-bold text-gray-800 dark:text-gray-200 truncate">{member.name}</h4>
					<div class="flex items-center gap-3 mt-0.5">
						<span
							class="text-xs text-gray-500 dark:text-gray-400 font-medium flex items-center gap-1"
						>
							<Camera class="w-3 h-3" />
							{member.count}
							{$t('top2shot.photos')}
						</span>
					</div>
				</div>

				<!-- Spend Bar Visual -->
				<div class="hidden sm:block w-24">
					<div class="text-[10px] text-gray-400 text-right font-bold mb-1">
						{formatCompact(member.spend)}
					</div>
					<div class="h-1.5 w-full bg-gray-100 dark:bg-zinc-700 rounded-full overflow-hidden">
						<div
							class="h-full bg-pink-500 rounded-full"
							style="width: {(member.count / topMemberCount) * 100}%"
						></div>
					</div>
				</div>
			</div>
		{/each}
	</div>
</div>
