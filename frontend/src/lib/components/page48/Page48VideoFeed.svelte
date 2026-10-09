<script lang="ts">
	import { onMount } from 'svelte';
	import {
		Heart,
		MessageCircle,
		Repeat2,
		Bookmark,
		Share2,
		ChevronUp,
		ChevronDown,
		Video
	} from 'lucide-svelte';
	import type { Page48Post } from '$lib/api/page48';
	import { page48Reads } from '$lib/stores/page48.svelte';
	import Page48Spinner from '$lib/components/page48/Page48Spinner.svelte';
	import VideoPlayer from '$lib/components/page48/VideoPlayer.svelte';
	import VideoCommentsPanel from '$lib/components/page48/VideoCommentsPanel.svelte';
	import ErrorState from '$lib/components/ErrorState.svelte';
	import { isAuthenticated } from '$lib/stores/authStatus.svelte';
	import { sharePost, togglePostInteraction } from '$lib/utils/page48';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	let posts = $state<Page48Post[]>([]);
	let loading = $state(true);
	let loadingMore = $state(false);
	let error = $state<string | null>(null);
	let hasMore = $state(false);
	let nextCursor = $state<string | null>(null);
	let sentinel: HTMLDivElement | undefined = $state();
	let scroller: HTMLDivElement | undefined = $state();
	let currentIndex = $state(0);
	/** The video whose comments are open; null keeps the panel closed. */
	let commentPost = $state<Page48Post | null>(null);
	// Mobile: full-bleed TikTok look (cover). Desktop: letterboxed & centered.
	let isMobile = $state(true);

	onMount(() => {
		// Matches the action rail's breakpoint (`sm`) so the immersive layout and the
		// outside-rail layout never disagree about available width.
		const mq = window.matchMedia('(max-width: 639px)');
		const update = () => (isMobile = mq.matches);
		update();
		mq.addEventListener('change', update);

		void loadFeed();

		return () => mq.removeEventListener('change', update);
	});

	// Infinite scroll: load the next page when the sentinel enters view.
	$effect(() => {
		const el = sentinel;
		if (!el) return;
		const observer = new IntersectionObserver(
			(entries) => {
				if (entries.some((e) => e.isIntersecting)) void loadMore();
			},
			{ root: scroller ?? null, rootMargin: '600px' }
		);
		observer.observe(el);
		return () => observer.disconnect();
	});

	function handleScroll() {
		const el = scroller;
		if (!el) return;
		currentIndex = Math.round(el.scrollTop / (el.clientHeight || 1));
		// Keep the open comments panel in sync with the clip being viewed.
		if (commentPost) {
			const current = posts[currentIndex];
			if (current && current.postId !== commentPost.postId) commentPost = current;
		}
	}

	function goTo(index: number) {
		const el = scroller;
		if (!el) return;
		const target = Math.max(0, Math.min(index, posts.length - 1));
		el.scrollTo({ top: target * el.clientHeight, behavior: 'smooth' });
	}

	async function loadFeed() {
		try {
			loading = true;
			error = null;
			const res = await page48Reads.getFeed(10, null, 'video');
			posts = res.data.filter((p) => p.videos.length > 0);
			hasMore = res.meta.hasMore;
			nextCursor = res.meta.nextCursor;
		} catch (err: unknown) {
			const e = err as { message?: string };
			error = e?.message || t('page48.videosFeed.loadError');
		} finally {
			loading = false;
		}
	}

	async function loadMore() {
		if (loadingMore || loading || !hasMore || !nextCursor) return;
		try {
			loadingMore = true;
			const res = await page48Reads.getFeed(10, nextCursor, 'video');
			posts = [...posts, ...res.data.filter((p) => p.videos.length > 0)];
			hasMore = res.meta.hasMore;
			nextCursor = res.meta.nextCursor;
		} catch (err) {
			console.error(err);
		} finally {
			loadingMore = false;
		}
	}

	function findPost(postId: string): Page48Post | undefined {
		return posts.find((p) => p.postId === postId);
	}

	async function handleLike(postId: string) {
		if (!canInteract) return;
		const post = findPost(postId);
		if (post) await togglePostInteraction(post, 'like');
	}
	async function handleRepost(postId: string) {
		if (!canInteract) return;
		const post = findPost(postId);
		if (post) await togglePostInteraction(post, 'repost');
	}
	async function handleBookmark(postId: string) {
		if (!canInteract) return;
		const post = findPost(postId);
		if (post) await togglePostInteraction(post, 'bookmark');
	}
	function handleComment(post: Page48Post) {
		// Toggle: the same icon both opens and closes the panel for its video.
		commentPost = commentPost?.postId === post.postId ? null : post;
	}
	function handleReplyAdded(postId: string, delta: number) {
		const post = findPost(postId);
		if (post) post.replyCount += delta;
	}
	function handleShare(post: Page48Post) {
		if (!canInteract) return;
		void sharePost(post);
	}

	// Public (unauthenticated) visitors can look but not interact; hover stays.
	let canInteract = $derived(isAuthenticated.value);

	function railBtnCls(overVideo: boolean) {
		return `flex flex-col items-center gap-1 sm:gap-0.5 transition-opacity hover:opacity-80 ${
			overVideo ? 'text-white' : 'text-gray-600 dark:text-gray-300'
		} ${canInteract ? 'cursor-pointer' : 'cursor-default'}`;
	}

	function avatarUrl(post: Page48Post) {
		return (
			post.userProfilePicture_small ||
			post.userProfilePicture ||
			`https://ui-avatars.com/api/?name=${encodeURIComponent(post.userDisplayName)}&background=fca5a5&color=fff`
		);
	}

	// Larger tap targets/typography on mobile (full-screen TikTok view).
	const iconCls = 'w-[30px] h-[30px] sm:w-6 sm:h-6';
	const countCls = 'text-[13px] sm:text-[11px] font-semibold';

	// Long captions are clamped with a "show more" toggle (bottom-anchored, so
	// expanding grows upward while the block's final line stays put).
	let expandedIds = $state<string[]>([]);
	function isExpanded(id: string) {
		return expandedIds.includes(id);
	}
	function toggleExpanded(id: string) {
		expandedIds = isExpanded(id) ? expandedIds.filter((x) => x !== id) : [...expandedIds, id];
	}
	function isLongCaption(content: string) {
		return content.length > 90 || content.includes('\n');
	}
</script>

<div
	class="relative h-[calc(100dvh-4rem)] w-full bg-white/70 dark:bg-zinc-950/70 backdrop-blur-3xl"
>
	<div
		bind:this={scroller}
		onscroll={handleScroll}
		class="h-full w-full overflow-y-auto snap-y snap-mandatory no-scrollbar overscroll-y-contain"
	>
		{#if loading}
			<div class="h-full flex items-center justify-center">
				<Page48Spinner class="h-[26px] w-[26px]" />
			</div>
		{:else if error}
			<div class="h-full flex items-center justify-center p-6">
				<ErrorState
					title={t('page48.videosFeed.loadError')}
					description={error}
					onRetry={loadFeed}
				/>
			</div>
		{:else if posts.length === 0}
			<div
				class="h-full flex flex-col items-center justify-center gap-3 text-gray-400 dark:text-gray-500 p-6 text-center"
			>
				<Video size={28} />
				<p class="text-sm">{t('page48.videosFeed.emptyText')}</p>
			</div>
		{:else}
			{#each posts as post (post.postId)}
				{@const video = post.videos[0]}
				{@const ratio =
					video.width > 0 && video.height > 0
						? Math.min(Math.max(video.width / video.height, 0.5625), 1.91)
						: 16 / 9}
				<section
					class="relative h-full snap-start flex items-center justify-center"
					style:scroll-snap-stop="always"
				>
					<div
						class={`relative w-full mx-auto ${isMobile ? 'h-full' : ''}`}
						style={isMobile
							? ''
							: `max-width: min(calc(100% - 9rem), calc((100dvh - 4rem) * ${ratio})); aspect-ratio: ${ratio}`}
					>
						<VideoPlayer
							src={video.url ?? ''}
							width={video.width}
							height={video.height}
							autoplay
							loop
							immersive={isMobile}
							class={isMobile ? 'h-full' : ''}
						/>

						<!-- Action rail: overlaid on the video (mobile) -->
						<div
							class="sm:hidden absolute right-2 bottom-24 flex flex-col items-center gap-6 z-[2]"
						>
							{@render rail(post, true)}
						</div>

						<!-- Action rail: outside the video on wide screens -->
						<div
							class="hidden sm:flex absolute left-full ml-4 bottom-8 z-[2] flex-col items-center gap-4"
						>
							{@render rail(post, false)}
						</div>

						<!-- Caption / author (bottom-anchored so it grows upward when expanded) -->
						<div
							class="absolute left-3 right-16 sm:right-3 bottom-16 sm:bottom-12 z-[2] text-white pointer-events-none"
						>
							<a
								href={`/page48/u/${post.username}`}
								class="font-bold text-[16px] sm:text-[14px] drop-shadow-lg pointer-events-auto"
							>
								@{post.username}
							</a>
							{#if post.content}
								<p
									class={`text-[15px] sm:text-[13px] leading-snug mt-1 drop-shadow-lg break-words ${
										isExpanded(post.postId)
											? 'whitespace-pre-wrap max-h-[40vh] overflow-y-auto no-scrollbar'
											: 'line-clamp-2'
									}`}
								>
									{post.content}
								</p>
								{#if isLongCaption(post.content)}
									<button
										class="pointer-events-auto text-[13px] font-bold opacity-90 mt-1 cursor-pointer drop-shadow"
										onclick={() => toggleExpanded(post.postId)}
									>
										{isExpanded(post.postId)
											? t('page48.video.showLess')
											: t('page48.video.showMore')}
									</button>
								{/if}
							{/if}
						</div>
					</div>
				</section>
			{/each}

			<div bind:this={sentinel} class="h-1 w-full"></div>
		{/if}
	</div>

	<!-- Desktop: arrow navigation (replaces the scrollbar, like TikTok web) -->
	{#if !loading && !error && posts.length > 0}
		<div class="hidden md:flex absolute right-4 top-1/2 -translate-y-1/2 z-[5] flex-col gap-3">
			<button
				class="w-11 h-11 rounded-full border border-gray-200 dark:border-zinc-700 bg-white/90 dark:bg-zinc-900/90 backdrop-blur shadow-sm flex items-center justify-center text-gray-700 dark:text-gray-200 hover:bg-white dark:hover:bg-zinc-800 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
				onclick={() => goTo(currentIndex - 1)}
				disabled={currentIndex <= 0}
				aria-label={t('page48.video.prev')}
			>
				<ChevronUp size={20} />
			</button>
			<button
				class="w-11 h-11 rounded-full border border-gray-200 dark:border-zinc-700 bg-white/90 dark:bg-zinc-900/90 backdrop-blur shadow-sm flex items-center justify-center text-gray-700 dark:text-gray-200 hover:bg-white dark:hover:bg-zinc-800 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
				onclick={() => goTo(currentIndex + 1)}
				disabled={currentIndex >= posts.length - 1 && !hasMore}
				aria-label={t('page48.video.next')}
			>
				<ChevronDown size={20} />
			</button>
		</div>
	{/if}

	<!-- Comments: floating panel on desktop, bottom drawer on mobile -->
	{#if commentPost}
		<VideoCommentsPanel
			post={commentPost}
			onClose={() => (commentPost = null)}
			onReplyAdded={handleReplyAdded}
		/>
	{/if}
</div>

{#snippet rail(post: Page48Post, overVideo: boolean)}
	<!-- Quotes count towards the repost icon, like X. -->
	{@const repostTotal = post.repostCount + post.quoteCount}
	<!-- Uploader avatar sits above the like icon (mobile & desktop). -->
	<a
		href={`/page48/u/${post.username}`}
		class="w-11 h-11 rounded-full overflow-hidden border-2 border-white dark:border-zinc-200 bg-gray-100 dark:bg-zinc-800 shadow-lg mb-1 shrink-0"
		aria-label={t('page48.aria.profile')}
	>
		<img src={avatarUrl(post)} alt={post.username} class="w-full h-full object-cover" />
	</a>

	<button
		class={railBtnCls(overVideo)}
		onclick={() => handleLike(post.postId)}
		aria-label={t('page48.aria.like')}
		aria-disabled={!canInteract}
	>
		<Heart
			class={`${iconCls} ${overVideo ? 'drop-shadow-lg' : ''} ${
				post.isLiked ? 'fill-red-500 text-red-500' : overVideo ? 'fill-white/20' : ''
			}`}
		/>
		{#if post.likesCount > 0}
			<span class={`${countCls} ${overVideo ? 'drop-shadow' : ''}`}>{post.likesCount}</span>
		{/if}
	</button>

	<button
		class={railBtnCls(overVideo)}
		onclick={() => handleComment(post)}
		aria-label={t('page48.aria.comment')}
		aria-disabled={!canInteract}
	>
		<MessageCircle class={`${iconCls} ${overVideo ? 'fill-white/20 drop-shadow-lg' : ''}`} />
		{#if post.replyCount > 0}
			<span class={`${countCls} ${overVideo ? 'drop-shadow' : ''}`}>{post.replyCount}</span>
		{/if}
	</button>

	<button
		class={railBtnCls(overVideo)}
		onclick={() => handleRepost(post.postId)}
		aria-label={t('page48.aria.repost')}
		aria-disabled={!canInteract}
	>
		<Repeat2
			class={`${iconCls} ${overVideo ? 'drop-shadow-lg' : ''} ${
				post.isReposted ? 'text-green-500' : ''
			}`}
		/>
		{#if repostTotal > 0}
			<span class={`${countCls} ${overVideo ? 'drop-shadow' : ''}`}>{repostTotal}</span>
		{/if}
	</button>

	<button
		class={railBtnCls(overVideo)}
		onclick={() => handleBookmark(post.postId)}
		aria-label={t('page48.aria.bookmark')}
		aria-disabled={!canInteract}
	>
		<Bookmark
			class={`${iconCls} ${overVideo ? 'drop-shadow-lg' : ''} ${
				post.isBookmarked ? 'fill-blue-500 text-blue-500' : overVideo ? 'fill-white/20' : ''
			}`}
		/>
	</button>

	<button
		class={railBtnCls(overVideo)}
		onclick={() => handleShare(post)}
		aria-label={t('page48.aria.share')}
		aria-disabled={!canInteract}
	>
		<Share2 class={`${iconCls} ${overVideo ? 'drop-shadow-lg' : ''}`} />
	</button>
{/snippet}
