<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { X } from 'lucide-svelte';
	import { page48Api, type Page48Post, type ThreadResponse } from '$lib/api/page48';
	import PostCard from '$lib/components/page48/PostCard.svelte';
	import PostComposer from '$lib/components/page48/PostComposer.svelte';
	import { ErrorState } from '$lib/components';
	import { page48NavbarStore } from '$lib/stores/page48.svelte';
	import { isAuthenticated } from '$lib/stores/authStatus.svelte';
	import { showToast } from '$lib/stores/toast.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';

	const { t } = useTranslation();
	import {
		sharePost,
		togglePostInteraction,
		uploadPage48Images,
		uploadPage48Video,
		type Page48Interaction,
		type VideoDraft
	} from '$lib/utils/page48';
	import { fade } from 'svelte/transition';

	let loading = $state(true);
	let error = $state<string | null>(null);
	let focused = $state<Page48Post | null>(null);
	let replies = $state<Page48Post[]>([]);
	// The post the composer currently replies to (defaults to the focused post).
	let replyTarget = $state<Page48Post | null>(null);

	let postId = $derived($page.params.postId ?? '');

	let seoTitle = $derived(focused ? `@${focused.username} · Page48` : t('page48.seo.postTitle'));
	let seoDescription = $derived(
		focused?.content?.trim() ? focused.content.trim().slice(0, 160) : t('page48.seo.postDesc')
	);
	let seoImage = $derived(focused?.images?.[0]?.url ?? undefined);

	onMount(() => {
		page48NavbarStore.pageType = 'post-detail';
	});

	// Reload whenever the route param changes: SvelteKit reuses this component
	// for same-route navigations, so onMount alone would leave stale content.
	$effect(() => {
		const id = postId;
		if (!id) return;
		load();
	});

	async function load() {
		try {
			loading = true;
			error = null;
			if (!postId) {
				error = t('page48.post.notFound');
				return;
			}
			const thread = await page48Api.getThread(postId);
			const node = findNode(thread, postId) ?? thread;
			focused = node.post;
			replies = collectReplies(node);
			replyTarget = node.post;
		} catch (err: unknown) {
			const e = err as { message?: string };
			error = e?.message || t('page48.post.loadError');
		} finally {
			loading = false;
		}
	}

	function findNode(node: ThreadResponse, id: string): ThreadResponse | null {
		if (node.post.postId === id) return node;
		for (const child of node.replies) {
			const found = findNode(child, id);
			if (found) return found;
		}
		return null;
	}

	function collectReplies(node: ThreadResponse): Page48Post[] {
		const out: Page48Post[] = [];
		for (const child of node.replies) {
			out.push(child.post, ...collectReplies(child));
		}
		return out;
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
		// Deleting the focused post leaves nothing to show here — go back to the feed.
		if (focused?.postId === postId) {
			goto('/page48');
			return;
		}
		replies = replies.filter((p) => p.postId !== postId);
	}

	async function handleReply(content: string, files: File[], video: VideoDraft | null) {
		const target = replyTarget ?? focused;
		if (!target) return;
		try {
			const filenames = files.length > 0 ? await uploadPage48Images(files) : [];
			const videos = video ? [await uploadPage48Video(video)] : [];
			await page48Api.createPost(content, filenames, videos, target.postId);
			showToast(t('page48.post.replySent'), 'success');
			await load();
		} catch (err: unknown) {
			const e = err as { message?: string };
			showToast(e?.message || t('page48.post.replyError'), 'error');
			throw err;
		}
	}

	function resolvePost(postId: string): Page48Post | undefined {
		return (
			replies.find((p) => p.postId === postId) ?? (focused?.postId === postId ? focused : undefined)
		);
	}

	async function handleReplyLike(postId: string) {
		const post = resolvePost(postId);
		if (post) await handleToggle(post, 'like');
	}

	async function handleReplyRepost(postId: string) {
		const post = resolvePost(postId);
		if (post) await handleToggle(post, 'repost');
	}

	async function handleReplyBookmark(postId: string) {
		const post = resolvePost(postId);
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
			/>
		</div>
	{/if}
{/snippet}

<SEO
	title={seoTitle}
	path={`/page48/post/${postId}`}
	description={seoDescription}
	image={seoImage}
	keywords="Page48, JKT48, postingan JKT48, komunitas JKT48"
/>

<div
	class="max-w-[620px] mx-auto w-full min-h-screen bg-white/70 dark:bg-zinc-950/70 backdrop-blur-3xl sm:border-x border-gray-200/60 dark:border-white/10 pb-24 shadow-sm shadow-black/5 dark:shadow-none transition-all"
>
	{#if loading}
		<div class="p-5 flex gap-4 animate-pulse">
			<div class="w-11 h-11 rounded-full bg-gray-200/80 dark:bg-zinc-800 shrink-0"></div>
			<div class="flex-1 space-y-2">
				<div class="h-4 bg-gray-200 dark:bg-zinc-800 rounded w-1/4"></div>
				<div class="h-3 bg-gray-200 dark:bg-zinc-800 rounded w-3/4"></div>
				<div class="h-3 bg-gray-200 dark:bg-zinc-800 rounded w-1/2"></div>
			</div>
		</div>
	{:else if error}
		<div class="p-6">
			<ErrorState title={t('page48.post.loadError')} description={error} onRetry={load} />
		</div>
	{:else if focused}
		<div
			class="flex flex-col divide-y divide-gray-200/60 dark:divide-white/10"
			in:fade={{ duration: 250 }}
		>
			<PostCard
				post={focused}
				isThreadLine={replies.length > 0}
				onLike={handleReplyLike}
				onRepost={handleReplyRepost}
				onBookmark={handleReplyBookmark}
				onComment={handleComment}
				onShare={handleShare}
				onDelete={handleDelete}
			/>
			{@render inlineComposer(focused)}

			{#each replies as reply, i (reply.postId)}
				<PostCard
					post={reply}
					isThreadLine={i < replies.length - 1}
					onLike={handleReplyLike}
					onRepost={handleReplyRepost}
					onBookmark={handleReplyBookmark}
					onComment={handleComment}
					onShare={handleShare}
					onDelete={handleDelete}
				/>
				{@render inlineComposer(reply)}
			{/each}
		</div>

		{#if replies.length === 0}
			<div class="p-10 text-center text-[13px] font-medium text-gray-400 dark:text-gray-500">
				{t('page48.post.emptyReplies')}
			</div>
		{/if}
	{/if}
</div>
