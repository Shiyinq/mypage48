<script lang="ts">
	import { page48Api, type Page48Post } from '$lib/api/page48';
	import { Heart, MessageCircle, Bookmark, Share, Check } from 'lucide-svelte';
	import { OptimizedImage, ImageLightbox } from '$lib/components/common';
	import PostMenu from '$lib/components/page48/PostMenu.svelte';
	import RepostMenu from '$lib/components/page48/RepostMenu.svelte';
	import QuotedPostCard from '$lib/components/page48/QuotedPostCard.svelte';
	import PostComposerModal from '$lib/components/page48/PostComposerModal.svelte';
	import EditPostModal from '$lib/components/page48/EditPostModal.svelte';
	import ConfirmModal from '$lib/components/page48/ConfirmModal.svelte';
	import ReportModal from '$lib/components/page48/ReportModal.svelte';
	import VideoPlayer from '$lib/components/page48/VideoPlayer.svelte';
	import PostImageCarousel from '$lib/components/page48/PostImageCarousel.svelte';
	import { portal } from '$lib/actions/portal';
	import { page } from '$app/stores';
	import { userProfile } from '$lib/stores/profile.svelte';
	import { isAuthenticated } from '$lib/stores/authStatus.svelte';
	import { showToast } from '$lib/stores/toast.svelte';
	import {
		formatPollRemaining,
		formatTimeAgo,
		getActiveMedia,
		imageRatio,
		measureMissingImageSizes,
		pollPercentage,
		tagUrl,
		voteOnPoll
	} from '$lib/utils/page48';
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
		clampContent = true
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
	let imageUrls = $derived(post.images?.map((image) => image.url) ?? []);
	// Keep the active media filter (Gambar/Video) when opening a hashtag.
	let activeMedia = $derived(getActiveMedia($page.url.pathname, $page.url.search));

	let lightboxOpen = $state(false);
	let lightboxIndex = $state(0);

	// A lone photo may not get taller than this; the box is capped by width
	// instead (see below) so its ratio always matches the photo.
	const IMAGE_MAX_HEIGHT = 500;

	// Older posts stored no dimensions; measure the photo in the browser instead.
	$effect(() => {
		if (post.images?.length) return measureMissingImageSizes(post.images);
	});

	let singleImageRatio = $derived(post.images?.length === 1 ? imageRatio(post.images[0]) : 16 / 9);

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

	// Polls: public visitors can look but not vote (options stay disabled), and
	// they get the running result since they can never vote. Signed-in users see
	// the result once they voted or once the poll ended.
	let now = $state(Date.now());
	let pollExpired = $derived(
		!!post.poll && (post.poll.isExpired || new Date(post.poll.endsAt).getTime() <= now)
	);
	let pollRemaining = $derived(post.poll ? formatPollRemaining(post.poll.endsAt, now) : '');
	let canVote = $derived(canInteract && !!post.poll && !pollExpired && !post.poll.myOptionId);
	let showPollResults = $derived(
		!!post.poll && (pollExpired || !canInteract || !!post.poll.myOptionId)
	);

	$effect(() => {
		if (!post.poll || pollExpired) return;
		// Only the countdown label needs to move, once every 10s is plenty.
		const timer = setInterval(() => (now = Date.now()), 10_000);
		return () => clearInterval(timer);
	});

	function handleVote(optionId: string) {
		if (!canVote) return;
		void voteOnPoll(post, optionId);
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

	function openLightbox(index: number) {
		lightboxIndex = index;
		lightboxOpen = true;
	}

	let timeAgo = $derived(formatTimeAgo(post.createdAt));

	function getAvatarUrl(url: string | null) {
		if (!url)
			return `https://ui-avatars.com/api/?name=${encodeURIComponent(post.userDisplayName)}&background=fca5a5&color=fff`;
		return url;
	}

	// Split content into plain text and `#hashtag` segments so hashtags can be
	// rendered as clickable links instead of duplicated tag chips.
	type ContentPart = { text: string; tag?: string };

	function parseContent(content: string): ContentPart[] {
		const parts: ContentPart[] = [];
		const regex = /#([\p{L}\p{N}_]+)/gu;
		let lastIndex = 0;
		let match: RegExpExecArray | null;

		while ((match = regex.exec(content)) !== null) {
			if (match.index > lastIndex) {
				parts.push({ text: content.slice(lastIndex, match.index) });
			}
			parts.push({ text: match[0], tag: match[1].toLowerCase() });
			lastIndex = match.index + match[0].length;
		}

		if (lastIndex < content.length) {
			parts.push({ text: content.slice(lastIndex) });
		}
		return parts;
	}

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
		<a
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
		</a>

		<!-- Thread Line (runs into the card edge so the segments meet) -->
		{#if isThreadLine}
			<div class="w-0.5 grow bg-gray-200/70 dark:bg-zinc-800/70 mt-2 -mb-3 min-h-[24px]"></div>
		{/if}
	</div>

	<!-- Right Column: Content -->
	<div class="flex flex-col flex-1 min-w-0 pt-0.5">
		<!-- Header (Name, Username, Time) -->
		<div class="flex items-center justify-between gap-2 mb-0.5">
			<a
				href={`/page48/u/${post.username}`}
				class="relative z-[1] flex items-center gap-1.5 truncate group/name"
			>
				<span
					class="font-semibold text-[15px] tracking-tight text-gray-900 dark:text-gray-100 group-hover/name:underline truncate"
					>{post.userDisplayName}</span
				>
			</a>
			<div class="relative z-[1] flex items-center gap-2 shrink-0">
				<span class="text-[15px] text-gray-500 hover:underline">{timeAgo}</span>
				{#if isAuthenticated.value}
					<PostMenu
						{isOwner}
						isPinned={post.isPinned}
						onEdit={() => (showEdit = true)}
						onDelete={() => (showDelete = true)}
						onReport={() => (showReport = true)}
						onTogglePin={isOwner && !post.parentPostId ? handleTogglePin : undefined}
					/>
				{/if}
			</div>
		</div>

		<!-- Post Content (clickable hashtags; rest of the card opens post detail) -->
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
		{#if post.poll}
			<div class="relative z-[1] mt-3 flex flex-col gap-1.5">
				{#each post.poll.options as option (option.id)}
					{@const percentage = pollPercentage(option.votes, post.poll.totalVotes)}
					{@const mine = option.id === post.poll.myOptionId}
					<button
						type="button"
						class={`relative isolate w-full overflow-hidden rounded-xl border px-3 py-2 text-left transition-colors ${mine ? 'border-red-400 dark:border-red-500' : 'border-gray-200 dark:border-zinc-700'} ${canVote ? 'cursor-pointer hover:border-red-400 hover:bg-red-50/70 dark:hover:bg-red-950/20' : 'cursor-default'}`}
						onclick={() => handleVote(option.id)}
						aria-disabled={!canVote}
						aria-label={t('page48.poll.voteFor', { option: option.text })}
					>
						{#if showPollResults}
							<span
								class={`absolute inset-y-0 left-0 -z-10 ${mine ? 'bg-red-500/20 dark:bg-red-500/25' : 'bg-gray-200/60 dark:bg-zinc-700/60'}`}
								style={`width:${percentage}%`}
							></span>
						{/if}
						<span class="flex items-center justify-between gap-3">
							<span class="truncate text-[14px] font-medium text-gray-900 dark:text-gray-100">
								{option.text}
							</span>
							{#if showPollResults}
								<span class="flex shrink-0 items-center gap-1.5">
									{#if mine}<Check size={14} class="text-red-500" />{/if}
									<span
										class={`text-[13px] font-semibold tabular-nums ${mine ? 'text-red-500' : 'text-gray-500 dark:text-gray-400'}`}
									>
										{percentage}%
									</span>
								</span>
							{/if}
						</span>
					</button>
				{/each}

				<p class="px-1 text-[13px] text-gray-500 dark:text-gray-400">
					{#if pollExpired}
						{t('page48.poll.ended')}
					{:else}
						{t('page48.poll.endsIn', { time: pollRemaining })}
					{/if}
					· {t('page48.poll.votes', { count: post.poll.totalVotes })}
				</p>
			</div>
		{/if}

		<!-- Post Images: single image inline, several as a swipeable carousel.
		     The wrapper is decoration so the empty margins beside a centered photo
		     still open the card; the media itself opts back in. -->
		{#if post.images && post.images.length > 0}
			<div class="pointer-events-none relative z-[1] mt-3">
				{#if post.images.length === 1}
					{@const image = post.images[0]}
					<!-- Same trick as VideoPlayer: keep the photo's own ratio and cap the box by
					     width, so the photo fills it exactly (no crop, no letterbox bars). -->
					<button
						type="button"
						class="pointer-events-auto relative mx-auto block w-full overflow-hidden rounded-2xl border border-gray-100 bg-gray-100 cursor-zoom-in dark:border-white/5 dark:bg-zinc-800"
						style={`aspect-ratio: ${singleImageRatio}; max-width: min(100%, ${Math.round(
							IMAGE_MAX_HEIGHT * singleImageRatio
						)}px);`}
						onclick={() => openLightbox(0)}
						aria-label={t('page48.aria.viewImage', { index: 1, total: 1 })}
					>
						<OptimizedImage
							src={image.url}
							srcMedium={image.url_medium}
							srcSmall={image.url_small}
							blurHash={image.blurHash}
							alt={t('page48.aria.media')}
							class="w-full h-full object-cover"
							objectFit="cover"
							sizes="(max-width: 640px) 100vw, 600px"
						/>
					</button>
				{:else}
					<div class="pointer-events-auto">
						<PostImageCarousel
							images={post.images}
							bind:index={lightboxIndex}
							onOpen={openLightbox}
						/>
					</div>
				{/if}
			</div>
		{/if}

		<!-- Post Video (single, X/Twitter style: click to play) -->
		{#if post.videos && post.videos.length > 0 && post.videos[0].url}
			<div class="pointer-events-none relative z-[1] mt-3">
				<VideoPlayer
					src={post.videos[0].url}
					width={post.videos[0].width}
					height={post.videos[0].height}
					maxHeight={510}
					controls
					class="pointer-events-auto"
				/>
			</div>
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
				count={post.repostCount}
				cursorClass={actionCursor}
				disabled={!canInteract}
				onRepost={() => interact(() => onRepost?.(post.postId))}
				onQuote={() => interact(openQuote)}
			/>

			<div class="flex items-center ml-auto sm:ml-0 gap-1 sm:gap-2">
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
					<Share size={18} class="transition-transform group-active/btn:scale-90" />
				</button>
			</div>
		</div>
	</div>

	{#if imageUrls.length > 0}
		<div use:portal>
			<ImageLightbox
				images={imageUrls}
				currentIndex={lightboxIndex}
				onIndexChange={(i) => (lightboxIndex = i)}
				isOpen={lightboxOpen}
				onClose={() => (lightboxOpen = false)}
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
