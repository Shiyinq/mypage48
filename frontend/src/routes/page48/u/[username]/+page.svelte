<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { Repeat2, Settings, Copy, Play, Pin } from 'lucide-svelte';
	import { page48Api, type Page48Post, type Page48UserProfile } from '$lib/api/page48';
	import PostCard from '$lib/components/page48/PostCard.svelte';
	import Page48Spinner from '$lib/components/page48/Page48Spinner.svelte';
	import ReportModal from '$lib/components/page48/ReportModal.svelte';
	import UserMenu from '$lib/components/page48/UserMenu.svelte';
	import ConfirmModal from '$lib/components/page48/ConfirmModal.svelte';
	import FollowButton from '$lib/components/page48/FollowButton.svelte';
	import { ErrorState } from '$lib/components';
	import { OptimizedImage } from '$lib/components/common';
	import { page48NavbarStore } from '$lib/stores/page48.svelte';
	import { userProfile } from '$lib/stores/profile.svelte';
	import { isAuthenticated } from '$lib/stores/authStatus.svelte';
	import { showToast } from '$lib/stores/toast.svelte';
	import { sharePost, togglePostInteraction } from '$lib/utils/page48';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { fade } from 'svelte/transition';

	const { t } = useTranslation();

	type Tab = 'posts' | 'media' | 'videos' | 'reposts' | 'replies' | 'likes' | 'bookmarks';

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

	// Known before the profile loads (from the route param), so the loading
	// skeleton matches the real header (settings pill vs. 3-dot menu).
	let isSameUser = $derived(!!userProfile.data?.username && userProfile.data.username === username);

	// Whether this profile has a Page48 cover image to render.
	let hasBanner = $derived(!!profile?.bannerPicture);

	// A block cuts the posts both ways, so there is nothing to list here.
	let canViewPosts = $derived(!profile?.isBlocked && !profile?.isBlockedBy);

	// A follower-only account hides its posts until the follow is approved.
	let isLockedOut = $derived(!!profile?.isLocked && !isOwnProfile && !profile?.isFollowing);

	// Everything the list area should render: tabs and posts, or a notice.
	let showPosts = $derived(canViewPosts && !isLockedOut);

	let seoTitle = $derived(
		profile ? `${profile.name} (@${profile.username}) · Page48` : t('page48.seo.userTitle')
	);
	let seoDescription = $derived(
		profile?.bio?.trim() ? profile.bio.trim().slice(0, 160) : t('page48.seo.userDesc')
	);
	let seoImage = $derived(profile ? getAvatarUrl(profile) : undefined);

	let tabs = $derived.by(() => {
		const items: { key: Tab; label: string }[] = [
			{ key: 'posts', label: t('page48.tabs.posts') },
			{ key: 'media', label: t('page48.tabs.media') },
			{ key: 'videos', label: t('page48.tabs.videos') },
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

	// A post created from the navbar composer arrives as a window event.
	onMount(() => {
		function handleCreated(event: Event) {
			const post = (event as CustomEvent<Page48Post>).detail;
			if (!post?.postId) return;
			if (activeTab !== 'posts') return;
			if (!profile || post.username !== profile.username) return;
			posts = [post, ...posts];
		}
		window.addEventListener('page48:post-created', handleCreated);
		return () => window.removeEventListener('page48:post-created', handleCreated);
	});

	// Reload when the route param changes (component is reused for same-route nav).
	$effect(() => {
		const name = username;
		if (!name) return;
		loadProfile();
	});

	// Active tab lives in the URL (?tab=…) in both directions: clicking a tab
	// updates the URL, and opening a URL directly activates that tab.
	let tabParam = $derived($page.url.searchParams.get('tab'));
	let lastTabKey = '';

	function resolveTab(raw: string | null): Tab {
		const allowed: Tab[] = isOwnProfile
			? ['posts', 'media', 'videos', 'reposts', 'replies', 'likes', 'bookmarks']
			: ['posts', 'media', 'videos', 'reposts', 'replies'];
		return raw && (allowed as string[]).includes(raw) ? (raw as Tab) : 'posts';
	}

	$effect(() => {
		const name = username;
		const target = resolveTab(tabParam);
		if (!name) return;
		if (!showPosts) {
			activeTab = target;
			posts = [];
			hasMore = false;
			nextCursor = null;
			loadingList = false;
			// Leaving this state later must trigger a fresh load.
			lastTabKey = '';
			return;
		}
		const key = `${name}|${target}`;
		if (key === lastTabKey) return;
		lastTabKey = key;
		void loadTab(target);
	});

	function selectTab(key: Tab) {
		if (key === activeTab) return;
		const url = key === 'posts' ? `/page48/u/${username}` : `/page48/u/${username}?tab=${key}`;
		void goto(url, { keepFocus: true, noScroll: true });
	}

	/** The Page48 settings page for this profile (it is only ever your own). */
	function openSettings() {
		void goto(`/page48/u/${profile?.username ?? username}/settings`);
	}

	/** Keep the header count in sync when the follow button toggles. */
	function handleFollowChange(following: boolean, pending: boolean) {
		if (!profile) return;
		const wasFollowing = profile.isFollowing;
		profile = {
			...profile,
			isFollowing: following,
			isFollowPending: pending,
			followerCount: Math.max(
				0,
				profile.followerCount +
					(following && !wasFollowing ? 1 : !following && wasFollowing ? -1 : 0)
			)
		};
	}

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
			case 'videos':
				return page48Api.getUserPosts(username, 20, cursor, 'video');
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

	function handleDelete(postId: string) {
		posts = posts.filter((p) => p.postId !== postId);
	}

	// Only one post can be pinned, so pinning moves it to the top and clears any
	// other pin. Unpinning needs no work: PostCard already flipped the shared
	// post object, and the order stays as it was.
	function handlePinChanged(updated: Page48Post) {
		if (activeTab !== 'posts' || !updated.isPinned) return;
		const others = posts.filter((p) => p.postId !== updated.postId);
		for (const p of others) p.isPinned = false;
		posts = [updated, ...others];
	}

	let showReportUser = $state(false);
	let showBlockConfirm = $state(false);
	let showMuteConfirm = $state(false);

	/** Block asks for confirmation first; unblocking is instant. */
	function requestToggleBlock() {
		if (!profile) return;
		if (profile.isBlocked) {
			void applyBlock(false);
		} else {
			showBlockConfirm = true;
		}
	}

	async function applyBlock(blocked: boolean) {
		if (!profile) return;
		const target = profile.username;
		try {
			const res = blocked ? await page48Api.blockUser(target) : await page48Api.unblockUser(target);
			showBlockConfirm = false;
			if (profile && profile.username === target) {
				profile = { ...profile, isBlocked: res.isBlocked, isFollowing: false };
			}
			showToast(t(res.isBlocked ? 'page48.block.success' : 'page48.unblock.success'), 'success');
		} catch (err: unknown) {
			const e = err as { detail?: string; message?: string };
			showToast(e?.detail || e?.message || t('page48.block.error'), 'error');
		}
	}

	/** Muting explains itself first; unmuting is instant. */
	function requestToggleMute() {
		if (!profile) return;
		if (profile.isMuted) {
			void applyMute(false);
		} else {
			showMuteConfirm = true;
		}
	}

	async function applyMute(muted: boolean) {
		if (!profile) return;
		const target = profile.username;
		try {
			const res = muted ? await page48Api.muteUser(target) : await page48Api.unmuteUser(target);
			showMuteConfirm = false;
			if (profile && profile.username === target) {
				profile = { ...profile, isMuted: res.isMuted };
			}
			showToast(t(res.isMuted ? 'page48.mute.success' : 'page48.unmute.success'), 'success');
		} catch (err: unknown) {
			const e = err as { detail?: string; message?: string };
			showToast(e?.detail || e?.message || t('page48.mute.error'), 'error');
		}
	}

	function getAvatarUrl(p: Page48UserProfile): string {
		if (p.profilePicture_small || p.profilePicture)
			return (p.profilePicture_small || p.profilePicture) as string;
		return `https://ui-avatars.com/api/?name=${encodeURIComponent(p.name)}&background=fca5a5&color=fff`;
	}

	function formatDuration(seconds: number): string {
		const m = Math.floor(seconds / 60);
		const s = Math.floor(seconds % 60);
		return `${m}:${s.toString().padStart(2, '0')}`;
	}
</script>

<svelte:window onscroll={handleScroll} />

<SEO
	title={seoTitle}
	path={`/page48/u/${username}`}
	description={seoDescription}
	image={seoImage}
	keywords={`Page48, JKT48, ${profile?.username ?? username}, profil Page48`}
/>

<div
	class="max-w-[620px] mx-auto w-full min-h-screen bg-white/70 dark:bg-zinc-950/70 backdrop-blur-3xl sm:border-x border-gray-200/60 dark:border-white/10 pb-24 shadow-sm shadow-black/5 dark:shadow-none transition-all"
>
	{#if loadingProfile}
		<div class="animate-pulse">
			<!-- Header -->
			<div class="relative flex flex-col gap-4 px-5 sm:px-6 pt-6 pb-4">
				{#if isSameUser || isAuthenticated.value}
					<div class="absolute top-0 right-0 flex items-center gap-1">
						<div class="w-7 h-7 rounded-full bg-gray-200 dark:bg-zinc-800"></div>
					</div>
				{/if}
				<div class="flex items-start gap-4">
					<div class="flex-1 min-w-0 pt-1">
						<div class="flex items-center gap-3">
							<div class="min-w-0 space-y-2">
								<div class="h-5 w-32 bg-gray-200 dark:bg-zinc-800 rounded"></div>
								<div class="h-3.5 w-20 bg-gray-200 dark:bg-zinc-800 rounded"></div>
							</div>
							{#if !isSameUser && isAuthenticated.value}
								<div class="h-9 w-20 shrink-0 rounded-full bg-gray-200 dark:bg-zinc-800"></div>
							{/if}
						</div>
						<div class="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2">
							{#each Array(4) as _}
								<div class="h-3.5 bg-gray-200 dark:bg-zinc-800 rounded w-14"></div>
							{/each}
						</div>
						<!-- Bio -->
						<div class="space-y-2 mt-2">
							<div class="h-3.5 bg-gray-200 dark:bg-zinc-800 rounded w-full"></div>
							<div class="h-3.5 bg-gray-200 dark:bg-zinc-800 rounded w-2/3"></div>
						</div>
					</div>
					<div class="w-36 h-36 rounded-full bg-gray-200/80 dark:bg-zinc-800 shrink-0"></div>
				</div>
			</div>

			<!-- Tabs -->
			<div class="flex border-b border-gray-200/60 dark:border-white/10">
				{#each Array(4) as _}
					<div class="flex-1 px-4 sm:px-2 py-3 flex justify-center">
						<div class="h-4 bg-gray-200 dark:bg-zinc-800 rounded w-3/4"></div>
					</div>
				{/each}
			</div>

			<!-- Post list -->
			<div class="divide-y divide-gray-200/60 dark:divide-white/10">
				{#each Array(4) as _}
					<div class="p-5 flex gap-4">
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
		{#if hasBanner}
			<!-- Banner (Page48 cover) -->
			<div class="w-full aspect-[3/1] overflow-hidden">
				<OptimizedImage
					src={profile.bannerPicture}
					srcMedium={profile.bannerPicture_medium}
					srcSmall={profile.bannerPicture_small}
					blurHash={profile.bannerBlurHash}
					alt={profile.name}
					class="w-full h-full object-cover"
					sizes="(max-width: 640px) 100vw, 620px"
				/>
			</div>
		{/if}

		<!-- Profile header -->
		<div class="relative flex flex-col gap-4 px-5 sm:px-6 pt-6 pb-4">
			<!-- Actions (top-right corner, just below the cover) -->
			{#if isOwnProfile || isAuthenticated.value}
				<div class="absolute top-0 right-0 flex items-center gap-1">
					{#if isOwnProfile}
						<button
							onclick={openSettings}
							title={t('page48.userPage.editInSettings')}
							aria-label={t('page48.userPage.editInSettings')}
							class="p-1 rounded-full text-gray-400 hover:text-gray-900 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
						>
							<Settings class="w-5 h-5" />
						</button>
					{/if}
					{#if !isOwnProfile && isAuthenticated.value}
						<UserMenu
							onReport={() => (showReportUser = true)}
							onToggleBlock={requestToggleBlock}
							onToggleMute={requestToggleMute}
							isBlocked={profile.isBlocked}
							isMuted={profile.isMuted}
						/>
					{/if}
				</div>
			{/if}

			<div class="flex items-start gap-4">
				<!-- Name + username + stats -->
				<div class="flex-1 min-w-0 pt-1">
					<div class="flex items-center gap-3">
						<div class="min-w-0">
							<h1 class="text-lg font-bold text-gray-900 dark:text-gray-100 truncate">
								{profile.name}
							</h1>
							<p class="text-[14px] text-gray-500 dark:text-gray-400 truncate">
								@{profile.username}
							</p>
						</div>
						{#if !isOwnProfile && isAuthenticated.value && !profile.isBlocked && !profile.isBlockedBy}
							<FollowButton
								username={profile.username}
								isFollowing={profile.isFollowing}
								isPending={profile.isFollowPending}
								size="md"
								onChange={handleFollowChange}
							/>
						{/if}
					</div>
					<div
						class="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2 text-[13px] text-gray-500 dark:text-gray-400"
					>
						<!-- Follow counts link to the public lists, but only for signed-in users. -->
						<a
							href={isAuthenticated.value ? `/page48/u/${profile.username}/followers` : undefined}
							class={isAuthenticated.value ? 'hover:underline' : undefined}
						>
							<span class="font-semibold text-gray-900 dark:text-gray-100"
								>{profile.followerCount}</span
							>
							{t('page48.userPage.followers')}
						</a>
						<a
							href={isAuthenticated.value ? `/page48/u/${profile.username}/following` : undefined}
							class={isAuthenticated.value ? 'hover:underline' : undefined}
						>
							<span class="font-semibold text-gray-900 dark:text-gray-100"
								>{profile.followingCount}</span
							>
							{t('page48.userPage.following')}
						</a>
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

					{#if profile.bio}
						<p
							class="mt-2 text-[14px] text-gray-700 dark:text-gray-300 whitespace-pre-wrap break-words"
						>
							{profile.bio}
						</p>
					{/if}
				</div>

				<!-- Profile photo (right) -->
				<div
					class="w-36 h-36 relative z-10 rounded-full overflow-hidden bg-gray-100 dark:bg-zinc-800 shrink-0 ring-2 ring-white shadow-sm dark:ring-zinc-900"
				>
					<OptimizedImage
						src={getAvatarUrl(profile)}
						srcMedium={profile.profilePicture_medium}
						srcSmall={profile.profilePicture_small}
						blurHash={profile.blurHash}
						alt={profile.name}
						class="w-full h-full object-cover"
						sizes="144px"
					/>
				</div>
			</div>
		</div>

		<!-- Tabs -->
		{#if !showPosts}
			<div class="p-12 text-center text-[13px] font-medium text-gray-400 dark:text-gray-500">
				{#if !canViewPosts}
					{profile.isBlocked ? t('page48.block.youBlocked') : t('page48.block.blockedBy')}
				{:else}
					{profile.isFollowPending
						? t('page48.follow.requestPending')
						: t('page48.follow.lockedPosts')}
				{/if}
			</div>
		{:else}
			<div
				class="flex border-b border-gray-200/60 dark:border-white/10 overflow-x-auto no-scrollbar"
			>
				{#each tabs as tab}
					<button
						onclick={() => selectTab(tab.key)}
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
					{:else if activeTab === 'videos'}
						{t('page48.empty.videos')}
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
			{:else if activeTab === 'videos'}
				<div class="grid grid-cols-3 gap-0.5 p-0.5" in:fade={{ duration: 250 }}>
					{#each posts as post (post.postId)}
						{@const clip = post.videos?.[0]}
						{#if clip?.url}
							<a
								href={`/page48/post/${post.postId}`}
								class="relative block aspect-square bg-gray-100 dark:bg-zinc-800 overflow-hidden cursor-pointer group"
								aria-label={t('page48.video.play')}
							>
								<video
									src={clip.url}
									muted
									playsinline
									preload="metadata"
									class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
								></video>
								<span class="absolute inset-0 flex items-center justify-center pointer-events-none">
									<span
										class="w-9 h-9 rounded-full bg-black/45 backdrop-blur flex items-center justify-center"
									>
										<Play size={16} class="text-white translate-x-0.5" fill="currentColor" />
									</span>
								</span>
								{#if clip.duration > 0}
									<span
										class="absolute bottom-1 right-1 px-1.5 py-0.5 rounded bg-black/60 text-white text-[10px] font-medium tabular-nums"
									>
										{formatDuration(clip.duration)}
									</span>
								{/if}
							</a>
						{/if}
					{/each}
				</div>

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
							{:else if activeTab === 'posts' && post.isPinned}
								<div
									class="flex items-center gap-2 px-5 sm:px-6 pt-4 text-[13px] font-semibold text-red-500 dark:text-red-400"
								>
									<Pin size={14} class="fill-red-500/20" />
									{t('page48.userPage.pinned')}
								</div>
							{/if}
							<PostCard
								{post}
								onLike={handleLike}
								onRepost={handleRepost}
								onBookmark={handleBookmark}
								onComment={handleComment}
								onShare={handleShare}
								onDelete={handleDelete}
								onPinChanged={handlePinChanged}
							/>
						</div>
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
		{/if}
	{/if}
</div>

{#if showBlockConfirm && profile}
	<ConfirmModal
		title={t('page48.block.title')}
		message={t('page48.block.message', { name: profile.name })}
		confirmText={t('page48.block.confirm')}
		destructive
		onCancel={() => (showBlockConfirm = false)}
		onConfirm={() => applyBlock(true)}
	/>
{/if}

{#if showMuteConfirm && profile}
	<ConfirmModal
		title={t('page48.mute.title')}
		message={t('page48.mute.message', { name: profile.name })}
		confirmText={t('page48.mute.confirm')}
		onCancel={() => (showMuteConfirm = false)}
		onConfirm={() => applyMute(true)}
	/>
{/if}

{#if showReportUser && profile}
	<ReportModal
		targetType="user"
		targetId={profile.userId}
		onClose={() => (showReportUser = false)}
	/>
{/if}
