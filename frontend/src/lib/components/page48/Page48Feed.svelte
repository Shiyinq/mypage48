<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { page48Api, type Page48Post } from '$lib/api/page48';
	import PostCard from '$lib/components/page48/PostCard.svelte';
	import PostComposer from '$lib/components/page48/PostComposer.svelte';
	import Page48Sidebars from '$lib/components/page48/Page48Sidebars.svelte';
	import Page48Spinner from '$lib/components/page48/Page48Spinner.svelte';
	import { ErrorState } from '$lib/components';
	import { fade } from 'svelte/transition';
	import { isAuthenticated } from '$lib/stores/authStatus.svelte';
	import { showToast } from '$lib/stores/toast.svelte';
	import { t } from '$lib/i18n';
	import {
		sharePost,
		togglePostInteraction,
		uploadPage48Images,
		uploadPage48Video,
		type PostDraftInput,
		type VideoDraft
	} from '$lib/utils/page48';

	interface Props {
		media?: 'text' | 'image' | 'video' | null;
		/** Only show posts from accounts the viewer follows (requires sign-in). */
		following?: boolean;
		showComposer?: boolean;
		showSidebars?: boolean;
		emptyTitle?: string;
		emptyText?: string;
	}

	let {
		media = null,
		following = false,
		showComposer = false,
		showSidebars = true,
		emptyTitle,
		emptyText
	}: Props = $props();

	let resolvedEmptyTitle = $derived(
		emptyTitle ?? (following ? t('page48.feed.followingEmptyTitle') : t('page48.feed.emptyTitle'))
	);
	let resolvedEmptyText = $derived(
		emptyText ?? (following ? t('page48.feed.followingEmptyText') : t('page48.feed.emptyText'))
	);

	let posts: Page48Post[] = $state([]);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let hasMore = $state(false);
	let nextCursor = $state<string | null>(null);
	let loadingMore = $state(false);

	// Load on mount and whenever the media filter or mode changes.
	$effect(() => {
		void media;
		void following;
		loadFeed();
	});

	// A post created from the navbar composer arrives as a window event, so the feed
	// can show it without a refetch (only when no media/following filter is active).
	onMount(() => {
		function handleCreated(event: Event) {
			if (media || following) return;
			const post = (event as CustomEvent<Page48Post>).detail;
			if (post?.postId) posts = [post, ...posts];
		}
		window.addEventListener('page48:post-created', handleCreated);
		return () => window.removeEventListener('page48:post-created', handleCreated);
	});

	async function loadFeed() {
		try {
			loading = true;
			error = null;
			const response = await page48Api.getFeed(20, null, media, following);
			posts = response.data;
			hasMore = response.meta.hasMore;
			nextCursor = response.meta.nextCursor;
		} catch (err: unknown) {
			const e = err as { message?: string };
			error = e?.message || t('page48.feed.loadError');
		} finally {
			loading = false;
		}
	}

	async function loadMore() {
		if (loadingMore || !hasMore || !nextCursor || loading) return;
		try {
			loadingMore = true;
			const response = await page48Api.getFeed(20, nextCursor, media, following);
			posts = [...posts, ...response.data];
			hasMore = response.meta.hasMore;
			nextCursor = response.meta.nextCursor;
		} catch (err) {
			console.error(err);
		} finally {
			loadingMore = false;
		}
	}

	function handleScroll() {
		const scrollY = window.scrollY;
		const innerHeight = window.innerHeight;
		const offsetHeight = document.body.offsetHeight;

		if (scrollY + innerHeight >= offsetHeight - 500) {
			loadMore();
		}
	}

	function findPost(postId: string): Page48Post | undefined {
		return posts.find((p) => p.postId === postId);
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
		goto(`/page48/post/${post.postId}`);
	}

	function handleShare(post: Page48Post) {
		void sharePost(post);
	}

	function handleDelete(postId: string) {
		posts = posts.filter((p) => p.postId !== postId);
	}

	/** Upload one composed draft and return the payload the API expects. */
	async function buildThreadItem(draft: PostDraftInput) {
		const images = draft.images.length > 0 ? await uploadPage48Images(draft.images) : [];
		const videos = draft.video ? [await uploadPage48Video(draft.video)] : [];
		return {
			content: draft.content,
			images,
			videos,
			poll: draft.poll,
			quotedPostId: draft.quotedPostId ?? null
		};
	}

	async function handleCreateThread(drafts: PostDraftInput[]) {
		try {
			const items = [];
			for (const draft of drafts) {
				items.push(await buildThreadItem(draft));
			}

			const thread = await page48Api.createThread(items);
			if (thread?.posts?.length) {
				// Only the first post belongs in the feed; the rest live in the thread.
				posts = [thread.posts[0], ...posts];
				showToast(t('page48.thread.sent', { count: thread.posts.length }), 'success');
			}
		} catch (err: unknown) {
			console.error(err);
			const e = err as { message?: string; detail?: string };
			showToast(e?.detail || e?.message || t('page48.thread.error'), 'error');
			throw err; // Rethrow so Composer stops loading state
		}
	}

	async function handleCreatePost(
		content: string,
		files: File[],
		video: VideoDraft | null,
		poll: { options: string[] } | null,
		quotedPostId: string | null
	) {
		try {
			const images = files.length > 0 ? await uploadPage48Images(files) : [];
			const videos = video ? [await uploadPage48Video(video)] : [];
			const newPost = await page48Api.createPost(
				content,
				images,
				videos,
				undefined,
				poll,
				quotedPostId ?? undefined
			);
			if (newPost) {
				posts = [newPost, ...posts];
				showToast(t('page48.feed.postSuccess'), 'success');
			}
		} catch (err: unknown) {
			console.error(err);
			const e = err as { message?: string };
			showToast(e?.message || t('page48.feed.postError'), 'error');
			throw err; // Rethrow so Composer stops loading state
		}
	}
</script>

<svelte:window onscroll={handleScroll} />

<div
	class="relative max-w-[620px] mx-auto w-full min-h-screen bg-white/70 dark:bg-zinc-950/70 backdrop-blur-3xl sm:border-x border-gray-200/60 dark:border-white/10 pb-24 shadow-sm shadow-black/5 dark:shadow-none transition-all"
>
	{#if showComposer && isAuthenticated.value}
		<PostComposer onPost={handleCreatePost} onPostThread={handleCreateThread} />
	{/if}

	{#if loading}
		<!-- Skeleton Feed -->
		<div class="divide-y divide-gray-200/60 dark:divide-white/10">
			{#each Array(5) as _}
				<div class="p-5 flex gap-4 animate-pulse">
					<div class="w-11 h-11 rounded-full bg-gray-200/80 dark:bg-zinc-800 shrink-0"></div>
					<div class="flex-1 space-y-2">
						<div class="flex items-center justify-between">
							<div class="h-4 bg-gray-200 dark:bg-zinc-800 rounded w-1/4"></div>
							<div class="h-3 bg-gray-200 dark:bg-zinc-800 rounded w-12"></div>
						</div>
						<div class="h-3 bg-gray-200 dark:bg-zinc-800 rounded w-3/4"></div>
						<div class="h-3 bg-gray-200 dark:bg-zinc-800 rounded w-1/2"></div>
					</div>
				</div>
			{/each}
		</div>
	{:else if error}
		<div class="p-6">
			<ErrorState title={t('page48.feed.loadError')} description={error} onRetry={loadFeed} />
		</div>
	{:else if posts.length === 0}
		<div class="flex flex-col items-center justify-center p-16 text-center text-gray-500">
			<div
				class="w-20 h-20 rounded-full bg-gradient-to-br from-red-50 to-pink-50 dark:from-red-950/30 dark:to-pink-950/30 flex items-center justify-center mb-6 shadow-sm border border-red-100 dark:border-red-900/30"
			>
				<span class="font-black text-red-500/80 text-3xl">48</span>
			</div>
			<h3 class="text-lg font-bold text-gray-900 dark:text-gray-100 mb-1">{resolvedEmptyTitle}</h3>
			<p class="text-sm text-gray-500">{resolvedEmptyText}</p>
		</div>
	{:else}
		<div
			class="flex flex-col divide-y divide-gray-200/60 dark:divide-white/10"
			in:fade={{ duration: 250 }}
		>
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

			{#if loadingMore}
				<div class="p-4 flex justify-center">
					<Page48Spinner />
				</div>
			{/if}

			{#if !hasMore && posts.length > 0}
				<div class="p-10 text-center flex flex-col items-center gap-3">
					<div class="w-1.5 h-1.5 bg-gray-300 dark:bg-gray-600 rounded-full"></div>
					<span class="text-[13px] font-medium text-gray-400 dark:text-gray-500">
						{t('page48.feed.end')}
					</span>
				</div>
			{/if}
		</div>
	{/if}
</div>

{#if showSidebars}
	<Page48Sidebars />
{/if}
