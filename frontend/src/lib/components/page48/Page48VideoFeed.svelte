<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import {
		Heart,
		MessageCircle,
		Repeat2,
		Bookmark,
		Share,
		ChevronUp,
		ChevronDown,
		LoaderCircle,
		Video
	} from 'lucide-svelte';
	import { page48Api, type Page48Post } from '$lib/api/page48';
	import VideoPlayer from '$lib/components/page48/VideoPlayer.svelte';
	import { ErrorState } from '$lib/components';
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
	// Mobile: full-bleed TikTok look (cover). Desktop: letterboxed & centered.
	let isMobile = $state(true);

	onMount(() => {
		const mq = window.matchMedia('(max-width: 767px)');
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
			const res = await page48Api.getFeed(10, null, 'video');
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
			const res = await page48Api.getFeed(10, nextCursor, 'video');
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
		if (!canInteract) return;
		goto(`/page48/post/${post.postId}`);
	}
	function handleShare(post: Page48Post) {
		if (!canInteract) return;
		void sharePost(post);
	}

	// Public (unauthenticated) visitors can look but not interact; hover stays.
	let canInteract = $derived(isAuthenticated.value);
	let railBtnCls = $derived(
		`flex flex-col items-center gap-1 sm:gap-0.5 text-white transition-opacity hover:opacity-80 ${canInteract ? 'cursor-pointer' : 'cursor-default'}`
	);

	// Larger tap targets/typography on mobile (full-screen TikTok view).
	const iconCls = 'w-[30px] h-[30px] sm:w-6 sm:h-6 drop-shadow-lg';
	const countCls = 'text-[13px] sm:text-[11px] font-semibold drop-shadow';
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
				<LoaderCircle size={26} class="animate-spin text-gray-400" />
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
				<section class="relative h-full snap-start" style:scroll-snap-stop="always">
					<div
						class={`relative w-full h-full mx-auto ${isMobile ? '' : 'flex items-center'}`}
						style={isMobile ? '' : `max-width: min(100%, calc((100dvh - 4rem) * ${ratio}))`}
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

						<!-- Right action rail -->
						<div
							class="absolute right-2 sm:right-3 bottom-24 flex flex-col items-center gap-4 sm:gap-3 z-[2]"
						>
							<button
								class={railBtnCls}
								onclick={() => handleLike(post.postId)}
								aria-label={t('page48.aria.like')}
								aria-disabled={!canInteract}
							>
								<Heart
									class={`${iconCls} ${post.isLiked ? 'fill-red-500 text-red-500' : 'fill-white/20'}`}
								/>
								{#if post.likesCount > 0}
									<span class={countCls}>{post.likesCount}</span>
								{/if}
							</button>
							<button
								class={railBtnCls}
								onclick={() => handleComment(post)}
								aria-label={t('page48.aria.comment')}
								aria-disabled={!canInteract}
							>
								<MessageCircle class={`${iconCls} fill-white/20`} />
								{#if post.replyCount > 0}
									<span class={countCls}>{post.replyCount}</span>
								{/if}
							</button>
							<button
								class={railBtnCls}
								onclick={() => handleRepost(post.postId)}
								aria-label={t('page48.aria.repost')}
								aria-disabled={!canInteract}
							>
								<Repeat2 class={`${iconCls} ${post.isReposted ? 'text-green-500' : ''}`} />
								{#if post.repostCount > 0}
									<span class={countCls}>{post.repostCount}</span>
								{/if}
							</button>
							<button
								class={railBtnCls}
								onclick={() => handleBookmark(post.postId)}
								aria-label={t('page48.aria.bookmark')}
								aria-disabled={!canInteract}
							>
								<Bookmark
									class={`${iconCls} ${post.isBookmarked ? 'fill-blue-400 text-blue-400' : 'fill-white/20'}`}
								/>
							</button>
							<button
								class={railBtnCls}
								onclick={() => handleShare(post)}
								aria-label={t('page48.aria.share')}
								aria-disabled={!canInteract}
							>
								<Share class={iconCls} />
							</button>
						</div>

						<!-- Caption / author (kept above the player's control bar) -->
						<div class="absolute left-3 right-16 bottom-20 z-[2] text-white pointer-events-none">
							<a
								href={`/page48/u/${post.username}`}
								class="font-bold text-[16px] sm:text-[14px] drop-shadow-lg pointer-events-auto"
							>
								@{post.username}
							</a>
							{#if post.content}
								<p
									class="text-[15px] sm:text-[13px] leading-snug line-clamp-3 sm:line-clamp-2 mt-1 drop-shadow-lg"
								>
									{post.content}
								</p>
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
</div>
