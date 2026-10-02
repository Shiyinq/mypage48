<script lang="ts">
	import { onMount } from 'svelte';
	import { TrendingUp } from 'lucide-svelte';
	import { page48Api, type TrendingTag } from '$lib/api/page48';
	import { ErrorState } from '$lib/components';
	import { page48NavbarStore } from '$lib/stores/page48.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import Page48Sidebars from '$lib/components/page48/Page48Sidebars.svelte';
	import MemberXTags from '$lib/components/page48/MemberXTags.svelte';
	import SearchBox from '$lib/components/page48/SearchBox.svelte';

	const { t } = useTranslation();

	let tags = $state<TrendingTag[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	onMount(() => {
		page48NavbarStore.pageType = 'trending';
		load();
	});

	async function load() {
		try {
			loading = true;
			error = null;
			const response = await page48Api.getTrendingTags(50);
			tags = response.tags;
		} catch (err: unknown) {
			const e = err as { message?: string };
			error = e?.message || t('page48.trending.loadError');
		} finally {
			loading = false;
		}
	}
</script>

<SEO
	title={t('page48.seo.trendingTitle')}
	path="/page48/trending"
	description={t('page48.seo.trendingDesc')}
	keywords="Page48, JKT48, trending, hashtag JKT48"
/>

<div
	class="max-w-[620px] mx-auto w-full min-h-screen bg-white/70 dark:bg-zinc-950/70 backdrop-blur-3xl sm:border-x border-gray-200/60 dark:border-white/10 pb-24 shadow-sm shadow-black/5 dark:shadow-none transition-all"
>
	<div class="px-5 sm:px-6 pt-6 pb-4 border-b border-gray-100/60 dark:border-white/5">
		<!-- Search lives in the sidebar on desktop, so mobile gets it above the title. -->
		<div class="mb-4 xl:hidden">
			<SearchBox />
		</div>
		<div class="flex items-center gap-2">
			<TrendingUp size={22} class="text-red-500" />
			<h1 class="text-xl font-bold text-gray-900 dark:text-gray-100">
				{t('page48.trending.title')}
			</h1>
		</div>
		<p class="text-[13px] text-gray-500 dark:text-gray-400 mt-1">{t('page48.trending.subtitle')}</p>
	</div>

	{#if loading}
		<div class="p-4 space-y-3 animate-pulse">
			{#each Array(8) as _}
				<div class="flex items-center justify-between">
					<div class="h-4 bg-gray-200 dark:bg-zinc-800 rounded w-1/2"></div>
					<div class="h-3 bg-gray-200 dark:bg-zinc-800 rounded w-10"></div>
				</div>
			{/each}
		</div>
	{:else if error}
		<div class="p-6">
			<ErrorState title={t('page48.trending.loadError')} description={error} onRetry={load} />
		</div>
	{:else if tags.length === 0}
		<div class="p-12 text-center text-[13px] font-medium text-gray-400 dark:text-gray-500">
			{t('page48.trending.empty')}
		</div>
	{:else}
		<ul class="divide-y divide-gray-100 dark:divide-white/5">
			{#each tags as item, i (item.tag)}
				<li>
					<a
						href={`/page48/tag/${item.tag}`}
						class="flex items-center gap-3 px-5 sm:px-6 py-3 hover:bg-gray-50 dark:hover:bg-white/5 transition-colors cursor-pointer"
					>
						<span
							class="text-[13px] font-bold text-gray-300 dark:text-zinc-600 w-5 shrink-0 tabular-nums"
						>
							{i + 1}
						</span>
						<span class="flex-1 min-w-0">
							<span class="block font-semibold text-[15px] text-red-500 truncate">
								#{item.tag}
							</span>
							<span class="block text-[12px] text-gray-400 dark:text-gray-500">
								{t('page48.trending.postCount', { count: item.count })}
							</span>
						</span>
					</a>
				</li>
			{/each}
		</ul>
	{/if}

	<!-- Member hashtags sit below the trending list, since the mobile menu no longer
	     has its own entry. Desktop shows them in the left sidebar, hence xl:hidden. -->
	<div class="xl:hidden border-t border-gray-100/60 dark:border-white/5">
		<MemberXTags variant="inline" />
	</div>
</div>

<Page48Sidebars showTrending={false} />
