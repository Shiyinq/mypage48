<script lang="ts">
	import { goto } from '$app/navigation';
	import { fade } from 'svelte/transition';
	import { page48Api, type Page48Post, type PostUserItem } from '$lib/api/page48';
	import PostCard from '$lib/components/page48/PostCard.svelte';
	import Page48Spinner from '$lib/components/page48/Page48Spinner.svelte';
	import PostActivityRowsSkeleton from '$lib/components/page48/PostActivityRowsSkeleton.svelte';
	import UserListItem from '$lib/components/page48/UserListItem.svelte';
	import { sharePost, togglePostInteraction } from '$lib/utils/page48';
	import { useTranslation } from '$lib/i18n/useTranslation';

	type ActivityTab = 'quotes' | 'reposts' | 'likes';

	interface Props {
		postId: string;
		tab: ActivityTab;
	}

	let { postId, tab }: Props = $props();

	const { t } = useTranslation();

	const PAGE_SIZE = 20;

	let posts = $state<Page48Post[]>([]);
	let users = $state<PostUserItem[]>([]);
	let loading = $state(true);
	let loadingMore = $state(false);
	let failed = $state(false);
	let hasMore = $state(false);
	let nextCursor = $state<string | null>(null);

	/** Bumped on every post/tab change so stale responses are ignored. */
	let token = 0;

	interface ListPage {
		posts: Page48Post[];
		users: PostUserItem[];
		hasMore: boolean;
		nextCursor: string | null;
	}

	async function fetchPage(
		id: string,
		which: ActivityTab,
		cursor: string | null
	): Promise<ListPage> {
		if (which === 'quotes') {
			const res = await page48Api.getPostQuotes(id, PAGE_SIZE, cursor);
			return {
				posts: res.data,
				users: [],
				hasMore: res.meta.hasMore,
				nextCursor: res.meta.nextCursor
			};
		}
		const res =
			which === 'reposts'
				? await page48Api.getPostReposts(id, PAGE_SIZE, cursor)
				: await page48Api.getPostLikes(id, PAGE_SIZE, cursor);
		return {
			posts: [],
			users: res.data,
			hasMore: res.meta.hasMore,
			nextCursor: res.meta.nextCursor
		};
	}

	$effect(() => {
		const id = postId;
		const which = tab;
		const mine = ++token;

		loading = true;
		failed = false;
		void (async () => {
			try {
				const page = await fetchPage(id, which, null);
				if (mine !== token) return;
				posts = page.posts;
				users = page.users;
				hasMore = page.hasMore;
				nextCursor = page.nextCursor;
			} catch {
				if (mine !== token) return;
				posts = [];
				users = [];
				hasMore = false;
				nextCursor = null;
				failed = true;
			} finally {
				if (mine === token) loading = false;
			}
		})();
	});

	async function loadMore() {
		if (!hasMore || loadingMore || !nextCursor) return;
		const mine = token;
		loadingMore = true;
		try {
			const page = await fetchPage(postId, tab, nextCursor);
			if (mine !== token) return;
			posts = [...posts, ...page.posts];
			users = [...users, ...page.users];
			hasMore = page.hasMore;
			nextCursor = page.nextCursor;
		} catch {
			// Keep whatever is already listed.
		} finally {
			loadingMore = false;
		}
	}

	function findPost(id: string): Page48Post | undefined {
		return posts.find((p) => p.postId === id);
	}

	async function handleLike(id: string) {
		const post = findPost(id);
		if (post) await togglePostInteraction(post, 'like');
	}

	async function handleRepost(id: string) {
		const post = findPost(id);
		if (post) await togglePostInteraction(post, 'repost');
	}

	async function handleBookmark(id: string) {
		const post = findPost(id);
		if (post) await togglePostInteraction(post, 'bookmark');
	}

	function handleComment(post: Page48Post) {
		void goto(`/page48/post/${post.postId}`);
	}

	function handleShare(post: Page48Post) {
		void sharePost(post);
	}

	function handleDelete(id: string) {
		posts = posts.filter((p) => p.postId !== id);
	}

	let isEmpty = $derived(tab === 'quotes' ? posts.length === 0 : users.length === 0);
</script>

{#if loading}
	<PostActivityRowsSkeleton kind={tab === 'quotes' ? 'posts' : 'users'} count={4} />
{:else if failed}
	<p class="p-12 text-center text-[13px] font-medium text-gray-400 dark:text-gray-500">
		{t('page48.activity.error')}
	</p>
{:else if isEmpty && !hasMore}
	<p class="p-12 text-center text-[13px] font-medium text-gray-400 dark:text-gray-500">
		{#if tab === 'quotes'}
			{t('page48.activity.emptyQuotes')}
		{:else if tab === 'reposts'}
			{t('page48.activity.emptyReposts')}
		{:else}
			{t('page48.activity.emptyLikes')}
		{/if}
	</p>
{:else}
	<div
		class="flex flex-col divide-y divide-gray-200/60 dark:divide-white/10"
		in:fade={{ duration: 200 }}
	>
		{#if tab === 'quotes'}
			{#each posts as post (post.postId)}
				<PostCard
					{post}
					onLike={handleLike}
					onRepost={handleRepost}
					onBookmark={handleBookmark}
					onComment={handleComment}
					onShare={handleShare}
					onDelete={handleDelete}
				/>
			{/each}
		{:else}
			{#each users as user (user.userId)}
				<UserListItem {user} showFollow />
			{/each}
		{/if}

		{#if loadingMore}
			<div class="flex justify-center p-4">
				<Page48Spinner />
			</div>
		{:else if hasMore}
			<div class="p-4 flex justify-center">
				<button
					class="rounded-full px-4 py-2 text-[13px] font-semibold text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors cursor-pointer"
					onclick={loadMore}
				>
					{t('page48.activity.loadMore')}
				</button>
			</div>
		{/if}
	</div>
{/if}
