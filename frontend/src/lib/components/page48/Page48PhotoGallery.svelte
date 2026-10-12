<script lang="ts">
	import { onMount } from 'svelte';
	import { ImageOff } from 'lucide-svelte';
	import OptimizedImage from '$lib/components/common/OptimizedImage.svelte';
	import Page48Spinner from '$lib/components/page48/Page48Spinner.svelte';
	import NewPostsIndicator from '$lib/components/page48/NewPostsIndicator.svelte';
	import PostMediaViewer from '$lib/components/page48/PostMediaViewer.svelte';
	import AccountBadge from '$lib/components/page48/AccountBadge.svelte';
	import type { Page48Post } from '$lib/api/page48';
	import { page48FeedStore } from '$lib/stores/page48Feed.svelte';
	import { measureMissingImageSizes, mediaRatio } from '$lib/utils/page48';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		emptyTitle?: string;
		emptyText?: string;
	}

	let { emptyTitle, emptyText }: Props = $props();

	const { t } = useTranslation();

	// The gallery keeps its posts and scroll while mounted away, like Home/Following.
	const feed = page48FeedStore;
	const feedKey = 'photos';
	const params = { media: 'image' as const, limit: 20 };
	const bucket = feed.bucket(feedKey);

	let posts = $derived(bucket.posts);
	let loading = $derived(!bucket.isLoaded && !bucket.error);
	let error = $derived(bucket.error);
	let loadingMore = $derived(bucket.isLoadingMore);
	let pendingCount = $derived(bucket.pending.length);
	/** True while the gallery sits at the very top (drives the indicator style). */
	let atTop = $state(true);

	/** Up to three avatars of the authors behind the waiting photos. */
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

	/** One tile per photo, keeping its post and its index within `post.media`. */
	let tiles = $derived(
		posts.flatMap((post) =>
			post.media
				.map((item, index) => ({ post, item, index }))
				.filter((tile) => tile.item.type === 'image')
		)
	);

	/** The post whose viewer is open, and the media index it opened on. */
	let viewerPost = $state<Page48Post | null>(null);
	let viewerIndex = $state(0);
	/** URL to put back when the viewer closes, so the gallery link stays shareable. */
	let viewerReturnUrl: string | null = null;

	let sentinel = $state<HTMLDivElement>();

	/** How often an active gallery looks for new photos. */
	const REFRESH_INTERVAL_MS = 3 * 60 * 1000;

	let scrollFrame = 0;
	let refreshTimer: ReturnType<typeof setInterval> | undefined;

	function handleScroll() {
		atTop = window.scrollY <= 16;
		if (scrollFrame) return;
		scrollFrame = requestAnimationFrame(() => {
			scrollFrame = 0;
			feed.saveScroll(feedKey, window.scrollY);
		});
	}

	/** Refresh only while this page is the active, visible tab. */
	function backgroundRefresh() {
		if (document.visibilityState !== 'visible' || !document.hasFocus()) return;
		void feed.refresh(feedKey, params);
	}

	function applyPending() {
		feed.applyPending(feedKey);
		window.scrollTo({ top: 0, behavior: 'smooth' });
	}

	function openViewer(tile: (typeof tiles)[number]) {
		viewerPost = tile.post;
		viewerIndex = tile.index;

		if (typeof window === 'undefined') return;
		const target = `/page48/post/${tile.post.postId}`;
		if (window.location.pathname === target) return;
		viewerReturnUrl = window.location.pathname + window.location.search + window.location.hash;
		window.history.replaceState(window.history.state, '', target);
	}

	function closeViewer() {
		viewerPost = null;
		if (typeof window === 'undefined' || !viewerReturnUrl) return;
		window.history.replaceState(window.history.state, '', viewerReturnUrl);
		viewerReturnUrl = null;
	}

	onMount(() => {
		window.addEventListener('scroll', handleScroll, { passive: true });
		window.addEventListener('focus', backgroundRefresh);
		document.addEventListener('visibilitychange', backgroundRefresh);
		refreshTimer = setInterval(backgroundRefresh, REFRESH_INTERVAL_MS);

		atTop = window.scrollY <= 16;

		// Already loaded: render instantly from the store and restore scroll.
		// A fresh gallery starts at the top, whichever page the user came from.
		const restore = bucket.isLoaded ? bucket.scrollY : 0;
		requestAnimationFrame(() => window.scrollTo(0, restore));
		if (bucket.isLoaded) {
			backgroundRefresh();
		} else {
			void feed.ensure(feedKey, params);
		}

		return () => {
			window.removeEventListener('scroll', handleScroll);
			window.removeEventListener('focus', backgroundRefresh);
			document.removeEventListener('visibilitychange', backgroundRefresh);
			if (refreshTimer) clearInterval(refreshTimer);
			if (scrollFrame) cancelAnimationFrame(scrollFrame);
		};
	});

	// Older posts stored no dimensions; measure them so each tile keeps its own ratio.
	$effect(() => {
		const images = posts.flatMap((post) => post.media ?? []).filter((m) => m.type === 'image');
		if (images.length) return measureMissingImageSizes(images);
	});

	// Load the next page shortly before the sentinel scrolls into view.
	$effect(() => {
		const el = sentinel;
		if (!el) return;
		const observer = new IntersectionObserver(
			(entries) => {
				if (entries.some((entry) => entry.isIntersecting)) void feed.loadMore(feedKey, params);
			},
			{ rootMargin: '800px' }
		);
		observer.observe(el);
		return () => observer.disconnect();
	});
</script>

{#if loading}
	<!-- Centered in the visible area, like the video feed (navbar + bottom bar). -->
	<div
		class="flex min-h-[calc(100dvh-8rem)] items-center justify-center xl:min-h-[calc(100dvh-4rem)]"
	>
		<Page48Spinner class="h-[26px] w-[26px]" />
	</div>
{:else if error}
	<div class="flex flex-col items-center gap-2 py-16 text-center text-gray-500 dark:text-gray-400">
		<ImageOff size={26} />
		<p class="text-sm">{error}</p>
	</div>
{:else if tiles.length === 0}
	<div class="flex flex-col items-center gap-2 py-16 text-center text-gray-500 dark:text-gray-400">
		<ImageOff size={26} />
		<p class="text-sm font-semibold">{emptyTitle ?? t('page48.photos.emptyTitle')}</p>
		<p class="text-xs">{emptyText ?? t('page48.photos.emptyText')}</p>
	</div>
{:else}
	<NewPostsIndicator
		variant="overlay"
		count={pendingCount}
		avatars={pendingAvatars}
		{atTop}
		onApply={applyPending}
	/>

	<!-- Masonry: CSS columns keep each photo's own ratio without cropping. -->
	<div class="columns-2 gap-1 sm:columns-3 md:columns-4 lg:columns-5 2xl:columns-6 [&>*]:mb-1">
		{#each tiles as tile (tile.post.postId + ':' + tile.item.filename)}
			<button
				type="button"
				class="group relative block w-full cursor-zoom-in overflow-hidden rounded-lg bg-gray-100 dark:bg-zinc-800"
				style={`aspect-ratio: ${mediaRatio(tile.item)};`}
				onclick={() => openViewer(tile)}
				aria-label={t('page48.aria.viewImage', { index: 1, total: tiles.length })}
			>
				<OptimizedImage
					src={tile.item.url}
					srcMedium={tile.item.url_medium}
					srcSmall={tile.item.url_small}
					blurHash={tile.item.blurHash}
					alt={t('page48.aria.media')}
					class="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
					objectFit="cover"
					sizes="(max-width: 640px) 50vw, (max-width: 1280px) 33vw, 25vw"
				/>
				<!-- Author overlay, revealed on hover -->
				<span
					class="pointer-events-none absolute inset-x-0 bottom-0 flex items-center gap-1.5 bg-gradient-to-t from-black/70 to-transparent px-2.5 pb-2 pt-6 text-[12px] font-semibold text-white opacity-0 transition-opacity group-hover:opacity-100"
				>
					<span class="truncate">@{tile.post.username}</span>
					<AccountBadge type={tile.post.page48AccountType} size={12} />
				</span>
			</button>
		{/each}
	</div>

	<div bind:this={sentinel} class="h-1"></div>

	{#if loadingMore}
		<div class="flex justify-center py-8">
			<Page48Spinner class="h-[22px] w-[22px]" />
		</div>
	{/if}
{/if}

{#if viewerPost}
	<PostMediaViewer
		post={viewerPost}
		initialIndex={viewerIndex}
		isOpen={viewerPost !== null}
		onClose={closeViewer}
	/>
{/if}
