<script lang="ts">
	import { page48Api, type Page48Post } from '$lib/api/page48';
	import { Heart, MessageCircle, Repeat2, Bookmark, Share, Check } from 'lucide-svelte';
	import { OptimizedImage, ImageLightbox } from '$lib/components/common';
	import PostMenu from '$lib/components/page48/PostMenu.svelte';
	import EditPostModal from '$lib/components/page48/EditPostModal.svelte';
	import ConfirmModal from '$lib/components/page48/ConfirmModal.svelte';
	import ReportModal from '$lib/components/page48/ReportModal.svelte';
	import VideoPlayer from '$lib/components/page48/VideoPlayer.svelte';
	import { portal } from '$lib/actions/portal';
	import { page } from '$app/stores';
	import { userProfile } from '$lib/stores/profile.svelte';
	import { isAuthenticated } from '$lib/stores/authStatus.svelte';
	import { showToast } from '$lib/stores/toast.svelte';
	import {
		formatPollRemaining,
		getActiveMedia,
		pollPercentage,
		tagUrl,
		voteOnPoll
	} from '$lib/utils/page48';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	interface Props {
		post: Page48Post;
		isThreadLine?: boolean; // Whether to show the vertical thread line to the next post
		onLike?: (postId: string) => void;
		onRepost?: (postId: string) => void;
		onBookmark?: (postId: string) => void;
		onShare?: (post: Page48Post) => void;
		onComment?: (post: Page48Post) => void;
		onDelete?: (postId: string) => void;
		onUpdated?: (post: Page48Post) => void;
	}

	let {
		post,
		isThreadLine = false,
		onLike,
		onRepost,
		onBookmark,
		onShare,
		onComment,
		onDelete,
		onUpdated
	}: Props = $props();

	let detailHref = $derived(`/page48/post/${post.postId}`);
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

	function openLightbox(index: number) {
		lightboxIndex = index;
		lightboxOpen = true;
	}

	function formatTimeAgo(dateStr: string): string {
		try {
			const now = Date.now();
			const then = new Date(dateStr).getTime();
			const diff = Math.max(0, Math.floor((now - then) / 1000));

			if (diff < 60) return `${diff}${t('page48.time.secondsShort')}`;
			if (diff < 3600) return `${Math.floor(diff / 60)}${t('page48.time.minutesShort')}`;
			if (diff < 86400) return `${Math.floor(diff / 3600)}${t('page48.time.hoursShort')}`;
			if (diff < 2592000) return `${Math.floor(diff / 86400)}${t('page48.time.daysShort')}`;
			if (diff < 31536000) return `${Math.floor(diff / 2592000)}${t('page48.time.monthsShort')}`;
			return `${Math.floor(diff / 31536000)}${t('page48.time.yearsShort')}`;
		} catch {
			return '';
		}
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
	class="relative isolate flex w-full gap-4 pt-5 pb-3 px-5 sm:px-6 hover:bg-black/[0.03] dark:hover:bg-white/[0.03] transition-colors group cursor-pointer"
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

		<!-- Thread Line (if connected to next post) -->
		{#if isThreadLine}
			<div class="w-0.5 grow bg-gray-200/70 dark:bg-zinc-800/70 my-2 min-h-[24px]"></div>
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
						onEdit={() => (showEdit = true)}
						onDelete={() => (showDelete = true)}
						onReport={() => (showReport = true)}
					/>
				{/if}
			</div>
		</div>

		<!-- Post Content (clickable hashtags; rest of the card opens post detail) -->
		{#if post.content}
			<p
				class="relative z-[1] pointer-events-none text-[15px] text-gray-800 dark:text-gray-200 whitespace-pre-wrap mt-0.5 leading-relaxed break-words"
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
		{/if}

		<!-- Extra tags (only those not already shown inline) -->
		{#if extraTags.length > 0}
			<div class="relative z-[1] flex flex-wrap gap-x-2.5 gap-y-1 mt-1.5">
				{#each extraTags as tag (tag)}
					<a
						href={tagUrl(tag, activeMedia)}
						class="text-[14px] font-medium text-red-500 hover:underline cursor-pointer"
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

		<!-- Post Images (Max 4 Grid) — click opens full image lightbox -->
		{#if post.images && post.images.length > 0}
			<div
				class={`relative z-[1] mt-3 grid gap-1.5 rounded-2xl overflow-hidden border border-gray-100 dark:border-white/5 ${
					post.images.length === 1 ? 'grid-cols-1' : 'grid-cols-2'
				}`}
			>
				{#each post.images as image, i (image.filename)}
					<!-- Logic for 3 images: first image takes full width of left col, other two share right col -->
					<button
						type="button"
						class={`relative bg-gray-100 dark:bg-zinc-800 cursor-zoom-in ${post.images.length === 3 && i === 0 ? 'row-span-2' : ''} ${post.images.length === 1 ? 'aspect-auto max-h-[500px]' : 'aspect-square'}`}
						onclick={() => openLightbox(i)}
						aria-label={t('page48.aria.viewImage', { index: i + 1, total: post.images.length })}
					>
						<OptimizedImage
							src={image.url}
							srcMedium={image.url_medium}
							srcSmall={image.url_small}
							blurHash={image.blurHash}
							alt={t('page48.aria.media')}
							class="w-full h-full object-cover"
							objectFit="cover"
						/>
					</button>
				{/each}
			</div>
		{/if}

		<!-- Post Video (single, X/Twitter style: click to play) -->
		{#if post.videos && post.videos.length > 0 && post.videos[0].url}
			<div class="relative z-[1] mt-3">
				<VideoPlayer
					src={post.videos[0].url}
					width={post.videos[0].width}
					height={post.videos[0].height}
					maxHeight={510}
					controls
				/>
			</div>
		{/if}

		<!-- Action Bar -->
		<div
			class="relative z-[1] flex items-center gap-1 -ml-2.5 mt-2.5 w-full justify-between sm:justify-start sm:gap-6 text-gray-500 dark:text-gray-400"
		>
			<!-- Like -->
			<button
				class={`flex items-center gap-1.5 p-2 rounded-full ${actionCursor} hover:bg-red-50 dark:hover:bg-red-950/40 hover:text-red-500 transition-all group/btn`}
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
				class={`flex items-center gap-1.5 p-2 rounded-full ${actionCursor} hover:bg-gray-100 dark:hover:bg-zinc-800/80 hover:text-gray-900 dark:hover:text-gray-200 transition-all group/btn`}
				aria-label={t('page48.aria.comment')}
				aria-disabled={!canInteract}
				onclick={() => interact(() => onComment?.(post))}
			>
				<MessageCircle size={18} class="transition-transform group-active/btn:scale-90" />
				{#if post.replyCount > 0}
					<span class="text-[13px] font-medium">{post.replyCount}</span>
				{/if}
			</button>

			<!-- Repost -->
			<button
				class={`flex items-center gap-1.5 p-2 rounded-full ${actionCursor} hover:bg-green-50 dark:hover:bg-green-950/40 hover:text-green-500 transition-all group/btn`}
				aria-label={t('page48.aria.repost')}
				aria-disabled={!canInteract}
				onclick={() => interact(() => onRepost?.(post.postId))}
			>
				<Repeat2
					size={18}
					class={`transition-transform group-active/btn:scale-90 ${post.isReposted ? 'text-green-500' : ''}`}
				/>
				{#if post.repostCount > 0}
					<span class={`text-[13px] font-medium ${post.isReposted ? 'text-green-500' : ''}`}
						>{post.repostCount}</span
					>
				{/if}
			</button>

			<div class="flex items-center ml-auto sm:ml-0 gap-1 sm:gap-2">
				<!-- Bookmark -->
				<button
					class={`flex items-center gap-1.5 p-2 rounded-full ${actionCursor} hover:bg-blue-50 dark:hover:bg-blue-950/40 hover:text-blue-500 transition-all group/btn`}
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
					class={`flex items-center p-2 rounded-full ${actionCursor} hover:bg-gray-100 dark:hover:bg-zinc-800/80 hover:text-gray-900 dark:hover:text-gray-200 transition-all group/btn`}
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
</article>
