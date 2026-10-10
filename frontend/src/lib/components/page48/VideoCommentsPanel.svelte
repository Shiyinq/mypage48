<script lang="ts">
	import { onMount } from 'svelte';
	import { X, Heart, MessageCircle, CornerDownRight } from 'lucide-svelte';
	import { page48Api, type Page48Post, type ThreadResponse } from '$lib/api/page48';
	import { page48Reads } from '$lib/stores/page48.svelte';
	import PostComposer from '$lib/components/page48/PostComposer.svelte';
	import AccountBadge from '$lib/components/page48/AccountBadge.svelte';
	import Page48Spinner from '$lib/components/page48/Page48Spinner.svelte';
	import ErrorState from '$lib/components/ErrorState.svelte';
	import { isAuthenticated } from '$lib/stores/authStatus.svelte';
	import { showToast } from '$lib/stores/toast.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import {
		formatPostTime,
		parseContent,
		tagUrl,
		userUrl,
		togglePostInteraction,
		uploadPage48Images,
		uploadPage48Video,
		type MentionCandidate,
		type VideoDraft
	} from '$lib/utils/page48';

	interface Props {
		/** The video post whose comments are shown. Changing it reloads the panel. */
		post: Page48Post;
		onClose: () => void;
		/** Fired after a comment is published so the host can bump its reply count. */
		onReplyAdded?: (postId: string, delta: number) => void;
	}

	let { post, onClose, onReplyAdded }: Props = $props();

	const { t } = useTranslation();

	let loading = $state(true);
	let error = $state<string | null>(null);
	/** Every reply in the thread, flattened in reading order, each with its depth. */
	let replies = $state<{ post: Page48Post; depth: number }[]>([]);
	/** The comment the composer answers; defaults to the video post itself. */
	let replyTarget = $state<Page48Post | null>(null);
	/** Cap the indent so deep threads never squeeze the text into a sliver. */
	const MAX_INDENT = 2;

	// Which presentation to use: bottom drawer below the `sm` breakpoint, floating
	// panel above it. Detected on mount so SSR renders the desktop layout.
	let isMobile = $state(true);

	// Drag-to-dismiss state for the mobile drawer.
	let dragY = $state(0);
	let dragging = $state(false);
	let pointerStart = 0;
	const DISMISS_THRESHOLD = 110;

	onMount(() => {
		const mq = window.matchMedia('(max-width: 639px)');
		const update = () => (isMobile = mq.matches);
		update();
		mq.addEventListener('change', update);
		return () => mq.removeEventListener('change', update);
	});

	// Reload whenever the focused video changes: the host reuses this component as
	// the viewer scrolls, so `post.postId` is the source of truth.
	$effect(() => {
		void load(post.postId);
	});

	let canInteract = $derived(isAuthenticated.value);

	let mentionCandidates = $derived.by<MentionCandidate[]>(() => {
		const seen = new Set<string>();
		const items: MentionCandidate[] = [];

		for (const item of [post, ...replies.map((r) => r.post)]) {
			const handle = item.username.toLowerCase();
			if (seen.has(handle)) continue;
			seen.add(handle);
			items.push({
				username: item.username,
				name: item.userDisplayName,
				profilePicture: item.userProfilePicture_small ?? item.userProfilePicture
			});
		}

		return items;
	});

	async function load(id: string) {
		try {
			loading = true;
			error = null;
			replyTarget = null;
			const thread = await page48Reads.getThread(id);
			replies = flatten(thread.replies, 0);
		} catch (err: unknown) {
			const e = err as { message?: string };
			error = e?.message || t('page48.post.loadError');
		} finally {
			loading = false;
		}
	}

	function flatten(nodes: ThreadResponse[], depth: number): { post: Page48Post; depth: number }[] {
		const out: { post: Page48Post; depth: number }[] = [];
		for (const node of nodes) {
			out.push({ post: node.post, depth });
			out.push(...flatten(node.replies, depth + 1));
		}
		return out;
	}

	async function handleLike(comment: Page48Post) {
		if (!canInteract) return;
		await togglePostInteraction(comment, 'like');
	}

	function startReply(comment: Page48Post) {
		if (!canInteract) return;
		replyTarget = comment;
	}

	function cancelReply() {
		replyTarget = null;
	}

	async function handleReply(
		content: string,
		files: File[],
		video: VideoDraft | null,
		poll: { options: string[] } | null,
		quotedPostId: string | null
	) {
		const target = replyTarget ?? post;
		try {
			const images = files.length > 0 ? await uploadPage48Images(files) : [];
			const videos = video ? [await uploadPage48Video(video)] : [];
			// Replies can't carry a poll (server rule), so `poll` is always null here.
			const created = await page48Api.createPost(
				content,
				images,
				videos,
				target.postId,
				poll,
				quotedPostId ?? undefined
			);
			showToast(t('page48.post.replySent'), 'success');
			// The server only bumps the direct parent's replyCount.
			target.replyCount += 1;
			if (target.postId === post.postId) onReplyAdded?.(post.postId, 1);
			const targetDepth = replies.find((r) => r.post.postId === target.postId)?.depth ?? -1;
			replies = [...replies, { post: created, depth: targetDepth + 1 }];
			replyTarget = null;
		} catch (err: unknown) {
			const e = err as { message?: string };
			showToast(e?.message || t('page48.post.replyError'), 'error');
			throw err;
		}
	}

	// --- Mobile swipe-to-dismiss ---------------------------------------------

	function onPointerDown(event: PointerEvent) {
		if (!isMobile) return;
		dragging = true;
		pointerStart = event.clientY;
		(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId);
	}

	function onPointerMove(event: PointerEvent) {
		if (!dragging) return;
		dragY = Math.max(0, event.clientY - pointerStart);
	}

	function onPointerUp(event: PointerEvent) {
		if (!dragging) return;
		dragging = false;
		const el = event.currentTarget as HTMLElement;
		if (el.hasPointerCapture(event.pointerId)) el.releasePointerCapture(event.pointerId);
		if (dragY > DISMISS_THRESHOLD) {
			closeSheet();
		} else {
			dragY = 0;
		}
	}

	/** Animate the drawer off-screen before the host unmounts it. */
	function closeSheet() {
		dragY = typeof window !== 'undefined' ? window.innerHeight : 600;
		setTimeout(onClose, 200);
	}

	function requestClose() {
		if (isMobile) closeSheet();
		else onClose();
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') requestClose();
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#snippet body()}
	<!-- Header -->
	<div class="relative flex shrink-0 flex-col border-b border-gray-200/70 dark:border-white/10">
		{#if isMobile}
			<button
				type="button"
				class="flex h-6 w-full touch-none items-center justify-center"
				onpointerdown={onPointerDown}
				onpointermove={onPointerMove}
				onpointerup={onPointerUp}
				onpointercancel={onPointerUp}
				aria-label={t('common.close')}
			>
				<span class="h-1 w-10 rounded-full bg-gray-300 dark:bg-zinc-700"></span>
			</button>
		{/if}
		<div class="relative flex items-center justify-center px-4 pb-3 pt-1">
			<h2 class="text-[15px] font-bold text-gray-900 dark:text-gray-100">
				{t('page48.video.commentsTitle')}
				{#if post.replyCount > 0}
					<span class="ml-1 font-medium text-gray-400 dark:text-gray-500">{post.replyCount}</span>
				{/if}
			</h2>
			<button
				type="button"
				class="absolute right-2 top-1/2 flex h-8 w-8 -translate-y-1/2 cursor-pointer items-center justify-center rounded-full text-gray-500 transition-colors hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-zinc-800"
				onclick={requestClose}
				aria-label={t('common.close')}
			>
				<X size={18} />
			</button>
		</div>
	</div>

	<!-- Comment list -->
	<div class="min-h-0 flex-1 overflow-y-auto overscroll-contain">
		{#if loading}
			<div class="flex h-40 items-center justify-center">
				<Page48Spinner class="h-[24px] w-[24px]" />
			</div>
		{:else if error}
			<div class="p-5">
				<ErrorState
					title={t('page48.post.loadError')}
					description={error}
					onRetry={() => load(post.postId)}
				/>
			</div>
		{:else if replies.length === 0}
			<div class="flex h-40 flex-col items-center justify-center gap-2 px-6 text-center">
				<MessageCircle size={26} class="text-gray-300 dark:text-zinc-700" />
				<p class="text-[13px] text-gray-400 dark:text-gray-500">
					{t('page48.video.commentsEmpty')}
				</p>
			</div>
		{:else}
			{#each replies as item (item.post.postId)}
				{@const comment = item.post}
				<div
					class="flex gap-3 px-4 py-3"
					style:margin-left={`${Math.min(item.depth, MAX_INDENT) * 20}px`}
				>
					<a
						href={userUrl(comment.username)}
						class="h-9 w-9 shrink-0 overflow-hidden rounded-full bg-gray-100 ring-1 ring-black/5 dark:bg-zinc-800 dark:ring-white/10"
						aria-label={t('page48.aria.profile')}
					>
						<img
							src={comment.userProfilePicture_small ??
								comment.userProfilePicture ??
								`https://ui-avatars.com/api/?name=${encodeURIComponent(comment.userDisplayName)}&background=fca5a5&color=fff`}
							alt={comment.username}
							class="h-full w-full object-cover"
						/>
					</a>

					<div class="min-w-0 flex-1">
						<div class="flex min-w-0 items-center gap-1.5">
							<span class="truncate text-[13px] font-semibold text-gray-900 dark:text-gray-100">
								{comment.userDisplayName}
							</span>
							<AccountBadge type={comment.page48AccountType} size={13} class="-ml-1 -mr-1" />
							<span class="truncate text-[12px] text-gray-500 dark:text-gray-400">
								@{comment.username}
							</span>
							<span class="shrink-0 text-[12px] text-gray-400 dark:text-gray-500">
								· {formatPostTime(comment.createdAt)}
							</span>
						</div>

						{#if comment.content}
							<p
								class="mt-0.5 text-[14px] leading-snug break-words whitespace-pre-wrap text-gray-800 dark:text-gray-200"
							>
								{#each parseContent(comment.content) as part, i (i)}
									{#if part.tag}
										<a href={tagUrl(part.tag)} class="cursor-pointer text-red-500 hover:underline"
											>{part.text}</a
										>
									{:else if part.mention}
										<a
											href={userUrl(part.mention)}
											class="cursor-pointer font-semibold text-red-500 hover:underline"
											>{part.text}</a
										>
									{:else if part.link}
										<a
											href={part.link}
											target="_blank"
											rel="noopener noreferrer nofollow"
											class="break-all text-blue-500 hover:underline">{part.text}</a
										>
									{:else}
										{part.text}
									{/if}
								{/each}
							</p>
						{/if}

						<div class="mt-1.5 flex items-center gap-4 text-gray-500 dark:text-gray-400">
							<button
								type="button"
								class="flex cursor-pointer items-center gap-1 text-[12px] font-semibold transition-colors hover:text-gray-700 dark:hover:text-gray-200"
								onclick={() => startReply(comment)}
								aria-label={t('page48.aria.comment')}
							>
								<CornerDownRight size={15} />
								{t('page48.video.commentReply')}
							</button>
							<button
								type="button"
								class="flex cursor-pointer items-center gap-1 text-[12px] font-semibold transition-colors hover:text-red-500"
								onclick={() => handleLike(comment)}
								aria-label={t('page48.aria.like')}
								aria-disabled={!canInteract}
							>
								<Heart size={15} class={comment.isLiked ? 'fill-red-500 text-red-500' : ''} />
								{#if comment.likesCount > 0}
									<span class={comment.isLiked ? 'text-red-500' : ''}>{comment.likesCount}</span>
								{/if}
							</button>
						</div>
					</div>
				</div>
			{/each}
		{/if}
	</div>

	<!-- Composer -->
	<div class="shrink-0 border-t border-gray-200/70 dark:border-white/10">
		{#if canInteract}
			{#if replyTarget}
				<div class="flex items-center justify-between px-5 pt-3 sm:px-6">
					<span class="text-[13px] text-gray-500 dark:text-gray-400">
						{t('page48.post.replyingTo')}
						<span class="font-semibold text-red-500">@{replyTarget.username}</span>
					</span>
					<button
						type="button"
						class="cursor-pointer rounded-full p-1 text-gray-400 hover:bg-gray-100 dark:hover:bg-zinc-800"
						onclick={cancelReply}
						aria-label={t('page48.aria.cancelReply')}
					>
						<X size={16} />
					</button>
				</div>
			{/if}
			<PostComposer
				isReply
				placeholder={t('page48.composer.replyPlaceholder', {
					username: (replyTarget ?? post).username
				})}
				onPost={handleReply}
				{mentionCandidates}
			/>
		{:else}
			<div class="p-4">
				<a
					href="/login"
					class="block rounded-full bg-red-600 px-5 py-2.5 text-center text-[13px] font-semibold text-white transition-colors hover:bg-red-700"
				>
					{t('page48.video.commentsSignIn')}
				</a>
			</div>
		{/if}
	</div>
{/snippet}

{#if isMobile}
	<!-- Mobile: bottom drawer, dismissed by swiping down or the close button -->
	<div class="fixed inset-0 z-[70] sm:hidden">
		<button
			type="button"
			class="absolute inset-0 cursor-pointer bg-black/40 backdrop-blur-[2px]"
			style:opacity={Math.max(0, 1 - dragY / 400)}
			onclick={requestClose}
			aria-label={t('common.close')}
		></button>
		<div
			class={`absolute bottom-0 left-0 right-0 flex max-h-[82dvh] flex-col overflow-hidden rounded-t-2xl border-t border-gray-200/70 bg-white shadow-[0_-8px_40px_rgba(0,0,0,0.25)] dark:border-white/10 dark:bg-zinc-900 ${dragging ? '' : 'transition-transform duration-200 ease-out'}`}
			style:transform={`translateY(${dragY}px)`}
			role="dialog"
			aria-modal="true"
			aria-label={t('page48.video.commentsTitle')}
		>
			{@render body()}
		</div>
	</div>
{:else}
	<!-- Desktop: floating panel on the right, TikTok-style -->
	<div
		class="fixed bottom-20 right-4 top-4 z-[60] flex w-[400px] max-w-[calc(100vw-2rem)] flex-col overflow-hidden rounded-2xl border border-gray-200/70 bg-white/95 shadow-2xl shadow-black/20 backdrop-blur-xl xl:bottom-4 xl:top-20 dark:border-white/10 dark:bg-zinc-900/95"
		role="dialog"
		aria-label={t('page48.video.commentsTitle')}
	>
		{@render body()}
	</div>
{/if}
