<script lang="ts">
	import { onMount } from 'svelte';
	import { TrendingUp } from 'lucide-svelte';
	import { page } from '$app/stores';
	import { trendingTagsStore } from '$lib/stores/page48.svelte';
	import { getActiveMedia, tagUrl } from '$lib/utils/page48';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	// Cached in the store, so navigating between Page48 pages doesn't refetch.
	let tags = $derived(trendingTagsStore.data);
	let loading = $derived(trendingTagsStore.isLoading || !trendingTagsStore.isLoaded);
	// Keep the active media filter (Gambar/Video) when opening a tag.
	let activeMedia = $derived(getActiveMedia($page.url.pathname, $page.url.search));

	onMount(() => {
		void trendingTagsStore.load();
	});
</script>

<section
	class="rounded-2xl bg-white/80 dark:bg-zinc-900/80 border border-gray-200/70 dark:border-white/10 backdrop-blur-xl overflow-hidden"
>
	<div class="flex items-center gap-2 px-4 py-3 border-b border-gray-100 dark:border-white/5">
		<TrendingUp size={16} class="text-red-500" />
		<h2 class="font-bold text-[15px] text-gray-900 dark:text-gray-100">
			{t('page48.trending.title')}
		</h2>
	</div>

	{#if loading}
		<div class="p-4 space-y-3 animate-pulse">
			{#each Array(5) as _}
				<div class="flex items-center justify-between">
					<div class="h-4 bg-gray-200 dark:bg-zinc-800 rounded w-1/2"></div>
					<div class="h-3 bg-gray-200 dark:bg-zinc-800 rounded w-8"></div>
				</div>
			{/each}
		</div>
	{:else if tags.length === 0}
		<div class="p-5 text-center text-[13px] text-gray-400 dark:text-gray-500">
			{t('page48.trending.empty')}
		</div>
	{:else}
		<ul class="divide-y divide-gray-100 dark:divide-white/5">
			{#each tags as item (item.tag)}
				<li>
					<a
						href={tagUrl(item.tag, activeMedia)}
						class="flex items-center justify-between px-4 py-2.5 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer"
					>
						<span class="font-semibold text-[14px] text-red-500 truncate">#{item.tag}</span>
						<span class="text-[12px] text-gray-400 dark:text-gray-500 shrink-0 tabular-nums">
							{t('page48.trending.postCount', { count: item.count })}
						</span>
					</a>
				</li>
			{/each}
		</ul>
	{/if}
</section>
