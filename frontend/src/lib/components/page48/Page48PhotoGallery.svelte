<script lang="ts">
	import { onMount } from 'svelte';
	import { ImageOff, LoaderCircle } from 'lucide-svelte';
	import OptimizedImage from '$lib/components/common/OptimizedImage.svelte';
	import PostMediaViewer from '$lib/components/page48/PostMediaViewer.svelte';
	import AccountBadge from '$lib/components/page48/AccountBadge.svelte';
	import type { Page48Post } from '$lib/api/page48';
	import { page48Reads } from '$lib/stores/page48.svelte';
	import { mediaRatio } from '$lib/utils/page48';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		emptyTitle?: string;
		emptyText?: string;
	}

	let { emptyTitle, emptyText }: Props = $props();

	const { t } = useTranslation();

	let posts = $state<Page48Post[]>([]);
	let loading = $state(true);
	let loadingMore = $state(false);
	let error = $state<string | null>(null);
	let hasMore = $state(false);
	let nextCursor = $state<string | null>(null);

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

	let sentinel = $state<HTMLDivElement>();

	function openViewer(tile: (typeof tiles)[number]) {
		viewerPost = tile.post;
		viewerIndex = tile.index;
	}

	async function loadFeed() {
		try {
			loading = true;
			error = null;
			const res = await page48Reads.getFeed(20, null, 'image');
			posts = res.data;
			hasMore = res.meta.hasMore;
			nextCursor = res.meta.nextCursor;
		} catch (err: unknown) {
			const e = err as { message?: string };
			error = e?.message || t('page48.photos.loadError');
		} finally {
			loading = false;
		}
	}

	async function loadMore() {
		if (loadingMore || loading || !hasMore || !nextCursor) return;
		try {
			loadingMore = true;
			const res = await page48Reads.getFeed(20, nextCursor, 'image');
			posts = [...posts, ...res.data];
			hasMore = res.meta.hasMore;
			nextCursor = res.meta.nextCursor;
		} catch (err) {
			console.error(err);
		} finally {
			loadingMore = false;
		}
	}

	onMount(() => {
		void loadFeed();
	});

	// Load the next page shortly before the sentinel scrolls into view.
	$effect(() => {
		const el = sentinel;
		if (!el) return;
		const observer = new IntersectionObserver(
			(entries) => {
				if (entries.some((entry) => entry.isIntersecting)) void loadMore();
			},
			{ rootMargin: '800px' }
		);
		observer.observe(el);
		return () => observer.disconnect();
	});
</script>

{#if loading}
	<div class="flex justify-center py-16">
		<LoaderCircle class="h-6 w-6 animate-spin text-gray-400" />
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
	<!-- Masonry: CSS columns keep each photo's own ratio without cropping. -->
	<div class="columns-2 gap-1.5 sm:columns-3 xl:columns-4 [&>*]:mb-1.5">
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
			<LoaderCircle class="h-5 w-5 animate-spin text-gray-400" />
		</div>
	{/if}
{/if}

{#if viewerPost}
	<PostMediaViewer
		post={viewerPost}
		initialIndex={viewerIndex}
		isOpen={viewerPost !== null}
		onClose={() => (viewerPost = null)}
	/>
{/if}
