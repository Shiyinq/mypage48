<script lang="ts">
	import { Star, Crown, ChevronRight } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { OptimizedImage } from '$lib/components/common';

	const { t } = useTranslation();

	interface Props {
		/**
		 * Top Show Card component for dashboard
		 */
		title: string;
		count: number;
		image: string | null;
		loading?: boolean;
	}

	let { title, count, image, loading = false }: Props = $props();
</script>

<div
	class="glass-card rounded-3xl relative overflow-hidden group hover:shadow-lg transition-all duration-300 flex flex-col h-full bg-purple-50/50 dark:bg-transparent border-purple-100 dark:border-purple-500/20"
>
	<div class="p-5 pb-0 flex justify-between items-start">
		<div class="flex items-center gap-2 text-purple-500">
			<div class="p-1.5 bg-purple-100 dark:bg-purple-800/40 rounded-lg">
				<Star class="w-4 h-4 fill-current" />
			</div>
			<span class="font-bold text-xs tracking-wider text-purple-500 dark:text-purple-400 uppercase"
				>{t('dashboard.theater.topShow')}</span
			>
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
				class="w-14 h-14 rounded-full p-0.5 bg-gradient-to-tr from-indigo-400 via-purple-500 to-fuchsia-500 flex-shrink-0"
			>
				<div
					class="w-full h-full rounded-full border-2 border-white dark:border-gray-800 overflow-hidden bg-white dark:bg-gray-800 flex items-center justify-center"
				>
					{#if image}
						<OptimizedImage src={image} alt={title} class="w-full h-full" />
					{:else}
						<Star class="w-6 h-6 text-purple-500 fill-purple-100" />
					{/if}
				</div>
			</div>
			<div class="min-w-0">
				<p class="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
					{t('dashboard.theater.mostWatched')}
				</p>
				<h3
					class={`font-black text-themed leading-none mb-0.5 truncate ${title.length > 15 ? 'text-sm' : 'text-lg'}`}
					{title}
				>
					{title}
				</h3>
				<p class="text-sm font-bold text-purple-500">
					{count}
					{t('shows.unit')}
				</p>
			</div>
		{/if}
	</div>
	{#if loading}
		<div
			class="mt-auto border-t border-purple-100 dark:border-purple-800/30 p-3 w-full flex justify-center"
		>
			<div class="h-4 w-24 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
		</div>
	{:else}
		<a
			href="/theater"
			class="mt-auto border-t border-purple-100 dark:border-purple-800/30 p-3 w-full text-center text-xs font-bold text-purple-600 dark:text-purple-400 hover:bg-purple-50 dark:hover:bg-purple-900/30 transition-colors flex items-center justify-center gap-1 relative z-20 cursor-pointer"
		>
			{t('common.viewDetails')}
			<ChevronRight class="w-3 h-3" />
		</a>
	{/if}
</div>
