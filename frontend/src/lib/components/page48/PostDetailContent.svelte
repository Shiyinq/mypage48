<script lang="ts">
	import { goto } from '$app/navigation';
	import { fade } from 'svelte/transition';
	import { X } from 'lucide-svelte';
	import { page48Api, type Page48Post, type ThreadResponse } from '$lib/api/page48';
	import PostCard from '$lib/components/page48/PostCard.svelte';
	import PostComposer from '$lib/components/page48/PostComposer.svelte';
	import { ErrorState } from '$lib/components';
	import { isAuthenticated } from '$lib/stores/authStatus.svelte';
	import { showToast } from '$lib/stores/toast.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import {
		sharePost,
		togglePostInteraction,
		uploadPage48Images,
		uploadPage48Video,
		type MentionCandidate,
		type Page48Interaction,
		type VideoDraft
	} from '$lib/utils/page48';

	interface Props {
		postId: string;
		/**
		 * Hide the focused post's own photo/video. Used by the media viewer, where
		 * the photo is already shown beside this pane.
		 */
		hideMedia?: boolean;
		/** Called after the focused post was deleted, so the host can navigate away. */
		onDeleted?: () => void;
		/** The focused post, exposed so the host can build SEO tags from it. */
		focused?: Page48Post | null;
	}

	let { postId, hideMedia = false, onDeleted, focused = $bindable(null) }: Props = $props();

	const { t } = useTranslation();

	let loading = $state(true);
	let error = $state<string | null>(null);
	/** The focused post plus the author's own continuations — rendered connected. */
	let chain = $state<Page48Post[]>([]);
	/** Absolute position of `chain[0]` in the author's thread, and the thread's total size. */
	let chainStart = $state(0);
	let chainTotal = $state(0);
	/** The post the focused one replies to, shown above it for context. */
	let parentContext = $state<Page48Post | null>(null);
	/** Direct replies, each keeping its own replies nested (like a thread). */
	let replyTree = $state<ThreadResponse[]>([]);
	/** Flat view of `replyTree`, used for lookups and the emptiness check. */
	let replies = $derived(flattenReplies(replyTree));
	// The post the composer currently replies to (defaults to the focused post).
	let replyTarget = $state<Page48Post | null>(null);

	/**
	 * Users offered after an `@` in the reply composer: the post being viewed plus
	 * everyone who commented on it, deduped.
	 */
	let mentionCandidates = $derived.by<MentionCandidate[]>(() => {
		const seen = new Set<string>();
		const items: MentionCandidate[] = [];

		for (const post of [focused, parentContext, ...chain, ...replies]) {
			if (!post) continue;
			const handle = post.username.toLowerCase();
			if (seen.has(handle)) continue;
			seen.add(handle);
			items.push({
				username: post.username,
				name: post.userDisplayName,
				profilePicture: post.userProfilePicture_small ?? post.userProfilePicture
			});
		}

		return items;
	});

	// Below this many replies a comment's replies are shown nested (like Threads).
	// At or above it they stay collapsed — the reply counter on the comment icon is
	// the hint, and the card still opens the comment's own detail page.
	const NESTED_REPLY_LIMIT = 5;
	// Nested replies stop indenting past this depth so the cards never get too narrow.
	const MAX_INDENT_DEPTH = 3;

	// Reload whenever the post changes: the host reuses this component across
	// navigations, so mounting alone would leave stale content.
	$effect(() => {
		const id = postId;
		if (!id) return;
		load(id);
	});

	async function load(id: string) {
		try {
			loading = true;
			error = null;
			if (!id) {
				error = t('page48.post.notFound');
				return;
			}
			const thread = await page48Api.getThread(id);
			const path = findPath(thread, id) ?? [thread];
			const node = path[path.length - 1];
			focused = node.post;
			chain = collectChain(node);

			// Number the chain from the thread's root, so opening the 4th post of an
			// 11-post thread still reads "4/11" instead of "1/8".
			const rootChain = collectChain(thread);
			const position = rootChain.findIndex((p) => p.postId === node.post.postId);
			chainStart = position > 0 ? position : 0;
			chainTotal = position >= 0 && rootChain.length > 1 ? rootChain.length : chain.length;

			// A post that is not part of the author's chain is somebody's reply: the post it
			// answers gets shown above, so it never reads like a standalone post.
			const parent = path.length > 1 ? path[path.length - 2].post : null;
			parentContext = position < 0 && parent ? parent : null;

			replyTree = toReplyTree(node, new Set(chain.map((post) => post.postId)));
			replyTarget = node.post;
		} catch (err: unknown) {
			const e = err as { message?: string };
			error = e?.message || t('page48.post.loadError');
		} finally {
			loading = false;
		}
	}

	/** Path from the root down to `id` (inclusive), or null when it is not in the tree. */
	function findPath(
		node: ThreadResponse,
		id: string,
		path: ThreadResponse[] = []
	): ThreadResponse[] | null {
		const walked = [...path, node];
		if (node.post.postId === id) return walked;
		for (const child of node.replies) {
			const found = findPath(child, id, walked);
			if (found) return found;
		}
		return null;
	}

	/**
	 * The author's own chain starting at `node`: a thread continuation is the child
	 * written by the same user, so the line only connects those.
	 */
	function collectChain(node: ThreadResponse): Page48Post[] {
		const out: Page48Post[] = [node.post];
		let current = node;

		for (let guard = 0; guard < 50; guard += 1) {
			const next = current.replies.find((child) => child.post.userId === current.post.userId);
			if (!next) break;

			out.push(next.post);
			current = next;
		}

		return out;
	}

	/**
	 * Replies shown under `node`: direct replies only, each keeping its own replies
	 * nested. Replies left on the author's continuations belong to those posts' own
	 * pages, so the chain contributes nothing here.
	 */
	function toReplyTree(node: ThreadResponse, chainIds: Set<string>): ThreadResponse[] {
		const out: ThreadResponse[] = [];

		for (const child of node.replies) {
			if (chainIds.has(child.post.postId)) continue;
			out.push({ post: child.post, replies: toReplyTree(child, chainIds) });
		}

		return out;
	}

	function flattenReplies(nodes: ThreadResponse[]): Page48Post[] {
		return nodes.flatMap((node) => [node.post, ...flattenReplies(node.replies)]);
	}

	function removeFromReplyTree(nodes: ThreadResponse[], id: string): ThreadResponse[] {
		return nodes
			.filter((node) => node.post.postId !== id)
			.map((node) => ({ post: node.post, replies: removeFromReplyTree(node.replies, id) }));
	}

	async function handleToggle(post: Page48Post, action: Page48Interaction) {
		await togglePostInteraction(post, action);
	}

	function handleComment(post: Page48Post) {
		replyTarget = post;
	}

	function cancelReply() {
		replyTarget = focused;
	}

	function handleShare(post: Page48Post) {
		void sharePost(post);
	}

	function handleDelete(postId: string) {
		// Deleting the focused post leaves nothing to show here.
		if (focused?.postId === postId) {
			onDeleted?.();
			return;
		}
		if (parentContext?.postId === postId) {
			parentContext = null;
			return;
		}
		chain = chain.filter((p) => p.postId !== postId);
		replyTree = removeFromReplyTree(replyTree, postId);
	}

	async function handleReply(content: string, files: File[], video: VideoDraft | null) {
		const target = replyTarget ?? focused;
		if (!target) return;
		try {
			const images = files.length > 0 ? await uploadPage48Images(files) : [];
			const videos = video ? [await uploadPage48Video(video)] : [];
			await page48Api.createPost(content, images, videos, target.postId);
			showToast(t('page48.post.replySent'), 'success');
			// A reply only shows up here when it answers the focused post or one of the
			// listed replies. Anything else — a chain continuation, or the parent post shown
			// as context — lives on that post's own page, so follow it to keep it visible.
			const shownHere =
				target.postId === focused?.postId || replies.some((p) => p.postId === target.postId);
			if (!shownHere) {
				await goto(`/page48/post/${target.postId}`);
				return;
			}
			await load(postId);
		} catch (err: unknown) {
			const e = err as { message?: string };
			showToast(e?.message || t('page48.post.replyError'), 'error');
			throw err;
		}
	}

	function resolvePost(id: string): Page48Post | undefined {
		return (
			replies.find((p) => p.postId === id) ??
			chain.find((p) => p.postId === id) ??
			(parentContext?.postId === id ? parentContext : undefined) ??
			(focused?.postId === id ? focused : undefined)
		);
	}

	async function handleReplyLike(id: string) {
		const post = resolvePost(id);
		if (post) await handleToggle(post, 'like');
	}

	async function handleReplyRepost(id: string) {
		const post = resolvePost(id);
		if (post) await handleToggle(post, 'repost');
	}

	async function handleReplyBookmark(id: string) {
		const post = resolvePost(id);
		if (post) await handleToggle(post, 'bookmark');
	}
</script>

{#snippet inlineComposer(post: Page48Post)}
	{#if isAuthenticated.value && replyTarget?.postId === post.postId}
		<div class="bg-white/60 dark:bg-zinc-950/60">
			{#if post.postId !== focused?.postId}
				<div class="flex items-center justify-between px-5 sm:px-6 pt-3">
					<span class="text-[13px] text-gray-500 dark:text-gray-400">
						{t('page48.post.replyingTo')}
						<span class="font-semibold text-red-500">@{post.username}</span>
					</span>
					<button
						class="p-1 rounded-full text-gray-400 hover:bg-gray-100 dark:hover:bg-zinc-800 cursor-pointer"
						onclick={cancelReply}
						aria-label={t('page48.aria.cancelReply')}
					>
						<X size={16} />
					</button>
				</div>
			{/if}
			<PostComposer
				isReply
				placeholder={t('page48.composer.replyPlaceholder', { username: post.username })}
				onPost={handleReply}
				{mentionCandidates}
			/>
		</div>
	{/if}
{/snippet}

{#snippet replyNode(node: ThreadResponse, depth: number)}
	<PostCard
		post={node.post}
		showThreadLink={false}
		onLike={handleReplyLike}
		onRepost={handleReplyRepost}
		onBookmark={handleReplyBookmark}
		onComment={handleComment}
		onShare={handleShare}
		onDelete={handleDelete}
	/>
	{@render inlineComposer(node.post)}

	{#if node.replies.length > 0 && node.replies.length < NESTED_REPLY_LIMIT}
		<div
			class={depth < MAX_INDENT_DEPTH
				? 'ml-5 sm:ml-6 border-l-2 border-gray-200/70 dark:border-zinc-800'
				: ''}
		>
			{#each node.replies as child (child.post.postId)}
				{@render replyNode(child, depth + 1)}
			{/each}
		</div>
	{/if}
{/snippet}

{#snippet postSkeleton(widths: string[])}
	<div class="flex gap-4 px-5 sm:px-6 pt-5 pb-3 animate-pulse">
		<div class="h-11 w-11 shrink-0 rounded-full bg-gray-200/80 dark:bg-zinc-800"></div>
		<div class="min-w-0 flex-1 pt-0.5">
			<div class="flex items-center justify-between gap-2">
				<div class="h-4 w-28 rounded bg-gray-200 dark:bg-zinc-800"></div>
				<div class="h-3.5 w-9 rounded bg-gray-200/80 dark:bg-zinc-800"></div>
			</div>
			<div class="mt-2.5 flex flex-col gap-2">
				{#each widths as width, i (i)}
					<div class={`h-3.5 rounded bg-gray-200 dark:bg-zinc-800 ${width}`}></div>
				{/each}
			</div>
			<div class="mt-3.5 flex items-center gap-6">
				{#each ['w-8', 'w-6', 'w-8', 'w-6'] as width, i (i)}
					<div class={`h-4 rounded-full bg-gray-200/80 dark:bg-zinc-800 ${width}`}></div>
				{/each}
				<div class="ml-auto h-4 w-4 rounded-full bg-gray-200/80 dark:bg-zinc-800"></div>
			</div>
		</div>
	</div>
{/snippet}

{#if loading}
	<!-- Mirrors the real page: one post, a divider, then its replies -->
	<div class="flex flex-col">
		{@render postSkeleton(['w-full', 'w-11/12', 'w-2/3'])}
		<div class="border-t border-gray-200/60 dark:border-white/10"></div>
		{@render postSkeleton(['w-full', 'w-1/2'])}
		{@render postSkeleton(['w-11/12', 'w-3/5'])}
	</div>
{:else if error}
	<div class="p-6">
		<ErrorState
			title={t('page48.post.loadError')}
			description={error}
			onRetry={() => load(postId)}
		/>
	</div>
{:else if focused}
	<div class="flex flex-col" in:fade={{ duration: 250 }}>
		<!-- Parent post: the context this reply answers, so it never reads as standalone -->
		{#if parentContext}
			<PostCard
				post={parentContext}
				isThreadLine
				showThreadLink={false}
				onLike={handleReplyLike}
				onRepost={handleReplyRepost}
				onBookmark={handleReplyBookmark}
				onComment={handleComment}
				onShare={handleShare}
				onDelete={handleDelete}
			/>
			{@render inlineComposer(parentContext)}
		{/if}

		<!-- The author's chain: connected, like a thread should read -->
		{#each chain as item, i (item.postId)}
			<PostCard
				post={item}
				isThreadLine={i < chain.length - 1}
				isContinuation={i > 0 || !!parentContext}
				threadPosition={chainTotal > 1 ? { index: chainStart + i, total: chainTotal } : undefined}
				showThreadLink={false}
				showActivityLink={i === 0}
				fullTimestamp={item.postId === focused?.postId}
				hideMedia={hideMedia && i === 0}
				onLike={handleReplyLike}
				onRepost={handleReplyRepost}
				onBookmark={handleReplyBookmark}
				onComment={handleComment}
				onShare={handleShare}
				onDelete={handleDelete}
			/>
			{@render inlineComposer(item)}
		{/each}

		<!-- Everyone else's replies: nested like a thread until they get too many -->
		{#if replyTree.length > 0}
			<div class="border-t border-gray-200/60 dark:border-white/10"></div>
			{#each replyTree as reply (reply.post.postId)}
				{@render replyNode(reply, 0)}
			{/each}
		{/if}
	</div>

	{#if replies.length === 0}
		<div class="p-10 text-center text-[13px] font-medium text-gray-400 dark:text-gray-500">
			{t('page48.post.emptyReplies')}
		</div>
	{/if}
{/if}
