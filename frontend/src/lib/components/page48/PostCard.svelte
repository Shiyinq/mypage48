<script lang="ts">
	import { page48Api, type Page48Post } from '$lib/api/page48';
	import { Heart, MessageCircle, Bookmark, Share2 } from 'lucide-svelte';
	import PostMenu from '$lib/components/page48/PostMenu.svelte';
	import UserHoverCard from '$lib/components/page48/UserHoverCard.svelte';
	import RepostMenu from '$lib/components/page48/RepostMenu.svelte';
	import QuotedPostCard from '$lib/components/page48/QuotedPostCard.svelte';
	import PostComposerModal from '$lib/components/page48/PostComposerModal.svelte';
	import PostMediaViewer from '$lib/components/page48/PostMediaViewer.svelte';
	import PostMedia from '$lib/components/page48/PostMedia.svelte';
	import PostPoll from '$lib/components/page48/PostPoll.svelte';
	import EditPostModal from '$lib/components/page48/EditPostModal.svelte';
	import ConfirmModal from '$lib/components/page48/ConfirmModal.svelte';
	import ReportModal from '$lib/components/page48/ReportModal.svelte';
	import { portal } from '$lib/actions/portal';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { userProfile } from '$lib/stores/profile.svelte';
	import { activityNavStore } from '$lib/stores/page48Nav.svelte';
	import { isAuthenticated } from '$lib/stores/authStatus.svelte';
	import { showToast } from '$lib/stores/toast.svelte';
	import { formatPostTime, getActiveMedia, parseContent, tagUrl, userUrl } from '$lib/utils/page48';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	interface Props {
		post: Page48Post;
		isThreadLine?: boolean; // Whether to show the vertical thread line to the next post
		/** A continuation of the post above (same author): no header, flush top. */
		isContinuation?: boolean;
		/** Position inside a chain, rendered as a subtle "2/4" marker. */
		threadPosition?: { index: number; total: number };
		/** Hide the "Show this thread" link (e.g. on the detail page, where it is already shown). */
		showThreadLink?: boolean;
		onLike?: (postId: string) => void;
		onRepost?: (postId: string) => void;
		onBookmark?: (postId: string) => void;
		onShare?: (post: Page48Post) => void;
		onComment?: (post: Page48Post) => void;
		onDelete?: (postId: string) => void;
		onUpdated?: (post: Page48Post) => void;
		/** Fired after the pin state changed, so a profile list can re-sort itself. */
		onPinChanged?: (post: Page48Post) => void;
		/** Collapse long text behind a "show more" toggle (lists pass this; the detail page does not). */
		clampContent?: boolean;
		/** Show a "View activity" link under the action bar (used on the detail page). */
		showActivityLink?: boolean;
		/** Hide the post's own photo/video (used when the media is shown beside it). */
		hideMedia?: boolean;
		/** Show the exact time and date instead of the relative/short timestamp. */
		fullTimestamp?: boolean;
	}

	let {
		post,
		isThreadLine = false,
		isContinuation = false,
		threadPosition = undefined,
		showThreadLink = true,
		onLike,
		onRepost,
		onBookmark,
		onShare,
		onComment,
		onDelete,
		onUpdated,
		onPinChanged,
		clampContent = true,
		showActivityLink = false,
		hideMedia = false,
		fullTimestamp = false
	}: Props = $props();

	// Long posts would stretch a feed row, so the text is clamped and a red "show more"
	// toggle is offered whenever it does not fit. Capped at half the height of the tallest
	// single photo (a 9/16 portrait, see IMAGE_MAX_HEIGHT) so text stays photo-sized.
	const CONTENT_CLAMP_PX = 250;

	let contentEl = $state<HTMLParagraphElement>();
	let contentExpanded = $state(false);
	let contentOverflows = $state(false);

	// Compare the natural text height against the clamp. Reading `post.content` keeps
	// this in sync when the post is edited or replaced.
	$effect(() => {
		const el = contentEl;
		void post.content;
		if (!el) {
			contentOverflows = false;
			return;
		}
		contentOverflows = el.scrollHeight > CONTENT_CLAMP_PX + 1;
	});

	// Re-measure whenever the text box changes size (window resize, rotation), otherwise a
	// post could stay collapsed — or unclamped — after its available width changed.
	$effect(() => {
		if (!clampContent) return;
		const el = contentEl;
		if (!el) return;

		const observer = new ResizeObserver(() => {
			contentOverflows = el.scrollHeight > CONTENT_CLAMP_PX + 1;
		});
		observer.observe(el);
		return () => observer.disconnect();
	});

	let showClamp = $derived(clampContent && contentOverflows && !contentExpanded);
	let showContentToggle = $derived(clampContent && contentOverflows);

	function toggleContent() {
		contentExpanded = !contentExpanded;
	}

	let detailHref = $derived(`/page48/post/${post.postId}`);
	let activityHref = $derived(`${detailHref}/activity`);
	let imageUrls = $derived(post.images?.map((image) => image.url) ?? []);
	// Keep the active media filter (Gambar/Video) when opening a hashtag.
	let activeMedia = $derived(getActiveMedia($page.url.pathname, $page.url.search));

	let lightboxOpen = $state(false);
	let lightboxIndex = $state(0);

	// Show the owner menu (Edit/Delete) only for the signed-in author.
	let isOwner = $derived(
		!!userProfile.data &&
			(userProfile.data.userId
				? userProfile.data.userId === post.userId
				: userProfile.data.username === post.username)
	);

	let showEdit = $state(false);
	let showDelete = $state(false);
	let showReport = $state(false);
	let deleting = $state(false);

	// Public (unauthenticated) visitors can look but not interact. Hover styling
	// (background/text colour) still applies, only the click action is blocked.
	let canInteract = $derived(isAuthenticated.value);
	let actionCursor = $derived(canInteract ? 'cursor-pointer' : 'cursor-default');

	function interact(fn: () => void) {
		if (canInteract) fn();
	}

	function handleEditSaved(updated: Page48Post) {
		post.content = updated.content;
		post.tags = updated.tags;
		post.isEdited = updated.isEdited;
		post.updatedAt = updated.updatedAt;
		onUpdated?.(post);
	}

	async function handleDelete() {
		if (deleting) return;
		deleting = true;
		try {
			await page48Api.deletePost(post.postId);
			showToast(t('page48.delete.success'), 'success');
			showDelete = false;
			onDelete?.(post.postId);
		} catch (err: unknown) {
			const e = err as { detail?: string; message?: string };
			showToast(e?.detail || e?.message || t('page48.delete.error'), 'error');
		} finally {
			deleting = false;
		}
	}

	// Pinning is owner-only and one per user: pinning another post replaces this
	// one on the server, so the list is told to re-sort via `onUpdated`.
	let pinning = $state(false);

	async function handleTogglePin() {
		if (pinning) return;
		pinning = true;
		try {
			const updated = post.isPinned
				? await page48Api.unpinPost(post.postId)
				: await page48Api.pinPost(post.postId);
			post.isPinned = updated.isPinned;
			showToast(updated.isPinned ? t('page48.pin.pinned') : t('page48.pin.unpinned'), 'success');
			onPinChanged?.(post);
		} catch (err: unknown) {
			const e = err as { detail?: string; message?: string };
			showToast(e?.detail || e?.message || t('page48.pin.error'), 'error');
		} finally {
			pinning = false;
		}
	}

	// Quoting reuses the shared composer in a modal, prefilled with this post.
	let showQuote = $state(false);
	let quoteTarget = $state<Page48Post | null>(null);

	function openQuote() {
		quoteTarget = post;
		showQuote = true;
	}

	function openActivity() {
		activityNavStore.fromList = !showActivityLink;
		void goto(activityHref);
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

	// While a photo is open the address bar shows the post's detail URL, exactly
	// like the detail page, so the link can be copied or shared from here. The
	// previous URL is put back when the viewer closes.
	let viewerReturnUrl: string | null = null;

	function pushViewerUrl() {
		if (typeof window === 'undefined') return;
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

	let timeLabel = $derived(formatPostTime(post.createdAt, fullTimestamp));
	// Shown as a hover tooltip, so lists still say "3j" while the exact time stays reachable.
	let exactTime = $derived(formatPostTime(post.createdAt, true));

	function getAvatarUrl(url: string | null) {
		if (!url)
			return `https://ui-avatars.com/api/?name=${encodeURIComponent(post.userDisplayName)}&background=fca5a5&color=fff`;
		return url;
	}

	// Hashtags and mentions inside the content, so neither needs a duplicated chip.
	let contentParts = $derived(post.content ? parseContent(post.content) : []);
	let inlineTags = $derived(
		new Set(contentParts.filter((part) => part.tag).map((part) => part.tag as string))
	);
	// Only show extra chips for tags that are not already visible in the content.
	let extraTags = $derived((post.tags ?? []).filter((tag) => !inlineTags.has(tag)));
</script>

<article
	class={`relative isolate flex w-full gap-4 ${isContinuation ? 'pt-0' : 'pt-5'} pb-3 px-5 sm:px-6 hover:bg-black/[0.03] dark:hover:bg-white/[0.03] transition-colors group cursor-pointer`}
>
	<!-- Full-card click target: opens the post detail. Interactive children sit above it. -->
	<a href={detailHref} class="absolute inset-0 z-0" aria-label={t('page48.aria.openPost')}></a>

	<!-- Left Column: Avatar & Thread Line -->
	<div class="flex flex-col items-center shrink-0">
		<!-- Avatar -->
		<UserHoverCard
			username={post.username}
			href={`/page48/u/${post.username}`}
			class="relative block w-11 h-11 rounded-full overflow-hidden bg-gray-100 dark:bg-zinc-800 shrink-0 z-10 ring-2 ring-white dark:ring-zinc-950 shadow-sm transition-transform hover:scale-105"
		>
			<img
				src={getAvatarUrl(post.userProfilePicture_small || post.userProfilePicture)}
				alt={post.username}
				class="w-full h-full object-cover"
				onerror={(e) => {
					(e.target as HTMLImageElement).src =
						`https://ui-avatars.com/api/?name=${encodeURIComponent(post.userDisplayName)}&background=fca5a5&color=fff`;
				}}
			/>
		</UserHoverCard>

		<!-- Thread Line (runs into the card edge so the segments meet) -->
		{#if isThreadLine}
			<div class="w-0.5 grow bg-gray-200/70 dark:bg-zinc-800/70 mt-2 -mb-3 min-h-[24px]"></div>
		{/if}
	</div>

	<!-- Right Column: Content -->
	<div class="flex flex-col flex-1 min-w-0 pt-0.5">
		<!-- Header (Name, Username, Time) -->
		<div class="flex items-center justify-between gap-2 mb-0.5">
			<UserHoverCard
				username={post.username}
				href={`/page48/u/${post.username}`}
				class="relative z-[1] min-w-0 flex items-center gap-1.5 truncate group/name"
			>
				<span
					class="font-semibold text-[15px] tracking-tight text-gray-900 dark:text-gray-100 group-hover/name:underline truncate"
					>{post.userDisplayName}</span
				>
				<span class="truncate text-[14px] text-gray-500 dark:text-gray-400">@{post.username}</span>
			</UserHoverCard>
			<div class="relative z-[1] flex items-center gap-2 shrink-0">
				<span class="group/time relative text-[15px] text-gray-500 hover:underline">
					{timeLabel}
					{#if !fullTimestamp}
						<span
							aria-hidden="true"
							class="pointer-events-none absolute right-0 bottom-full z-20 mb-2 px-2 py-1 text-[11px] font-medium text-white whitespace-nowrap rounded-lg bg-gray-900 border border-white/10 opacity-0 shadow-xl transition-all group-hover/time:opacity-100 dark:bg-zinc-800"
						>
							{exactTime}
						</span>
					{/if}
				</span>
				{#if isAuthenticated.value}
					<PostMenu
						{isOwner}
						isPinned={post.isPinned}
						onEdit={() => (showEdit = true)}
						onDelete={() => (showDelete = true)}
						onReport={() => (showReport = true)}
						onTogglePin={isOwner && !post.parentPostId ? handleTogglePin : undefined}
						onViewActivity={openActivity}
					/>
				{/if}
			</div>
		</div>

		<!-- Post Content (clickable hashtags and mentions; rest of the card opens
		     post detail) -->
		{#if post.content}
			<p
				bind:this={contentEl}
				class={`relative z-[1] pointer-events-none text-[15px] text-gray-800 dark:text-gray-200 whitespace-pre-wrap mt-0.5 leading-relaxed break-words ${showClamp ? 'max-h-[250px] overflow-hidden' : ''}`}
			>
				{#each contentParts as part, i (i)}
					{#if part.tag}
						<a
							href={tagUrl(part.tag, activeMedia)}
							class="pointer-events-auto text-red-500 hover:underline cursor-pointer">{part.text}</a
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

			{#if showContentToggle}
				<button
					type="button"
					class="relative z-[1] self-start mt-1 text-[14px] font-semibold text-red-500 hover:text-red-600 dark:text-red-400 dark:hover:text-red-300 cursor-pointer"
					onclick={toggleContent}
				>
					{contentExpanded ? t('page48.post.showLess') : t('page48.post.showMore')}
				</button>
			{/if}
		{/if}

		<!-- Thread position: kept below the last line of the text, like Threads.
		     The chip is decoration, so it must not swallow clicks meant for the card. -->
		{#if threadPosition}
			<div class="pointer-events-none relative z-[1] mt-1.5 flex">
				<span
					class="rounded-md border border-gray-200 px-1.5 py-0.5 text-[12px] font-medium tabular-nums text-gray-500 dark:border-zinc-700 dark:text-gray-400"
				>
					{threadPosition.index + 1}/{threadPosition.total}
				</span>
			</div>
		{/if}

		<!-- Extra tags (only those not already shown inline) -->
		{#if extraTags.length > 0}
			<div class="pointer-events-none relative z-[1] flex flex-wrap gap-x-2.5 gap-y-1 mt-1.5">
				{#each extraTags as tag (tag)}
					<a
						href={tagUrl(tag, activeMedia)}
						class="pointer-events-auto text-[14px] font-medium text-red-500 hover:underline cursor-pointer"
					>
						#{tag}
					</a>
				{/each}
			</div>
		{/if}

		<!-- Poll -->
		<PostPoll {post} />

		<!-- Post media: photos (one inline, several as a carousel) and video -->
		{#if !hideMedia}
			<PostMedia
				images={post.images ?? []}
				videos={post.videos ?? []}
				bind:index={lightboxIndex}
				onOpen={openLightbox}
			/>
		{/if}

		<!-- Quoted post preview -->
		{#if post.quotedPostId}
			<div class="pointer-events-auto relative z-[1]">
				<QuotedPostCard post={post.quotedPost ?? null} unavailable={!post.quotedPost} />
			</div>
		{/if}

		<!-- Thread continuation: opens the detail page where the chain is shown -->
		{#if showThreadLink && post.threadCount > 0}
			<a
				href={detailHref}
				class="relative z-[1] mt-2 inline-block text-[13px] font-semibold text-red-500 hover:underline cursor-pointer"
			>
				{t('page48.thread.show', { count: post.threadCount })}
			</a>
		{/if}

		<!-- Action Bar: the row itself is decoration, so clicks fall through to the card;
		     each button opts back in with pointer-events-auto. -->
		<div
			class="pointer-events-none relative z-[1] flex items-center gap-1 -ml-2.5 mt-2.5 w-full justify-between sm:justify-start sm:gap-6 text-gray-500 dark:text-gray-400"
		>
			<!-- Like -->
			<button
				class={`pointer-events-auto flex items-center gap-1.5 p-2 rounded-full ${actionCursor} hover:bg-red-50 dark:hover:bg-red-950/40 hover:text-red-500 transition-all group/btn`}
				aria-label={t('page48.aria.like')}
				aria-disabled={!canInteract}
				onclick={() => interact(() => onLike?.(post.postId))}
			>
				<Heart
					size={18}
					class={`transition-transform group-active/btn:scale-90 ${post.isLiked ? 'fill-red-500 text-red-500' : ''}`}
				/>
				{#if post.likesCount > 0}
					<span class={`text-[13px] font-medium ${post.isLiked ? 'text-red-500' : ''}`}
						>{post.likesCount}</span
					>
				{/if}
			</button>

			<!-- Comment -->
			<button
				class={`pointer-events-auto flex items-center gap-1.5 p-2 rounded-full ${actionCursor} hover:bg-gray-100 dark:hover:bg-zinc-800/80 hover:text-gray-900 dark:hover:text-gray-200 transition-all group/btn`}
				aria-label={t('page48.aria.comment')}
				aria-disabled={!canInteract}
				onclick={() => interact(() => onComment?.(post))}
			>
				<MessageCircle size={18} class="transition-transform group-active/btn:scale-90" />
				{#if post.replyCount > 0}
					<span class="text-[13px] font-medium">{post.replyCount}</span>
				{/if}
			</button>

			<!-- Repost / Quote -->
			<RepostMenu
				isReposted={post.isReposted}
				count={post.repostCount + post.quoteCount}
				cursorClass={actionCursor}
				disabled={!canInteract}
				onRepost={() => interact(() => onRepost?.(post.postId))}
				onQuote={() => interact(openQuote)}
			/>

			<div class={`flex items-center gap-1 sm:gap-2 ${showActivityLink ? '' : 'ml-auto sm:ml-0'}`}>
				<!-- Bookmark -->
				<button
					class={`pointer-events-auto flex items-center gap-1.5 p-2 rounded-full ${actionCursor} hover:bg-blue-50 dark:hover:bg-blue-950/40 hover:text-blue-500 transition-all group/btn`}
					aria-label={t('page48.aria.bookmark')}
					aria-disabled={!canInteract}
					onclick={() => interact(() => onBookmark?.(post.postId))}
				>
					<Bookmark
						size={18}
						class={`transition-transform group-active/btn:scale-90 ${
							post.isBookmarked ? 'fill-blue-500 text-blue-500' : ''
						}`}
					/>
				</button>

				<!-- Share -->
				<button
					class={`pointer-events-auto flex items-center p-2 rounded-full ${actionCursor} hover:bg-gray-100 dark:hover:bg-zinc-800/80 hover:text-gray-900 dark:hover:text-gray-200 transition-all group/btn`}
					aria-label={t('page48.aria.share')}
					aria-disabled={!canInteract}
					onclick={() => interact(() => onShare?.(post))}
				>
					<Share2 size={18} class="transition-transform group-active/btn:scale-90" />
				</button>
			</div>

			{#if showActivityLink}
				<a
					href={activityHref}
					class="pointer-events-auto ml-auto cursor-pointer text-[13px] font-semibold text-red-500 hover:underline"
				>
					{t('page48.activity.view')}
				</a>
			{/if}
		</div>
	</div>

	{#if !hideMedia && imageUrls.length > 0}
		<div use:portal>
			<PostMediaViewer
				{post}
				initialIndex={lightboxIndex}
				isOpen={lightboxOpen}
				onClose={closeLightbox}
			/>
		</div>
	{/if}

	{#if showEdit}
		<EditPostModal {post} onClose={() => (showEdit = false)} onSaved={handleEditSaved} />
	{/if}

	{#if showDelete}
		<ConfirmModal
			title={t('page48.delete.title')}
			message={t('page48.delete.message')}
			confirmText={t('page48.delete.confirm')}
			destructive
			onCancel={() => (showDelete = false)}
			onConfirm={handleDelete}
		/>
	{/if}

	{#if showReport}
		<ReportModal targetType="post" targetId={post.postId} onClose={() => (showReport = false)} />
	{/if}

	{#if showQuote}
		<PostComposerModal
			quotedPost={quoteTarget}
			onRemoveQuote={() => (quoteTarget = null)}
			onClose={() => (showQuote = false)}
		/>
	{/if}
</article>
