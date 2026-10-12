<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { fade } from 'svelte/transition';
	import { Hash, Search } from 'lucide-svelte';
	import {
		type Page48Post,
		type Page48SearchTab,
		type Page48SearchTopResponse,
		type PostUserItem,
		type TrendingTag
	} from '$lib/api/page48';
	import PostCard from '$lib/components/page48/PostCard.svelte';
	import UserListItem from '$lib/components/page48/UserListItem.svelte';
	import Page48Spinner from '$lib/components/page48/Page48Spinner.svelte';
	import Page48Sidebars from '$lib/components/page48/Page48Sidebars.svelte';
	import { SEARCH_FIELD_CLASS, SEARCH_FIELD_ICON_CLASS } from '$lib/components/page48/searchField';
	import ErrorState from '$lib/components/ErrorState.svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { isAuthenticated } from '$lib/stores/authStatus.svelte';
	import { page48NavbarStore, page48Reads } from '$lib/stores/page48.svelte';
	import { sharePost, tagUrl, togglePostInteraction } from '$lib/utils/page48';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	const PAGE_SIZE = 20;
	const MIN_QUERY_LENGTH = 2;
	const TABS: Page48SearchTab[] = ['top', 'posts', 'media', 'users', 'tags'];

	onMount(() => {
		page48NavbarStore.pageType = 'search';
		// Search is signed-in only; a direct visit sends the visitor to log in first.
		if (!isAuthenticated.value) void goto('/login');
	});

	let query = $derived($page.url.searchParams.get('query') ?? '');
	let activeTab = $derived.by<Page48SearchTab>(() => {
		const raw = $page.url.searchParams.get('tab');
		return (TABS as string[]).includes(raw ?? '') ? (raw as Page48SearchTab) : 'posts';
	});

	let isListTab = $derived(activeTab === 'posts' || activeTab === 'media');
	let ready = $derived(query.trim().length >= MIN_QUERY_LENGTH);

	let term = $state('');
	let loading = $state(false);
	let loadingMore = $state(false);
	let failed = $state(false);

	let posts = $state<Page48Post[]>([]);
	let cursor = $state<string | null>(null);
	let hasMore = $state(false);

	let top = $state<Page48SearchTopResponse | null>(null);
	let people = $state<PostUserItem[]>([]);
	let tags = $state<TrendingTag[]>([]);

	// The input mirrors the URL, so a history navigation restores it too.
	$effect(() => {
		term = query;
	});

	// Everything is driven by the URL, so a shared link opens the same results.
	$effect(() => {
		void query;
		void activeTab;
		void load();
	});

	async function load() {
		if (!ready) {
			posts = [];
			cursor = null;
			hasMore = false;
			top = null;
			people = [];
			tags = [];
			return;
		}

		loading = true;
		failed = false;
		try {
			if (isListTab) {
				await loadPosts(true);
			} else if (activeTab === 'top') {
				top = await page48Reads.searchTop(query);
			} else if (activeTab === 'users') {
				people = (await page48Reads.searchUsers(query)).data;
			} else {
				tags = (await page48Reads.searchTags(query)).tags;
			}
		} catch {
			failed = true;
		} finally {
			loading = false;
			loadingMore = false;
		}
	}

	async function loadPosts(reset: boolean) {
		const response = await page48Reads.searchPosts(
			query,
			activeTab === 'media' ? 'media' : 'posts',
			PAGE_SIZE,
			reset ? null : cursor
		);
		posts = reset ? response.data : [...posts, ...response.data];
		cursor = response.meta.nextCursor;
		hasMore = response.meta.hasMore;
	}

	function loadMore() {
		if (!isListTab || loading || loadingMore || !hasMore) return;
		loadingMore = true;
		void loadPosts(false).finally(() => {
			loadingMore = false;
		});
	}

	function handleScroll() {
		const scrollY = window.scrollY;
		const innerHeight = window.innerHeight;
		const offsetHeight = document.body.offsetHeight;

		if (scrollY + innerHeight >= offsetHeight - 500) {
			loadMore();
		}
	}

	function submit(event: SubmitEvent) {
		event.preventDefault();
		const value = term.trim();
		if (value.length < MIN_QUERY_LENGTH) return;
		void openSearch(value, 'posts');
	}

	function openSearch(value: string, tab: Page48SearchTab) {
		return goto(`/page48/search?query=${encodeURIComponent(value)}&tab=${tab}`, {
			keepFocus: true,
			noScroll: true
		});
	}

	function findPost(postId: string): Page48Post | undefined {
		return (
			posts.find((post) => post.postId === postId) ??
			top?.posts.find((post) => post.postId === postId)
		);
	}

	async function handleLike(postId: string) {
		const post = findPost(postId);
		if (post) await togglePostInteraction(post, 'like');
	}

	async function handleRepost(postId: string) {
		const post = findPost(postId);
		if (post) await togglePostInteraction(post, 'repost');
	}

	async function handleBookmark(postId: string) {
		const post = findPost(postId);
		if (post) await togglePostInteraction(post, 'bookmark');
	}

	function handleComment(post: Page48Post) {
		void goto(`/page48/post/${post.postId}`);
	}

	function handleShare(post: Page48Post) {
		void sharePost(post);
	}

	let isEmpty = $derived(
		isListTab
			? posts.length === 0
			: activeTab === 'top'
				? !top || (top.users.length === 0 && top.tags.length === 0 && top.posts.length === 0)
				: activeTab === 'users'
					? people.length === 0
					: tags.length === 0
	);
</script>

<svelte:window onscroll={handleScroll} />

<SEO
	title={t('page48.search.title')}
	path="/page48/search"
	description={t('page48.search.description')}
/>

<div
	class="relative max-w-[620px] mx-auto w-full min-h-screen bg-white/70 dark:bg-zinc-950/70 backdrop-blur-3xl sm:border-x border-gray-200/60 dark:border-white/10 pb-24 shadow-sm shadow-black/5 dark:shadow-none transition-all"
>
	<div class="px-5 sm:px-6 pt-6 pb-4">
		<form onsubmit={submit} role="search">
			<div class="relative">
				<Search size={16} class={SEARCH_FIELD_ICON_CLASS} />
				<input
					bind:value={term}
					type="text"
					enterkeyhint="search"
					placeholder={t('page48.search.placeholder')}
					aria-label={t('page48.search.placeholder')}
					class={SEARCH_FIELD_CLASS}
				/>
			</div>
		</form>
		<p class="mt-2 text-[12px] text-gray-400 dark:text-gray-500">{t('page48.search.hint')}</p>
	</div>

	<div class="flex border-b border-gray-200/60 dark:border-white/10" role="tablist">
		{#each TABS as tab (tab)}
			<button
				role="tab"
				aria-selected={activeTab === tab}
				onclick={() => ready && openSearch(query, tab)}
				class={`-mb-px flex-1 cursor-pointer whitespace-nowrap border-b-2 px-1.5 py-3 text-[12px] font-semibold transition-colors sm:px-2 sm:text-[13px] ${
					activeTab === tab
						? 'border-red-600 text-red-600 dark:border-red-400 dark:text-red-400'
						: 'border-transparent text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200'
				}`}
			>
				{t(`page48.search.tab.${tab}`)}
			</button>
		{/each}
	</div>

	{#if !ready}
		<div class="p-12 text-center text-[13px] text-gray-400 dark:text-gray-500">
			{t('page48.search.prompt')}
		</div>
	{:else if loading}
		<div class="divide-y divide-gray-100 dark:divide-white/5">
			{#each Array(5) as _}
				<div class="flex animate-pulse gap-3 p-5">
					<div class="h-10 w-10 shrink-0 rounded-full bg-gray-200/80 dark:bg-zinc-800"></div>
					<div class="flex-1 space-y-2">
						<div class="h-4 w-1/3 rounded bg-gray-200 dark:bg-zinc-800"></div>
						<div class="h-3.5 w-2/3 rounded bg-gray-200 dark:bg-zinc-800"></div>
					</div>
				</div>
			{/each}
		</div>
	{:else if failed}
		<div class="p-6">
			<ErrorState
				title={t('page48.search.loadError')}
				description={t('page48.search.loadErrorText')}
				onRetry={load}
			/>
		</div>
	{:else if isEmpty}
		<div class="p-12 text-center text-[13px] text-gray-400 dark:text-gray-500">
			{t('page48.search.empty')}
		</div>
	{:else if activeTab === 'top'}
		<div class="flex flex-col" in:fade={{ duration: 200 }}>
			{#if top && top.users.length > 0}
				<section>
					<h2
						class="px-5 pt-4 pb-1 text-[12px] font-bold uppercase tracking-wide text-gray-400 sm:px-6"
					>
						{t('page48.search.section.users')}
					</h2>
					{#each top.users as user (user.userId)}
						<UserListItem {user} showFollow />
					{/each}
				</section>
			{/if}

			{#if top && top.tags.length > 0}
				<section>
					<h2
						class="px-5 pt-4 pb-1 text-[12px] font-bold uppercase tracking-wide text-gray-400 sm:px-6"
					>
						{t('page48.search.section.tags')}
					</h2>
					{#each top.tags as tag (tag.tag)}
						<a
							href={tagUrl(tag.tag)}
							class="flex items-center justify-between px-5 py-2.5 transition-colors hover:bg-gray-50 sm:px-6 dark:hover:bg-white/5"
						>
							<span
								class="flex min-w-0 items-center gap-2 text-[14px] font-medium text-gray-900 dark:text-gray-100"
							>
								<Hash size={15} class="shrink-0 text-gray-400" />
								<span class="truncate">{tag.tag}</span>
							</span>
							<span class="shrink-0 text-[12px] tabular-nums text-gray-400">{tag.count}</span>
						</a>
					{/each}
				</section>
			{/if}

			{#if top && top.posts.length > 0}
				<section>
					<h2
						class="px-5 pt-4 pb-1 text-[12px] font-bold uppercase tracking-wide text-gray-400 sm:px-6"
					>
						{t('page48.search.section.posts')}
					</h2>
					<div class="divide-y divide-gray-100 dark:divide-white/5">
						{#each top.posts as post (post.postId)}
							<PostCard
								{post}
								onLike={handleLike}
								onRepost={handleRepost}
								onBookmark={handleBookmark}
								onComment={handleComment}
								onShare={handleShare}
							/>
						{/each}
					</div>
				</section>
			{/if}
		</div>
	{:else if isListTab}
		<div class="flex flex-col" in:fade={{ duration: 200 }}>
			<div class="divide-y divide-gray-100 dark:divide-white/5">
				{#each posts as post (post.postId)}
					<PostCard
						{post}
						onLike={handleLike}
						onRepost={handleRepost}
						onBookmark={handleBookmark}
						onComment={handleComment}
						onShare={handleShare}
					/>
				{/each}
			</div>

			{#if loadingMore}
				<div class="p-4 flex justify-center">
					<Page48Spinner />
				</div>
			{/if}
		</div>
	{:else if activeTab === 'users'}
		<div class="flex flex-col divide-y divide-gray-100 dark:divide-white/5">
			{#each people as user (user.userId)}
				<UserListItem {user} showFollow />
			{/each}
		</div>
	{:else}
		<ul class="divide-y divide-gray-100 dark:divide-white/5">
			{#each tags as tag (tag.tag)}
				<li>
					<a
						href={tagUrl(tag.tag)}
						class="flex items-center justify-between px-5 py-3 transition-colors hover:bg-gray-50 sm:px-6 dark:hover:bg-white/5"
					>
						<span
							class="flex min-w-0 items-center gap-2 text-[14px] font-medium text-gray-900 dark:text-gray-100"
						>
							<Hash size={15} class="shrink-0 text-gray-400" />
							<span class="truncate">{tag.tag}</span>
						</span>
						<span class="shrink-0 text-[12px] tabular-nums text-gray-400">{tag.count}</span>
					</a>
				</li>
			{/each}
		</ul>
	{/if}
</div>

<Page48Sidebars showTrending={false} showSearch={false} />
