<script lang="ts">
	import { Heart, Crown, ChevronRight, User } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { OptimizedImage } from '$lib/components/common';

	const { t } = useTranslation();

	interface Props {
		/**
		 * Top 2-Shot Card component for dashboard
		 */
		name: string | null;
		count: number;
		image: string | undefined;
		image_medium?: string | undefined;
		image_small?: string | undefined;
		blurHash?: string | null;
		loading?: boolean;
	}

	let {
		name,
		count,
		image,
		image_medium,
		image_small,
		blurHash,
		loading = false
	}: Props = $props();
</script>

<div
	class="glass-card rounded-3xl relative overflow-hidden group hover:shadow-lg transition-all duration-300 flex flex-col h-full bg-pink-50/50 dark:bg-transparent border-pink-100 dark:border-pink-500/20"
>
	<div class="p-5 pb-0 flex justify-between items-start">
		<div class="flex items-center gap-2 text-pink-500">
			<div class="flex items-center gap-2 mb-3">
				<Heart class="w-4 h-4 text-pink-500 fill-pink-500" />
				<span class="text-[10px] font-black tracking-widest text-pink-500 uppercase"
					>{t('dashboard.twoShot.topTwoShot')}</span
				>
			</div>
		</div>
		<Crown class="w-5 h-5 text-yellow-400 fill-current" />
	</div>
	<div class="p-5 flex items-center gap-4">
		{#if loading}
			<!-- Skeleton Loading -->
			<div
				class="w-14 h-14 rounded-full bg-gray-200 dark:bg-zinc-700 animate-pulse flex-shrink-0"
			></div>
			<div class="min-w-0 flex-1">
				<div class="h-2 w-16 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse mb-2"></div>
				<div class="h-5 w-28 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse mb-1"></div>
				<div class="h-3 w-12 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
			</div>
		{:else}
			<div
				class="w-14 h-14 rounded-full p-0.5 bg-gradient-to-tr from-pink-400 via-rose-500 to-red-500 flex-shrink-0"
			>
				<div
					class="w-full h-full rounded-full border-2 border-white dark:border-gray-800 overflow-hidden bg-white dark:bg-gray-800 flex items-center justify-center"
				>
					{#if image}
						<OptimizedImage
							src={image}
							srcMedium={image_medium}
							srcSmall={image_small}
							{blurHash}
							alt={name || ''}
							class="w-full h-full"
							sizes="56px"
						/>
					{:else}
						<User class="w-6 h-6 text-pink-500 fill-pink-100" />
					{/if}
				</div>
			</div>
			<div class="min-w-0">
				<p class="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-1">
					{t('dashboard.twoShot.mostCollected')}
				</p>
				<h3
					class={`font-black text-themed leading-none mb-0.5 truncate ${(name?.length ?? 0) > 15 ? 'text-sm' : 'text-lg'}`}
					title={name || '-'}
				>
					{name || '-'}
				</h3>
				<p class="text-sm font-bold text-pink-500">
					{count}
					{t('dashboard.twoShot.photos')}
				</p>
			</div>
		{/if}
	</div>
	{#if loading}
		<div
			class="mt-auto border-t border-pink-100 dark:border-pink-800/30 p-3 w-full flex justify-center"
		>
			<div class="h-4 w-24 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
		</div>
	{:else}
		<a
			href="/top-2shot"
			class="mt-auto border-t border-pink-100 dark:border-pink-800/30 p-3 w-full text-center text-xs font-bold text-pink-600 dark:text-pink-400 hover:bg-pink-50 dark:hover:bg-pink-900/30 transition-colors flex items-center justify-center gap-1 cursor-pointer"
		>
			{t('common.viewDetails')}
			<ChevronRight class="w-3 h-3" />
		</a>
	{/if}
</div>
