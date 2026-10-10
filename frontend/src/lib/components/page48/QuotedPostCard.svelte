<script lang="ts">
	import { X } from 'lucide-svelte';
	import { page } from '$app/stores';
	import { portal } from '$lib/actions/portal';
	import type { Page48Post } from '$lib/api/page48';
	import PostMedia from '$lib/components/page48/PostMedia.svelte';
	import PostMediaViewer from '$lib/components/page48/PostMediaViewer.svelte';
	import PostPoll from '$lib/components/page48/PostPoll.svelte';
	import UserHoverCard from '$lib/components/page48/UserHoverCard.svelte';
	import AccountBadge from '$lib/components/page48/AccountBadge.svelte';
	import { formatPostTime, getActiveMedia, parseContent, tagUrl, userUrl } from '$lib/utils/page48';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		/** The quoted post. `null` with `unavailable` set means it was deleted. */
		post: Page48Post | null;
		/** The original is gone: show a placeholder instead of the preview. */
		unavailable?: boolean;
		/** Show a remove button (used inside the composer). */
		removable?: boolean;
		onRemove?: () => void;
	}

	let { post, unavailable = false, removable = false, onRemove }: Props = $props();

	const { t } = useTranslation();

	/**
	 * The composer preview sits inside a modal, where a portalled viewer would land
	 * behind the dialog, so a preview stays read-only.
	 */
	let interactive = $derived(!removable);

	// Keep the active media filter (Gambar/Video) when opening a hashtag.
	let activeMedia = $derived(getActiveMedia($page.url.pathname, $page.url.search));

	let contentParts = $derived(post?.content ? parseContent(post.content) : []);
	let imageUrls = $derived(post?.images?.map((image) => image.url) ?? []);

	let lightboxOpen = $state(false);
	let lightboxIndex = $state(0);

	// Opening the media viewer points the URL at the quoted post, exactly like opening
	// the media of a normal post does; closing puts the previous URL back.
	let viewerReturnUrl: string | null = null;

	function pushViewerUrl() {
		if (typeof window === 'undefined' || !post) return;
		const target = `/page48/post/${post.postId}`;
		if (window.location.pathname === target) return;
		viewerReturnUrl = window.location.pathname + window.location.search + window.location.hash;
		window.history.replaceState(window.history.state, '', target);
	}

	function restoreViewerUrl() {
		if (typeof window === 'undefined' || !viewerReturnUrl) return;
		window.history.replaceState(window.history.state, '', viewerReturnUrl);
		viewerReturnUrl = null;
	}

	function openLightbox(index: number) {
		lightboxIndex = index;
		lightboxOpen = true;
		pushViewerUrl();
	}

	function closeLightbox() {
		lightboxOpen = false;
		restoreViewerUrl();
	}

	function avatarUrl(user: Page48Post): string {
		if (user.userProfilePicture_small || user.userProfilePicture) {
			return (user.userProfilePicture_small || user.userProfilePicture) as string;
		}
		return `https://ui-avatars.com/api/?name=${encodeURIComponent(user.userDisplayName)}&background=fca5a5&color=fff`;
	}
</script>

<div
	class="group relative mt-3 overflow-hidden rounded-2xl border border-gray-200 bg-white dark:border-zinc-700 dark:bg-zinc-900"
>
	{#if removable}
		<button
			type="button"
			class="absolute right-1.5 top-1.5 z-[2] p-1.5 rounded-full text-gray-400 hover:text-gray-900 hover:bg-gray-100 dark:hover:text-gray-100 dark:hover:bg-zinc-800 cursor-pointer"
			onclick={(e) => {
				e.stopPropagation();
				onRemove?.();
			}}
			aria-label={t('page48.aria.removeQuote')}
		>
			<X size={15} />
		</button>
	{/if}

	{#if unavailable || !post}
		<p class="px-3 py-3 text-[13px] text-gray-500 dark:text-gray-400">
			{t('page48.post.quotedUnavailable')}
		</p>
	{:else}
		<!-- Full-card click target: opens the quoted post. The media and links sit above
		     it, so opening a photo does not navigate away. -->
		{#if interactive}
			<a
				href={`/page48/post/${post.postId}`}
				class="absolute inset-0 z-0"
				aria-label={t('page48.aria.openPost')}
			></a>
		{/if}

		<!-- Deliberately NOT positioned: a positioned wrapper would paint above the
		     full-card link and swallow every click. Only the pieces that must be
		     interactive are raised with z-[1]. -->
		<div class="p-3">
			<div class="flex items-center gap-1.5 text-[13px]">
				<UserHoverCard
					username={post.username}
					href={userUrl(post.username)}
					class="relative z-[1] flex min-w-0 items-center gap-1.5"
				>
					<img
						src={avatarUrl(post)}
						alt={post.username}
						class="w-6 h-6 rounded-full object-cover bg-gray-100 dark:bg-zinc-800 shrink-0"
						loading="lazy"
					/>
					<span class="truncate font-semibold text-gray-900 dark:text-gray-100">
						{post.userDisplayName}
					</span>
					<AccountBadge type={post.page48AccountType} size={13} class="-ml-1 -mr-1" />
					<span class="truncate text-gray-500 dark:text-gray-400">@{post.username}</span>
				</UserHoverCard>
				<span class="shrink-0 text-gray-400">·</span>
				<span class="shrink-0 text-gray-500 dark:text-gray-400">
					{formatPostTime(post.createdAt)}
				</span>
			</div>

			{#if post.content}
				<p
					class="pointer-events-none relative z-[1] mt-1 line-clamp-6 whitespace-pre-wrap break-words text-[14px] leading-relaxed text-gray-700 dark:text-gray-300"
				>
					{#each contentParts as part, i (i)}
						{#if part.tag}
							<a
								href={tagUrl(part.tag, activeMedia)}
								class="pointer-events-auto text-red-500 hover:underline cursor-pointer"
								>{part.text}</a
							>
						{:else if part.mention}
							<UserHoverCard
								username={part.mention}
								href={userUrl(part.mention)}
								class="pointer-events-auto font-semibold text-red-500 hover:underline cursor-pointer"
								>{part.text}</UserHoverCard
							>
						{:else if part.link}
							<a
								href={part.link}
								target="_blank"
								rel="noopener noreferrer nofollow"
								class="pointer-events-auto text-blue-500 hover:underline break-all">{part.text}</a
							>
						{:else}
							{part.text}
						{/if}
					{/each}
				</p>
			{/if}

			<PostPoll {post} {interactive} />

			<PostMedia
				images={post.images ?? []}
				videos={post.videos ?? []}
				bind:index={lightboxIndex}
				onOpen={interactive ? openLightbox : undefined}
			/>
		</div>
	{/if}
</div>

{#if interactive && post && imageUrls.length > 0}
	<div use:portal>
		<PostMediaViewer
			{post}
			initialIndex={lightboxIndex}
			isOpen={lightboxOpen}
			onClose={closeLightbox}
		/>
	</div>
{/if}
