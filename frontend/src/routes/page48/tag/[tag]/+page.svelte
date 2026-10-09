<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { Hash } from 'lucide-svelte';
	import type { Page48Post } from '$lib/api/page48';
	import PostCard from '$lib/components/page48/PostCard.svelte';
	import Page48Sidebars from '$lib/components/page48/Page48Sidebars.svelte';
	import Page48Spinner from '$lib/components/page48/Page48Spinner.svelte';
	import ErrorState from '$lib/components/ErrorState.svelte';
	import { page48NavbarStore, page48Reads } from '$lib/stores/page48.svelte';
	import { sharePost, togglePostInteraction, getActiveMedia } from '$lib/utils/page48';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { fade } from 'svelte/transition';

	const { t } = useTranslation();

	let tag = $derived($page.params.tag ?? '');
	// Media filter inherited from the feed the user came from (Gambar/Video).
	let media = $derived(getActiveMedia($page.url.pathname, $page.url.search));
	let mediaLabel = $derived(
		media === 'image'
			? t('page48.tag.mediaImage')
			: media === 'video'
				? t('page48.tag.mediaVideo')
				: media === 'text'
					? t('page48.tag.mediaText')
					: null
	);

	let posts = $state<Page48Post[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let loadingMore = $state(false);
	let hasMore = $state(false);
	let nextCursor = $state<string | null>(null);

	onMount(() => {
		page48NavbarStore.pageType = 'feed';
	});

	// Reload when the tag param or the media filter changes.
	$effect(() => {
		const value = tag;
		void media;
		if (!value) return;
		load();
	});

	async function load() {
		try {
			loading = true;
			error = null;
			const response = await page48Reads.getPostsByTag(tag, 20, null, media);
			posts = response.data;
			hasMore = response.meta.hasMore;
			nextCursor = response.meta.nextCursor;
		} catch (err: unknown) {
			const e = err as { message?: string };
			error = e?.message || t('page48.tag.loadError');
		} finally {
			loading = false;
		}
	}

	async function loadMore() {
		if (loadingMore || !hasMore || !nextCursor || loading) return;
		try {
			loadingMore = true;
			const response = await page48Reads.getPostsByTag(tag, 20, nextCursor, media);
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
</script>

<svelte:window onscroll={handleScroll} />

<SEO
	title={t('page48.seo.tagTitle', { tag })}
	path={`/page48/tag/${tag}`}
	description={t('page48.seo.tagDesc', { tag })}
	keywords={`Page48, JKT48, #${tag}, hashtag JKT48`}
/>

<div
	class="max-w-[620px] mx-auto w-full min-h-screen bg-white/70 dark:bg-zinc-950/70 backdrop-blur-3xl sm:border-x border-gray-200/60 dark:border-white/10 pb-24 shadow-sm shadow-black/5 dark:shadow-none transition-all"
>
	<!-- Header -->
	<div class="px-5 sm:px-6 pt-6 pb-4 border-b border-gray-100/60 dark:border-white/5">
		<div class="flex items-center gap-2">
			<Hash size={22} class="text-red-500" />
			<h1 class="text-xl font-bold text-gray-900 dark:text-gray-100 truncate">{tag}</h1>
		</div>
		<p class="text-[13px] text-gray-500 dark:text-gray-400 mt-1">
			{mediaLabel ? t('page48.tag.headerFiltered', { media: mediaLabel }) : t('page48.tag.header')}
		</p>
	</div>

	{#if loading}
		<div class="divide-y divide-gray-200/60 dark:divide-white/10">
			{#each Array(4) as _}
				<div class="p-5 flex gap-4 animate-pulse">
					<div class="w-11 h-11 rounded-full bg-gray-200/80 dark:bg-zinc-800 shrink-0"></div>
					<div class="flex-1 space-y-2">
						<div class="h-4 bg-gray-200 dark:bg-zinc-800 rounded w-1/4"></div>
						<div class="h-3 bg-gray-200 dark:bg-zinc-800 rounded w-3/4"></div>
						<div class="h-3 bg-gray-200 dark:bg-zinc-800 rounded w-1/2"></div>
					</div>
				</div>
			{/each}
		</div>
	{:else if error}
		<div class="p-6">
			<ErrorState title={t('page48.tag.loadError')} description={error} onRetry={load} />
		</div>
	{:else if posts.length === 0}
		<div class="flex flex-col items-center justify-center p-16 text-center text-gray-500">
			<div
				class="w-20 h-20 rounded-full bg-gradient-to-br from-red-50 to-pink-50 dark:from-red-950/30 dark:to-pink-950/30 flex items-center justify-center mb-6 shadow-sm border border-red-100 dark:border-red-900/30"
			>
				<Hash size={28} class="text-red-500/80" />
			</div>
			<h3 class="text-lg font-bold text-gray-900 dark:text-gray-100 mb-1">
				{t('page48.feed.emptyTitle')}
			</h3>
			<p class="text-sm text-gray-500">{t('page48.tag.empty', { tag })}</p>
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

<Page48Sidebars />
