<script lang="ts">
	import { X } from 'lucide-svelte';
	import { portal } from '$lib/actions/portal';
	import { fade } from 'svelte/transition';
	import PostComposer from '$lib/components/page48/PostComposer.svelte';
	import { page48Api, type Page48Post } from '$lib/api/page48';
	import { showToast } from '$lib/stores/toast.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import {
		uploadPage48Images,
		uploadPage48Video,
		type PostDraftInput,
		type VideoDraft
	} from '$lib/utils/page48';

	interface Props {
		onClose: () => void;
		/** When set, the composer publishes a quote of this post. */
		quotedPost?: Page48Post | null;
		onRemoveQuote?: () => void;
	}

	let { onClose, quotedPost = null, onRemoveQuote }: Props = $props();

	const { t } = useTranslation();

	/** Upload one composed draft and return the payload the API expects. */
	async function buildThreadItem(draft: PostDraftInput) {
		const images = draft.images.length > 0 ? await uploadPage48Images(draft.images) : [];
		const videos = draft.video ? [await uploadPage48Video(draft.video)] : [];
		return { content: draft.content, images, videos, poll: draft.poll };
	}

	/**
	 * Tell the rest of Page48 a post was created so any mounted list can prepend it.
	 * The navbar lives outside the feed/profile lists, so a window event decouples them.
	 */
	function announce(post: unknown) {
		window.dispatchEvent(new CustomEvent('page48:post-created', { detail: post }));
	}

	async function handlePost(
		content: string,
		files: File[],
		video: VideoDraft | null,
		poll: { options: string[] } | null
	) {
		try {
			const images = files.length > 0 ? await uploadPage48Images(files) : [];
			const videos = video ? [await uploadPage48Video(video)] : [];
			const newPost = await page48Api.createPost(
				content,
				images,
				videos,
				undefined,
				poll,
				quotedPost?.postId
			);
			if (newPost) {
				announce(newPost);
				showToast(t('page48.feed.postSuccess'), 'success');
				onClose();
			}
		} catch (err: unknown) {
			const e = err as { message?: string; detail?: string };
			showToast(e?.detail || e?.message || t('page48.feed.postError'), 'error');
			throw err; // Rethrow so the composer stops its loading state
		}
	}

	async function handleThread(drafts: PostDraftInput[]) {
		try {
			const items = [];
			for (const draft of drafts) {
				items.push(await buildThreadItem(draft));
			}

			const thread = await page48Api.createThread(items);
			if (thread?.posts?.length) {
				// Only the first post belongs in a list; the rest live in the thread.
				announce(thread.posts[0]);
				showToast(t('page48.thread.sent', { count: thread.posts.length }), 'success');
				onClose();
			}
		} catch (err: unknown) {
			const e = err as { message?: string; detail?: string };
			showToast(e?.detail || e?.message || t('page48.thread.error'), 'error');
			throw err;
		}
	}
</script>

<svelte:window
	onkeydown={(e) => {
		if (e.key === 'Escape') onClose();
	}}
/>

<div
	use:portal
	class="fixed inset-0 z-[10060] flex justify-center sm:items-center sm:p-4"
	transition:fade={{ duration: 150 }}
	role="dialog"
	aria-modal="true"
	aria-label={t('page48.composer.newPost')}
>
	<div
		class="absolute inset-0 bg-black/60 backdrop-blur-sm"
		onclick={onClose}
		role="presentation"
	></div>

	<!-- Full screen on mobile (keyboard friendly), a centred card from sm up. -->
	<div
		class="relative flex h-[100dvh] w-full flex-col overflow-hidden bg-white shadow-2xl dark:bg-zinc-950 sm:h-auto sm:max-h-[85dvh] sm:max-w-[620px] sm:rounded-2xl sm:border sm:border-gray-200 dark:border-zinc-800"
	>
		<div
			class="flex h-14 shrink-0 items-center justify-between gap-3 border-b border-gray-100 px-4 dark:border-white/10 sm:px-6"
		>
			<h2 class="text-[15px] font-bold text-gray-900 dark:text-gray-100">
				{quotedPost ? t('page48.repostMenu.quote') : t('page48.composer.newPost')}
			</h2>
			<button
				class="-mr-2 p-2 rounded-full text-gray-400 hover:bg-gray-100 dark:hover:bg-zinc-800 cursor-pointer"
				onclick={onClose}
				aria-label={t('page48.aria.close')}
			>
				<X size={18} />
			</button>
		</div>

		<div class="flex-1 overflow-y-auto overscroll-contain">
			<PostComposer
				onPost={handlePost}
				onPostThread={quotedPost ? undefined : handleThread}
				{quotedPost}
				{onRemoveQuote}
				autofocus
			/>
		</div>
	</div>
</div>
