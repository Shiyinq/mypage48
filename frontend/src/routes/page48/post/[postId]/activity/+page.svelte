<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { fade } from 'svelte/transition';
	import { ArrowLeft } from 'lucide-svelte';
	import { page48Api, type PostActivityResponse } from '$lib/api/page48';
	import PostActivityList from '$lib/components/page48/PostActivityList.svelte';
	import PostActivityRowsSkeleton from '$lib/components/page48/PostActivityRowsSkeleton.svelte';
	import ErrorState from '$lib/components/ErrorState.svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { page48NavbarStore } from '$lib/stores/page48.svelte';
	import { activityNavStore } from '$lib/stores/page48Nav.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	type ActivityTab = 'quotes' | 'reposts' | 'likes';

	const { t } = useTranslation();

	let postId = $derived($page.params.postId ?? '');

	let activity = $state<PostActivityResponse | null>(null);
	let loading = $state(true);
	let failed = $state(false);

	onMount(() => {
		page48NavbarStore.pageType = 'post-detail';
	});

	$effect(() => {
		const id = postId;
		if (!id) return;
		void load(id);
	});

	async function load(id: string) {
		loading = true;
		failed = false;
		try {
			activity = await page48Api.getPostActivity(id);
		} catch {
			activity = null;
			failed = true;
		} finally {
			loading = false;
		}
	}

	// The Likes tab only exists for the author, so a direct ?tab=likes link opened
	// by anyone else falls back to Quotes.
	let activeTab = $derived.by<ActivityTab>(() => {
		const raw = $page.url.searchParams.get('tab');
		const wanted: ActivityTab = raw === 'reposts' || raw === 'likes' ? raw : 'quotes';
		if (wanted === 'likes' && !activity?.canViewLikes) return 'quotes';
		return wanted;
	});

	let tabs = $derived.by(() => {
		if (!activity) return [] as { key: ActivityTab; label: string; count: number }[];
		const items: { key: ActivityTab; label: string; count: number }[] = [
			{ key: 'quotes', label: t('page48.activity.quotes'), count: activity.quoteCount },
			{ key: 'reposts', label: t('page48.activity.reposts'), count: activity.repostCount }
		];
		if (activity.canViewLikes) {
			items.push({ key: 'likes', label: t('page48.activity.likes'), count: activity.likeCount });
		}
		return items;
	});

	function selectTab(key: ActivityTab) {
		if (key === activeTab) return;
		const url =
			key === 'quotes'
				? `/page48/post/${postId}/activity`
				: `/page48/post/${postId}/activity?tab=${key}`;
		void goto(url, { keepFocus: true, noScroll: true });
	}

	// Opened from a post list: go back so that list is restored as it was. Opened
	// from the post page (or a direct link): there is nothing to return to, so
	// fall back to the post itself.
	function goBack() {
		if (activityNavStore.fromList && typeof window !== 'undefined' && window.history.length > 1) {
			window.history.back();
			return;
		}
		void goto(`/page48/post/${postId}`);
	}
</script>

<SEO
	title={t('page48.activity.title')}
	path={`/page48/post/${postId}/activity`}
	description={t('page48.seo.postDesc')}
/>

<div
	class="max-w-[620px] mx-auto w-full min-h-screen bg-white/70 dark:bg-zinc-950/70 backdrop-blur-3xl sm:border-x border-gray-200/60 dark:border-white/10 pb-24 shadow-sm shadow-black/5 dark:shadow-none transition-all"
>
	{#if loading}
		<div class="flex flex-col">
			<div class="flex animate-pulse flex-col">
				<!-- Header: back button + title -->
				<div class="flex items-center gap-3 px-5 pb-1 pt-5 sm:px-6">
					<div
						class="h-[30px] w-[30px] shrink-0 rounded-full bg-gray-200/80 dark:bg-zinc-800"
					></div>
					<div class="h-5 w-32 rounded bg-gray-200 dark:bg-zinc-800"></div>
				</div>

				<!-- Tabs: equal-width segments, like the real tab bar -->
				<div class="flex border-b border-gray-200/60 dark:border-white/10">
					{#each [0, 1] as _}
						<div class="flex flex-1 justify-center px-2 py-3">
							<div class="h-4 w-16 rounded bg-gray-200 dark:bg-zinc-800"></div>
						</div>
					{/each}
				</div>
			</div>

			<PostActivityRowsSkeleton kind={activeTab === 'quotes' ? 'posts' : 'users'} />
		</div>
	{:else if failed || !activity}
		<div class="p-6">
			<ErrorState
				title={t('page48.activity.loadError')}
				description={t('page48.activity.loadErrorText')}
				onRetry={() => load(postId)}
			/>
		</div>
	{:else}
		<div class="flex flex-col" in:fade={{ duration: 250 }}>
			<!-- Header -->
			<div class="flex items-center gap-3 px-5 pb-1 pt-5 sm:px-6">
				<button
					class="-ml-1.5 cursor-pointer rounded-full p-1.5 text-gray-600 transition-colors hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-zinc-800"
					onclick={goBack}
					aria-label={t('page48.activity.backToPost')}
					title={t('page48.activity.backToPost')}
				>
					<ArrowLeft size={18} />
				</button>
				<h1 class="text-[16px] font-bold text-gray-900 dark:text-gray-100">
					{t('page48.activity.title')}
				</h1>
			</div>

			<!-- Tabs -->
			<div class="flex border-b border-gray-200/60 dark:border-white/10" role="tablist">
				{#each tabs as tab (tab.key)}
					<button
						role="tab"
						aria-selected={activeTab === tab.key}
						onclick={() => selectTab(tab.key)}
						class={`-mb-px flex-1 cursor-pointer whitespace-nowrap border-b-2 px-2 py-3 text-[14px] font-semibold transition-colors ${
							activeTab === tab.key
								? 'border-red-600 text-red-600 dark:border-red-400 dark:text-red-400'
								: 'border-transparent text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200'
						}`}
					>
						{tab.label}
						<span class="ml-1 tabular-nums text-gray-400 dark:text-gray-500">{tab.count}</span>
					</button>
				{/each}
			</div>

			<PostActivityList {postId} tab={activeTab} />
		</div>
	{/if}
</div>
