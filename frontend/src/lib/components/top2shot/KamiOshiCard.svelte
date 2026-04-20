<script lang="ts">
	import { Crown, User } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { OptimizedImage } from '$lib/components/common';
	import type { TopTwoShotMember } from '$lib/types';

	interface Props {
		member: TopTwoShotMember;
	}

	let { member }: Props = $props();

	const { t } = useTranslation();

	const formatCompact = (val: number) =>
		new Intl.NumberFormat('id-ID', {
			style: 'currency',
			currency: 'IDR',
			notation: 'compact'
		}).format(val);
</script>

<div class="relative group">
	<div
		class="relative overflow-hidden bg-white dark:bg-zinc-800 rounded-3xl shadow-sm border border-gray-100 dark:border-zinc-700 p-8 transition-all duration-300 hover:shadow-xl"
	>
		<!-- Decorative Header Background -->
		<div
			class="absolute top-0 left-0 w-full h-32 bg-gradient-to-b from-pink-50/80 to-transparent dark:from-pink-900/10 dark:to-transparent -z-0"
		></div>

		<div class="relative z-10 flex flex-col items-center text-center">
			<div
				class="bg-gradient-to-r from-amber-100 to-amber-200 dark:from-amber-900/40 dark:to-amber-800/40 text-amber-700 dark:text-amber-400 text-[10px] font-black tracking-widest px-4 py-1.5 rounded-full mb-6 shadow-sm flex items-center gap-1.5 border border-amber-200/50 dark:border-amber-700/30"
			>
				<Crown class="w-3.5 h-3.5 fill-current" />
				{t('top2shot.mostCollected')}
			</div>

			<div class="relative mb-6 group-hover:scale-105 transition-transform duration-500">
				<div
					class="w-36 h-36 rounded-full p-1.5 bg-white dark:bg-zinc-800 shadow-xl ring-1 ring-gray-100 dark:ring-zinc-700 relative z-10"
				>
					<div
						class="w-full h-full rounded-full overflow-hidden bg-gray-100 dark:bg-zinc-700 relative"
					>
						{#if member.image}
							<OptimizedImage
								src={member.image}
								srcMedium={member.image_medium}
								srcSmall={member.image_small}
								alt={member.name}
								sizes="144px"
								class="w-full h-full object-cover"
							/>
						{:else}
							<div
								class="w-full h-full flex items-center justify-center text-gray-300 dark:text-gray-600"
							>
								<User class="w-16 h-16" />
							</div>
						{/if}
					</div>
				</div>
				<!-- Rank Badge -->
				<div
					class="absolute bottom-1 right-1 bg-yellow-400 text-yellow-900 w-10 h-10 flex items-center justify-center rounded-full font-black border-4 border-white dark:border-zinc-800 shadow-lg text-lg z-20"
				>
					#1
				</div>
			</div>

			<h3 class="text-2xl font-black text-gray-900 dark:text-white mb-1">
				{member.name}
			</h3>
			<p
				class="text-pink-500 font-bold text-sm mb-8 bg-pink-50 dark:bg-pink-900/20 px-3 py-1 rounded-lg"
			>
				{t('top2shot.cherished')}
			</p>

			<div class="grid grid-cols-2 gap-4 w-full">
				<div
					class="bg-gray-50 dark:bg-zinc-700/30 rounded-2xl p-4 border border-gray-100 dark:border-zinc-700/50"
				>
					<div class="text-xs text-gray-500 dark:text-gray-400 uppercase font-bold mb-1">
						{t('top2shot.stats2shots')}
					</div>
					<div class="text-2xl font-black text-gray-800 dark:text-gray-100">
						{member.count}x
					</div>
				</div>
				<div
					class="bg-gray-50 dark:bg-zinc-700/30 rounded-2xl p-4 border border-gray-100 dark:border-zinc-700/50"
				>
					<div class="text-xs text-gray-500 dark:text-gray-400 uppercase font-bold mb-1">
						{t('top2shot.statsSpent')}
					</div>
					<div class="text-lg font-black text-gray-800 dark:text-gray-100 mt-1">
						{formatCompact(member.spend)}
					</div>
				</div>
			</div>
		</div>
	</div>
</div>
