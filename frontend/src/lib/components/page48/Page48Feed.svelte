<script lang="ts">
	import { goto } from '$app/navigation';
	import { page48Api, type Page48Post } from '$lib/api/page48';
	import PostCard from '$lib/components/page48/PostCard.svelte';
	import PostComposer from '$lib/components/page48/PostComposer.svelte';
	import Page48Sidebars from '$lib/components/page48/Page48Sidebars.svelte';
	import { ErrorState } from '$lib/components';
	import { fade } from 'svelte/transition';
	import { isAuthenticated } from '$lib/stores/authStatus.svelte';
	import { showToast } from '$lib/stores/toast.svelte';
	import { t } from '$lib/i18n';
	import { sharePost, togglePostInteraction, uploadPage48Images } from '$lib/utils/page48';

	interface Props {
		media?: 'text' | 'image' | 'video' | null;
		showComposer?: boolean;
		showSidebars?: boolean;
		emptyTitle?: string;
		emptyText?: string;
	}

	let {
		media = null,
		showComposer = false,
		showSidebars = true,
		emptyTitle,
		emptyText
	}: Props = $props();

	let resolvedEmptyTitle = $derived(emptyTitle ?? t('page48.feed.emptyTitle'));
	let resolvedEmptyText = $derived(emptyText ?? t('page48.feed.emptyText'));

	let posts: Page48Post[] = $state([]);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let hasMore = $state(false);
	let nextCursor = $state<string | null>(null);
	let loadingMore = $state(false);

	// Load on mount and whenever the media filter changes.
	$effect(() => {
		void media;
		loadFeed();
	});

	async function loadFeed() {
		try {
			loading = true;
			error = null;
			const response = await page48Api.getFeed(20, null, media);
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
			const response = await page48Api.getFeed(20, nextCursor, media);
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

	async function handleCreatePost(content: string, files: File[]) {
		try {
			const filenames = files.length > 0 ? await uploadPage48Images(files) : [];
			const newPost = await page48Api.createPost(content, filenames);
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
		<PostComposer onPost={handleCreatePost} />
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
				/>
			{/each}

			{#if loadingMore}
				<div class="p-4 flex justify-center">
					<div
						class="w-6 h-6 border-2 border-red-200 border-t-red-600 rounded-full animate-spin"
					></div>
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
