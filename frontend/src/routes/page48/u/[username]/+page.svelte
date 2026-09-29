<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { Repeat2, Settings, ExternalLink, LoaderCircle, Copy } from 'lucide-svelte';
	import { page48Api, type Page48Post, type Page48UserProfile } from '$lib/api/page48';
	import PostCard from '$lib/components/page48/PostCard.svelte';
	import { ErrorState } from '$lib/components';
	import { OptimizedImage } from '$lib/components/common';
	import { page48NavbarStore } from '$lib/stores/page48.svelte';
	import { userProfile } from '$lib/stores/profile.svelte';
	import { sharePost, togglePostInteraction } from '$lib/utils/page48';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { fade } from 'svelte/transition';

	const { t } = useTranslation();

	type Tab = 'posts' | 'media' | 'reposts' | 'replies' | 'likes' | 'bookmarks';

	let username = $derived($page.params.username ?? '');

	let profile = $state<Page48UserProfile | null>(null);
	let loadingProfile = $state(true);
	let profileError = $state<string | null>(null);
	let notFound = $state(false);

	let activeTab = $state<Tab>('posts');
	let posts = $state<Page48Post[]>([]);
	let loadingList = $state(true);
	let loadingMore = $state(false);
	let hasMore = $state(false);
	let nextCursor = $state<string | null>(null);

	let isOwnProfile = $derived(!!profile && userProfile.data?.username === profile.username);

	let tabs = $derived.by(() => {
		const items: { key: Tab; label: string }[] = [
			{ key: 'posts', label: t('page48.tabs.posts') },
			{ key: 'media', label: t('page48.tabs.media') },
			{ key: 'reposts', label: t('page48.tabs.reposts') },
			{ key: 'replies', label: t('page48.tabs.replies') }
		];
		// Likes & bookmarks are private and only shown on your own profile.
		if (isOwnProfile) {
			items.push(
				{ key: 'likes', label: t('page48.tabs.likes') },
				{ key: 'bookmarks', label: t('page48.tabs.bookmarks') }
			);
		}
		return items;
	});

	onMount(() => {
		page48NavbarStore.pageType = 'user-profile';
	});

	// Reload when the route param changes (component is reused for same-route nav).
	$effect(() => {
		const name = username;
		if (!name) return;
		loadProfile();
	});

	async function loadProfile() {
		try {
			loadingProfile = true;
			profileError = null;
			notFound = false;
			if (!username) {
				notFound = true;
				return;
			}
			profile = await page48Api.getUserProfile(username);
			await loadTab('posts');
		} catch (err: unknown) {
			const e = err as { status?: number; message?: string };
			if (e?.status === 404) {
				notFound = true;
			} else {
				profileError = e?.message || t('page48.userPage.loadError');
			}
		} finally {
			loadingProfile = false;
		}
	}

	async function fetchTab(tab: Tab, cursor: string | null) {
		switch (tab) {
			case 'media':
				return page48Api.getUserPosts(username, 20, cursor, 'image');
			case 'reposts':
				return page48Api.getUserReposts(username, 20, cursor);
			case 'replies':
				return page48Api.getUserReplies(username, 20, cursor);
			case 'likes':
				return page48Api.getLikes(20, cursor);
			case 'bookmarks':
				return page48Api.getBookmarks(20, cursor);
			default:
				return page48Api.getUserPosts(username, 20, cursor);
		}
	}

	async function loadTab(tab: Tab) {
		activeTab = tab;
		try {
			loadingList = true;
			const response = await fetchTab(tab, null);
			posts = response.data;
			hasMore = response.meta.hasMore;
			nextCursor = response.meta.nextCursor;
		} catch (err) {
			console.error(err);
			posts = [];
			hasMore = false;
			nextCursor = null;
		} finally {
			loadingList = false;
		}
	}

	async function loadMore() {
		if (loadingMore || !hasMore || !nextCursor || loadingList) return;
		try {
			loadingMore = true;
			const response = await fetchTab(activeTab, nextCursor);
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
		if (post) {
			await togglePostInteraction(post, 'repost');
			// Un-reposting from the Repost tab should remove it from the list.
			if (activeTab === 'reposts' && post && !post.isReposted) {
				posts = posts.filter((p) => p.postId !== postId);
			}
		}
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

	function getAvatarUrl(p: Page48UserProfile): string {
		if (p.profilePicture_small || p.profilePicture)
			return (p.profilePicture_small || p.profilePicture) as string;
		return `https://ui-avatars.com/api/?name=${encodeURIComponent(p.name)}&background=fca5a5&color=fff`;
	}
</script>

<svelte:window onscroll={handleScroll} />

<div
	class="max-w-[620px] mx-auto w-full min-h-screen bg-white/70 dark:bg-zinc-950/70 backdrop-blur-3xl sm:border-x border-gray-200/60 dark:border-white/10 pb-24 shadow-sm shadow-black/5 dark:shadow-none transition-all"
>
	{#if loadingProfile}
		<div class="p-5 flex gap-4 animate-pulse">
			<div class="w-20 h-20 rounded-full bg-gray-200/80 dark:bg-zinc-800 shrink-0"></div>
			<div class="flex-1 space-y-3 pt-2">
				<div class="h-5 bg-gray-200 dark:bg-zinc-800 rounded w-1/3"></div>
				<div class="h-3 bg-gray-200 dark:bg-zinc-800 rounded w-1/4"></div>
				<div class="h-3 bg-gray-200 dark:bg-zinc-800 rounded w-2/3"></div>
			</div>
		</div>
	{:else if notFound}
		<div class="flex flex-col items-center justify-center p-16 text-center text-gray-500">
			<div
				class="w-20 h-20 rounded-full bg-gradient-to-br from-red-50 to-pink-50 dark:from-red-950/30 dark:to-pink-950/30 flex items-center justify-center mb-6 shadow-sm border border-red-100 dark:border-red-900/30"
			>
				<span class="font-black text-red-500/80 text-3xl">48</span>
			</div>
			<h3 class="text-lg font-bold text-gray-900 dark:text-gray-100 mb-1">
				{t('page48.userPage.notFoundTitle')}
			</h3>
			<p class="text-sm text-gray-500">{t('page48.userPage.notFoundText')}</p>
		</div>
	{:else if profileError}
		<div class="p-6">
			<ErrorState
				title={t('page48.userPage.loadError')}
				description={profileError}
				onRetry={loadProfile}
			/>
		</div>
	{:else if profile}
		<!-- Profile header -->
		<div class="flex flex-col gap-4 px-5 sm:px-6 pt-6 pb-4">
			<div class="flex items-start gap-4">
				<div
					class="w-20 h-20 rounded-full overflow-hidden bg-gray-100 dark:bg-zinc-800 shrink-0 ring-2 ring-white dark:ring-zinc-900 shadow-sm"
				>
					<OptimizedImage
						src={getAvatarUrl(profile)}
						srcMedium={profile.profilePicture_medium}
						srcSmall={profile.profilePicture_small}
						blurHash={profile.blurHash}
						alt={profile.name}
						class="w-full h-full object-cover"
						sizes="80px"
					/>
				</div>
				<div class="flex-1 min-w-0 pt-1">
					<h1 class="text-lg font-bold text-gray-900 dark:text-gray-100 truncate">
						{profile.name}
					</h1>
					<p class="text-[14px] text-gray-500 dark:text-gray-400 truncate">@{profile.username}</p>
					<div class="flex items-center gap-3 mt-2 text-[13px] text-gray-500 dark:text-gray-400">
						<span
							><span class="font-semibold text-gray-900 dark:text-gray-100"
								>{profile.postCount}</span
							>
							{t('page48.tabs.posts')}</span
						>
						<span
							><span class="font-semibold text-gray-900 dark:text-gray-100"
								>{profile.repostCount}</span
							>
							{t('page48.tabs.reposts')}</span
						>
					</div>
				</div>
			</div>

			{#if profile.bio}
				<p class="text-[14px] text-gray-700 dark:text-gray-300 whitespace-pre-wrap break-words">
					{profile.bio}
				</p>
			{/if}

			<div class="flex items-center gap-2">
				{#if isOwnProfile}
					<button
						onclick={() => goto('/settings')}
						class="flex items-center gap-2 px-4 py-2 rounded-full border border-gray-200 dark:border-zinc-800 text-[13px] font-semibold text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-zinc-900 transition-colors cursor-pointer"
					>
						<Settings size={15} />
						{t('page48.userPage.editInSettings')}
					</button>
				{/if}
				<a
					href={`/u/${profile.username}`}
					class="flex items-center gap-2 px-4 py-2 rounded-full border border-gray-200 dark:border-zinc-800 text-[13px] font-semibold text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-zinc-900 transition-colors cursor-pointer"
				>
					<ExternalLink size={15} />
					{t('page48.userPage.fullProfile')}
				</a>
			</div>
		</div>

		<!-- Tabs -->
		<div class="flex border-b border-gray-200/60 dark:border-white/10 overflow-x-auto no-scrollbar">
			{#each tabs as tab}
				<button
					onclick={() => loadTab(tab.key)}
					class={`shrink-0 sm:flex-1 px-4 sm:px-2 py-3 text-[14px] font-semibold whitespace-nowrap transition-colors cursor-pointer border-b-2 -mb-px ${
						activeTab === tab.key
							? 'text-red-600 dark:text-red-400 border-red-600 dark:border-red-400'
							: 'text-gray-500 dark:text-gray-400 border-transparent hover:text-gray-800 dark:hover:text-gray-200'
					}`}
				>
					{tab.label}
				</button>
			{/each}
		</div>

		<!-- Post list -->
		{#if loadingList}
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
		{:else if posts.length === 0}
			<div class="p-12 text-center text-[13px] font-medium text-gray-400 dark:text-gray-500">
				{#if activeTab === 'posts'}
					{t('page48.empty.posts')}
				{:else if activeTab === 'media'}
					{t('page48.empty.media')}
				{:else if activeTab === 'reposts'}
					{t('page48.empty.reposts')}
				{:else if activeTab === 'likes'}
					{t('page48.empty.likes')}
				{:else if activeTab === 'bookmarks'}
					{t('page48.empty.bookmarks')}
				{:else}
					{t('page48.empty.replies')}
				{/if}
			</div>
		{:else if activeTab === 'media'}
			<div class="grid grid-cols-3 gap-0.5 p-0.5" in:fade={{ duration: 250 }}>
				{#each posts as post (post.postId)}
					{@const cover = post.images?.[0]}
					{#if cover}
						<a
							href={`/page48/post/${post.postId}`}
							class="relative block aspect-square bg-gray-100 dark:bg-zinc-800 overflow-hidden cursor-pointer group"
						>
							<OptimizedImage
								src={cover.url}
								srcMedium={cover.url_medium}
								srcSmall={cover.url_small}
								blurHash={cover.blurHash}
								alt={t('page48.aria.media')}
								class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
							/>
							{#if post.images.length > 1}
								<span
									class="absolute top-1.5 right-1.5 text-white drop-shadow-[0_1px_2px_rgba(0,0,0,0.6)]"
									aria-label={t('page48.aria.imageCount', { count: post.images.length })}
									title={t('page48.aria.imageCount', { count: post.images.length })}
								>
									<Copy size={16} fill="currentColor" />
								</span>
							{/if}
						</a>
					{/if}
				{/each}
			</div>

			{#if loadingMore}
				<div class="p-4 flex justify-center">
					<LoaderCircle size={20} class="animate-spin text-gray-400" />
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
		{:else}
			<div
				class="flex flex-col divide-y divide-gray-200/60 dark:divide-white/10"
				in:fade={{ duration: 250 }}
			>
				{#each posts as post (post.postId)}
					<div>
						{#if activeTab === 'reposts'}
							<div
								class="flex items-center gap-2 px-5 sm:px-6 pt-4 text-[13px] font-medium text-gray-500 dark:text-gray-400"
							>
								<Repeat2 size={14} class="text-green-500" />
								{t('page48.userPage.reposted')}
							</div>
						{/if}
						<PostCard
							{post}
							onLike={handleLike}
							onRepost={handleRepost}
							onBookmark={handleBookmark}
							onComment={handleComment}
							onShare={handleShare}
						/>
					</div>
				{/each}

				{#if loadingMore}
					<div class="p-4 flex justify-center">
						<LoaderCircle size={20} class="animate-spin text-gray-400" />
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
	{/if}
</div>
