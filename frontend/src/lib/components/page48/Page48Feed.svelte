<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { type Page48Post } from '$lib/api/page48';
	import { page48FeedStore } from '$lib/stores/page48Feed.svelte';
	import PostCard from '$lib/components/page48/PostCard.svelte';
	import Page48Sidebars from '$lib/components/page48/Page48Sidebars.svelte';
	import Page48Spinner from '$lib/components/page48/Page48Spinner.svelte';
	import NewPostsIndicator from '$lib/components/page48/NewPostsIndicator.svelte';
	import ErrorState from '$lib/components/ErrorState.svelte';
	import { fade } from 'svelte/transition';
	import { t } from '$lib/i18n';
	import { sharePost, togglePostInteraction } from '$lib/utils/page48';

	interface Props {
		media?: 'text' | 'image' | 'video' | null;
		/** Only show posts from accounts the viewer follows (requires sign-in). */
		following?: boolean;
		showSidebars?: boolean;
		emptyTitle?: string;
		emptyText?: string;
	}

	let {
		media = null,
		following = false,
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

	// Home and Following keep their posts and scroll between visits; the media
	// pages (Photos/Videos) are left as they are for now.
	// svelte-ignore state_referenced_locally
	const persistent = media === null;
	// svelte-ignore state_referenced_locally
	const feedKey = persistent ? (following ? 'following' : 'home') : `media:${media}`;

	const feed = page48FeedStore;
	// svelte-ignore state_referenced_locally
	const params = { media, following };
	const bucket = feed.bucket(feedKey);

	let posts = $derived(bucket.posts);
	let loading = $derived(!bucket.isLoaded && !bucket.error);
	let error = $derived(bucket.error);
	let loadingMore = $derived(bucket.isLoadingMore);
	let hasMore = $derived(bucket.hasMore);
	let pendingCount = $derived(bucket.pending.length);
	/** True while the timeline sits at the very top (drives the indicator style). */
	let atTop = $state(true);

	/** Up to three avatars of the authors behind the waiting posts. */
	let pendingAvatars = $derived.by(() => {
		const seen = new Set<string>();
		const out: string[] = [];
		for (const post of bucket.pending) {
			const picture = post.userProfilePicture_small ?? post.userProfilePicture;
			if (picture && !seen.has(post.userId)) {
				seen.add(post.userId);
				out.push(picture);
				if (out.length >= 3) break;
			}
		}
		return out;
	});

	/** How often an active Home/Following page looks for new posts. */
	const REFRESH_INTERVAL_MS = 3 * 60 * 1000;

	let scrollFrame = 0;
	let refreshTimer: ReturnType<typeof setInterval> | undefined;

	function handleScroll() {
		atTop = window.scrollY <= 16;

		const scrollY = window.scrollY;
		const innerHeight = window.innerHeight;
		const offsetHeight = document.body.offsetHeight;
		if (scrollY + innerHeight >= offsetHeight - 500) {
			void feed.loadMore(feedKey, params);
		}

		if (scrollFrame || !persistent) return;
		scrollFrame = requestAnimationFrame(() => {
			scrollFrame = 0;
			feed.saveScroll(feedKey, window.scrollY);
		});
	}

	/** Refresh only while this page is the active, visible tab. */
	function backgroundRefresh() {
		if (!persistent) return;
		if (document.visibilityState !== 'visible' || !document.hasFocus()) return;
		void feed.refresh(feedKey, params);
	}

	function applyPending() {
		feed.applyPending(feedKey);
		window.scrollTo({ top: 0, behavior: 'smooth' });
	}

	onMount(() => {
		window.addEventListener('scroll', handleScroll, { passive: true });
		window.addEventListener('focus', backgroundRefresh);
		document.addEventListener('visibilitychange', backgroundRefresh);
		if (persistent) refreshTimer = setInterval(backgroundRefresh, REFRESH_INTERVAL_MS);

		atTop = window.scrollY <= 16;

		// Always set the offset ourselves: a loaded feed restores where it was, a
		// fresh one starts at the top — whichever page the user came from.
		const restore = persistent && bucket.isLoaded ? bucket.scrollY : 0;
		requestAnimationFrame(() => window.scrollTo(0, restore));
		if (bucket.isLoaded) {
			backgroundRefresh();
		} else {
			void feed.ensure(feedKey, params);
		}

		// A post created from the navbar composer is prepended without a refetch
		// (Home only: the Following feed is filtered).
		function handleCreated(event: Event) {
			if (!persistent || following) return;
			const post = (event as CustomEvent<Page48Post>).detail;
			if (post?.postId) feed.prepend(feedKey, post);
		}
		window.addEventListener('page48:post-created', handleCreated);

		return () => {
			window.removeEventListener('scroll', handleScroll);
			window.removeEventListener('focus', backgroundRefresh);
			document.removeEventListener('visibilitychange', backgroundRefresh);
			window.removeEventListener('page48:post-created', handleCreated);
			if (refreshTimer) clearInterval(refreshTimer);
			if (scrollFrame) cancelAnimationFrame(scrollFrame);
		};
	});

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
		feed.removePost(feedKey, postId);
	}
</script>

<div
	class="relative max-w-[620px] mx-auto w-full min-h-screen bg-white/70 dark:bg-zinc-950/70 backdrop-blur-3xl sm:border-x border-gray-200/60 dark:border-white/10 pb-24 shadow-sm shadow-black/5 dark:shadow-none transition-all"
>
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
			<ErrorState
				title={t('page48.feed.loadError')}
				description={error}
				onRetry={() => feed.ensure(feedKey, params, true)}
			/>
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
			<NewPostsIndicator
				count={pendingCount}
				avatars={pendingAvatars}
				{atTop}
				onApply={applyPending}
			/>

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
