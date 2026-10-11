<script lang="ts">
	import {
		Image as ImageIcon,
		ChartNoAxesColumn,
		EyeOff,
		Plus,
		Smile,
		Trash2,
		X,
		Loader2
	} from 'lucide-svelte';
	import { onMount, tick } from 'svelte';
	import { fade } from 'svelte/transition';
	import EmojiPicker from '$lib/components/page48/EmojiPicker.svelte';
	import MentionSuggestions from '$lib/components/page48/MentionSuggestions.svelte';
	import QuotedPostCard from '$lib/components/page48/QuotedPostCard.svelte';
	import PostEmbedView from '$lib/components/page48/PostEmbedView.svelte';
	import { page48Api, type Page48MediaItem, type Page48Post } from '$lib/api/page48';
	import { userProfile } from '$lib/stores/profile.svelte';
	import { showToast } from '$lib/stores/toast.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import {
		findActiveMention,
		findPostEmbed,
		parseContent,
		probeVideo,
		PAGE48_IMAGE_MAX_BYTES,
		PAGE48_MAX_MEDIA,
		PAGE48_VIDEO_ALLOWED_TYPES,
		PAGE48_VIDEO_MAX_BYTES,
		PAGE48_VIDEO_MAX_SECONDS,
		POLL_MAX_OPTION_LENGTH,
		POLL_MAX_OPTIONS,
		POLL_MIN_OPTIONS,
		searchMentionCandidates,
		takeQuotedPostLink,
		type MediaDraft,
		type MentionCandidate,
		type PostDraftInput
	} from '$lib/utils/page48';

	const { t } = useTranslation();

	interface Props {
		/** Publish a new post. Omitted in edit mode. */
		onPost?: (
			content: string,
			media: MediaDraft[],
			poll: { options: string[] } | null,
			quotedPostId: string | null,
			isSpoiler: boolean
		) => Promise<void>;
		/** Only provided where threads make sense (the feed, not the reply composer). */
		onPostThread?: (drafts: PostDraftInput[]) => Promise<void>;
		/** Seed the composer with an existing post and save edits instead. */
		editingPost?: Page48Post | null;
		/** Save an edit (edit mode). */
		onEdit?: (draft: PostDraftInput) => Promise<void>;
		isReply?: boolean;
		placeholder?: string;
		/** Focus the textarea on mount (e.g. when the composer is opened in a modal). */
		autofocus?: boolean;
		/** Seeds the composer with a quote (e.g. opened from the Repost menu). */
		quotedPost?: Page48Post | null;
		onRemoveQuote?: () => void;
		/**
		 * Users offered after an `@`: normally the author and commenters of the post
		 * being viewed. Who the viewer follows is added as a fallback automatically.
		 */
		mentionCandidates?: MentionCandidate[];
	}

	let {
		onPost,
		onPostThread,
		editingPost = null,
		onEdit,
		isReply = false,
		placeholder,
		autofocus = false,
		quotedPost = null,
		onRemoveQuote,
		mentionCandidates = []
	}: Props = $props();

	/** Edit mode: same composer, but it saves an existing post. */
	let editing = $derived(!!editingPost);

	let resolvedPlaceholder = $derived(placeholder ?? t('page48.composer.placeholder'));

	// Matches the backend limit (CreatePostRequest.content: max_length=500).
	const MAX_CONTENT_LENGTH = 500;

	/** Suggestions shown at once, and how many follows to search as a fallback. */
	const MENTION_LIMIT = 6;
	const MENTION_FOLLOWING_LIMIT = 50;

	/**
	 * Typography shared by the textarea and the highlight layer behind it — they have
	 * to match exactly or the coloured text would drift away from the real text.
	 */
	const CONTENT_TEXT_CLASS =
		'text-[17px] sm:text-[20px] leading-relaxed whitespace-pre-wrap break-words';

	// In edit mode these are seeded once from the post being edited.
	// svelte-ignore state_referenced_locally
	let content = $state(editingPost?.content ?? '');
	/** Ordered media picked for this draft, images and videos mixed. */
	let media = $state<MediaDraft[]>([]);
	/** Object URLs for `media`, kept in step so a preview can be revoked. */
	let mediaPreviews = $state<string[]>([]);
	/** Media already on the post, kept unless removed (seeded in edit mode). */
	// svelte-ignore state_referenced_locally
	let existingMedia = $state<Page48MediaItem[]>(editingPost?.media ?? []);
	let probing = $state(false);
	let isSubmitting = $state(false);
	let emojiOpen = $state(false);
	let pollOpen = $state(false);
	/** Mark the active draft as a spoiler (each thread item carries its own flag). */
	// svelte-ignore state_referenced_locally
	let spoilerOn = $state(editingPost?.isSpoiler ?? false);
	/** Reply mode hides the tool row until the user engages the composer. */
	let composerActive = $state(false);
	let pollOptions = $state<string[]>(['', '']);
	/** The quote attached to this draft: seeded by the parent, replaced by a paste. */
	let quoteOverride = $state<Page48Post | null | undefined>(undefined);
	let quote = $derived(quoteOverride === undefined ? quotedPost : quoteOverride);
	/** Posts already queued for the thread (the active draft is the one below). */
	let threadItems = $state<PostDraftInput[]>([]);
	let textareaEl = $state<HTMLTextAreaElement>();
	let emojiButton = $state<HTMLButtonElement>();
	let fileInput = $state<HTMLInputElement>();

	/** The `@handle` being typed, or null when no suggestion panel should show. */
	let mentionQuery = $state<string | null>(null);
	/** Where the handle starts and ends in `content`, so picking replaces all of it. */
	let mentionRange = $state<{ start: number; end: number } | null>(null);
	let mentionActive = $state(0);
	/** Who the viewer follows, fetched at most once and only to widen the search. */
	let followingCandidates = $state<MentionCandidate[]>([]);
	let followingLoading = $state(false);

	// Focus when the composer is opened as a modal. Deferred by one frame because the
	// modal is portalled (its node is moved to <body> right after mount), and moving a
	// node in the DOM blurs anything focused inside it during that same mount pass.
	onMount(() => {
		// Grow once for any seeded content (edit mode), and focus if requested.
		requestAnimationFrame(() => {
			if (!textareaEl) return;
			autoGrow(textareaEl);
			if (autofocus) textareaEl.focus();
		});
	});

	function autoGrow(el: HTMLTextAreaElement) {
		el.style.height = 'auto';
		el.style.height = el.scrollHeight + 'px';
	}

	// Mentions and hashtags are coloured while typing, matching the published post.
	let contentParts = $derived(parseContent(content));
	// Live preview of a YouTube or X link, so the author sees the embed before posting.
	let postEmbed = $derived(findPostEmbed(contentParts));

	/** Insert text at the caret (or over a range), keeping focus and caret in place. */
	async function insertAtCaret(text: string, rangeStart?: number, rangeEnd?: number) {
		const el = textareaEl;
		const start = rangeStart ?? el?.selectionStart ?? content.length;
		const end = rangeEnd ?? el?.selectionEnd ?? start;

		if (content.length - (end - start) + text.length > MAX_CONTENT_LENGTH) {
			showToast(t('page48.composer.emojiTooLong'), 'error');
			return;
		}

		content = content.slice(0, start) + text + content.slice(end);
		const caret = start + text.length;

		if (!el) return;
		await tick();
		el.focus();
		el.setSelectionRange(caret, caret);
		autoGrow(el);
	}

	/** Insert an emoji at the caret, keeping focus and the caret in the textarea. */
	async function insertEmoji(char: string) {
		await insertAtCaret(char);
	}

	/**
	 * Suggestions for the handle being typed: the in-context users first (the post
	 * and its comments), then who the viewer follows, deduped and without the
	 * viewer themself.
	 */
	let mentionItems = $derived.by(() => {
		const query = mentionQuery;
		if (query === null) return [] as MentionCandidate[];

		const self = userProfile.data?.username?.toLowerCase() ?? null;
		const seen = new Set<string>();
		const items: MentionCandidate[] = [];

		for (const source of [mentionCandidates, followingCandidates]) {
			for (const candidate of searchMentionCandidates(source, query)) {
				const handle = candidate.username.toLowerCase();
				if (handle === self || seen.has(handle)) continue;
				seen.add(handle);
				items.push(candidate);
				if (items.length >= MENTION_LIMIT) return items;
			}
		}

		return items;
	});

	// `mentionActive` can point past a list that just shrank; clamp for both the
	// highlight and the item Enter inserts.
	let activeMentionIndex = $derived(
		mentionItems.length === 0 ? 0 : Math.min(mentionActive, mentionItems.length - 1)
	);

	/** Pick up the `@` under the caret after every edit. */
	function syncMentionState() {
		const el = textareaEl;
		if (!el) return;

		const found = findActiveMention(content, el.selectionStart ?? content.length);
		if (!found) {
			closeMentions();
			return;
		}

		mentionQuery = found.query;
		mentionRange = { start: found.start, end: found.end };
		mentionActive = 0;
		emojiOpen = false;

		// Nothing in context matches, so widen the search to who the viewer follows.
		if (searchMentionCandidates(mentionCandidates, found.query).length === 0) {
			void loadFollowingCandidates();
		}
	}

	/** Load who the viewer follows, once, for suggestions outside the current post. */
	async function loadFollowingCandidates() {
		if (followingLoading || followingCandidates.length > 0) return;
		const username = userProfile.data?.username;
		if (!username) return;

		followingLoading = true;
		try {
			const response = await page48Api.getFollowing(username, MENTION_FOLLOWING_LIMIT);
			followingCandidates = response.data.map((user) => ({
				username: user.username,
				name: user.name,
				profilePicture: user.profilePicture_small ?? user.profilePicture
			}));
		} catch {
			// Suggestions simply stay limited to the in-context users.
		} finally {
			followingLoading = false;
		}
	}

	function closeMentions() {
		mentionQuery = null;
		mentionRange = null;
	}

	async function pickMention(candidate: MentionCandidate | undefined) {
		const range = mentionRange;
		if (!candidate || !range) return;
		closeMentions();
		// A trailing space so typing continues right after the handle.
		await insertAtCaret(`@${candidate.username} `, range.start, range.end);
	}

	/** Returns true when the key was consumed by the suggestion panel. */
	function handleMentionKeydown(event: KeyboardEvent): boolean {
		if (mentionQuery === null) return false;

		if (event.key === 'Escape') {
			event.preventDefault();
			// Keep the composer modal's window-level Escape handler out of this.
			event.stopPropagation();
			closeMentions();
			return true;
		}

		const count = mentionItems.length;
		if (count === 0) return false;

		if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
			event.preventDefault();
			const step = event.key === 'ArrowDown' ? 1 : -1;
			mentionActive = (activeMentionIndex + step + count) % count;
			return true;
		}

		if (event.key === 'Enter' || event.key === 'Tab') {
			event.preventDefault();
			void pickMention(mentionItems[activeMentionIndex]);
			return true;
		}

		return false;
	}

	/** Pick any mix of photos and videos; up to `PAGE48_MAX_MEDIA` in total. */
	async function handleMediaSelect(e: Event) {
		const target = e.target as HTMLInputElement;
		const files = Array.from(target.files ?? []);
		target.value = '';
		if (files.length === 0) return;

		const room = PAGE48_MAX_MEDIA - media.length - existingMedia.length;
		if (room <= 0) {
			showToast(t('page48.composer.maxMedia'), 'error');
			return;
		}

		probing = true;
		try {
			for (const file of files.slice(0, room)) {
				const draft = await buildMediaDraft(file);
				if (!draft) continue;
				media = [...media, draft];
				mediaPreviews = [...mediaPreviews, URL.createObjectURL(file)];
			}
		} finally {
			probing = false;
		}
	}

	/** Validate one picked file and shape it for the draft, or null if rejected. */
	async function buildMediaDraft(file: File): Promise<MediaDraft | null> {
		if (file.type.startsWith('image/')) {
			if (file.size > PAGE48_IMAGE_MAX_BYTES) {
				showToast(t('page48.composer.maxSize'), 'error');
				return null;
			}
			return { type: 'image', file };
		}

		if (!PAGE48_VIDEO_ALLOWED_TYPES.includes(file.type)) {
			showToast(t('page48.composer.videoInvalidType'), 'error');
			return null;
		}
		if (file.size > PAGE48_VIDEO_MAX_BYTES) {
			showToast(t('page48.composer.videoTooLarge'), 'error');
			return null;
		}
		try {
			const meta = await probeVideo(file);
			if (!Number.isFinite(meta.duration) || meta.duration <= 0) {
				showToast(t('page48.composer.videoUnreadable'), 'error');
				return null;
			}
			if (meta.duration > PAGE48_VIDEO_MAX_SECONDS + 0.5) {
				showToast(t('page48.composer.videoTooLong'), 'error');
				return null;
			}
			return {
				type: 'video',
				file,
				width: meta.width,
				height: meta.height,
				duration: meta.duration
			};
		} catch {
			showToast(t('page48.composer.videoUnreadable'), 'error');
			return null;
		}
	}

	function removeMedia(index: number) {
		URL.revokeObjectURL(mediaPreviews[index]);
		media = media.filter((_, i) => i !== index);
		mediaPreviews = mediaPreviews.filter((_, i) => i !== index);
	}

	/** Drop one of the post's existing media (removed from storage on save). */
	function removeExistingMedia(index: number) {
		existingMedia = existingMedia.filter((_, i) => i !== index);
	}

	/** The post currently being edited, in the shape the API expects. */
	function currentDraft(): PostDraftInput {
		return {
			content,
			media: [...media],
			poll: pollOpen ? { options: pollDraft } : null,
			quotedPostId: quote?.postId ?? null,
			isSpoiler: spoilerOn,
			existingMedia: [...existingMedia]
		};
	}

	function draftHasContent(draft: PostDraftInput): boolean {
		return (
			draft.content.trim().length > 0 ||
			draft.media.length > 0 ||
			(draft.existingMedia?.length ?? 0) > 0 ||
			(!!draft.poll && draft.poll.options.length >= POLL_MIN_OPTIONS) ||
			!!draft.quotedPostId
		);
	}

	function resetDraft() {
		content = '';
		mediaPreviews.forEach(URL.revokeObjectURL);
		media = [];
		mediaPreviews = [];
		existingMedia = [];
		closePoll();
		spoilerOn = false;
		quoteOverride = undefined;
		emojiOpen = false;
		void tick().then(() => {
			if (textareaEl) textareaEl.style.height = 'auto';
		});
	}

	/** Park the current draft as a thread post and start a fresh one. */
	function addToThread() {
		const draft = currentDraft();
		if (!draftHasContent(draft)) return;

		threadItems = [...threadItems, draft];
		resetDraft();
	}

	function removeThreadItem(index: number) {
		threadItems = threadItems.filter((_, i) => i !== index);
	}

	function draftSummary(draft: PostDraftInput): string {
		const parts: string[] = [];
		const mediaCount = draft.media.length + (draft.existingMedia?.length ?? 0);
		if (mediaCount > 0) parts.push(t('page48.composer.mediaCount', { count: mediaCount }));
		if (draft.poll) parts.push(t('page48.poll.create'));
		if (draft.quotedPostId) parts.push(t('page48.repostMenu.quote'));
		return parts.join(' · ');
	}

	// Poll editor (a poll can't be combined with media)
	function dropMedia() {
		mediaPreviews.forEach(URL.revokeObjectURL);
		media = [];
		mediaPreviews = [];
	}

	function openPoll() {
		dropMedia();
		pollOpen = true;
	}

	function closePoll() {
		pollOpen = false;
		pollOptions = ['', ''];
	}

	/** Drop the quote — whether it came from the host card or a pasted link. */
	function removeQuote() {
		quoteOverride = null;
		onRemoveQuote?.();
	}

	/** A quote and a poll can't coexist (the server rejects the pair). */
	function attachQuote(post: Page48Post) {
		quoteOverride = post;
		closePoll();
	}

	/**
	 * Pasting a Page48 post link quotes that post, like X: the link is taken out of
	 * the text and the post is fetched for the preview.
	 */
	async function handlePaste(event: ClipboardEvent) {
		// An edit keeps its original quote; pasting a link must not change it.
		if (editing) return;
		const text = event.clipboardData?.getData('text') ?? '';
		const taken = takeQuotedPostLink(text);
		if (!taken) return;

		event.preventDefault();
		try {
			attachQuote(await page48Api.getPost(taken.postId));
			if (taken.rest) await insertAtCaret(taken.rest);
		} catch {
			// Keep the raw text so the pasted link is not lost.
			showToast(t('page48.composer.quoteNotFound'), 'error');
			await insertAtCaret(text);
		}
	}

	function addPollOption() {
		if (pollOptions.length >= POLL_MAX_OPTIONS) return;
		pollOptions = [...pollOptions, ''];
	}

	function removePollOption(index: number) {
		pollOptions = pollOptions.filter((_, i) => i !== index);
	}

	/** Mirror the post counter colours: amber near the limit, red at the limit. */
	function pollCounterClass(length: number) {
		if (length >= POLL_MAX_OPTION_LENGTH) return 'text-red-500';
		if (length >= POLL_MAX_OPTION_LENGTH - 10) return 'text-amber-500';
		return 'text-gray-400 dark:text-gray-500';
	}

	let pollDraft = $derived(
		pollOptions.map((option) => option.trim()).filter((option) => option.length > 0)
	);
	// Mirrors the server rule: 2..6 options, max 50 characters each.
	let pollReady = $derived(!pollOpen || pollDraft.length >= POLL_MIN_OPTIONS);

	async function handleSubmit() {
		if (isSubmitting) return;

		// Edit mode: save this single post instead of publishing a new one.
		if (editing) {
			const draft = currentDraft();
			if (!draftHasContent(draft)) return;
			try {
				isSubmitting = true;
				await onEdit?.(draft);
			} catch (error) {
				console.error(error);
			} finally {
				isSubmitting = false;
			}
			return;
		}

		if (!pollReady) return;

		const drafts = [...threadItems];
		const active = currentDraft();
		// A quote may be published with no text of its own.
		if (draftHasContent(active) || quote) drafts.push(active);
		if (drafts.length === 0) return;

		// Extra drafts only exist when a thread handler was provided.
		const publishAsThread = drafts.length > 1 && !!onPostThread;

		try {
			isSubmitting = true;
			if (publishAsThread) {
				await onPostThread?.(drafts);
			} else {
				const [only] = drafts;
				await onPost?.(
					only.content,
					only.media,
					only.poll,
					only.quotedPostId ?? null,
					only.isSpoiler ?? false
				);
			}
			threadItems = [];
			resetDraft();
		} catch (error) {
			console.error(error);
		} finally {
			isSubmitting = false;
		}
	}

	let canSubmit = $derived(
		(draftHasContent(currentDraft()) || threadItems.length > 0 || !!quote) && pollReady
	);
	let isThread = $derived(threadItems.length > 0);

	// The reply composer starts as just a text box + a disabled post button; the tool row
	// shows up once it is clicked (or as soon as there is something to attach it to).
	let showToolRow = $derived(
		!isReply || composerActive || isThread || draftHasContent(currentDraft())
	);

	let userAvatar = $derived(
		userProfile.data?.profilePicture_small ||
			(userProfile.data
				? `https://ui-avatars.com/api/?name=${encodeURIComponent(userProfile.data.name || '')}&background=fca5a5&color=fff`
				: null)
	);
</script>

<!-- Submit button: sits beside the input until the tool row appears, then moves into it -->
{#snippet submitButton()}
	<button
		class="px-5 py-2 bg-black dark:bg-white text-white dark:text-black rounded-full font-semibold text-[14px] disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer hover:bg-gray-800 dark:hover:bg-gray-200 transition-all flex items-center gap-2 active:scale-95 shadow-sm"
		disabled={!canSubmit || isSubmitting || probing}
		onclick={handleSubmit}
	>
		{#if isSubmitting}
			<Loader2 size={16} class="animate-spin" />
		{/if}
		{editing
			? t('page48.edit.save')
			: isThread
				? t('page48.thread.publish')
				: isReply
					? t('page48.composer.reply')
					: t('page48.composer.submit')}
	</button>
{/snippet}

<div
	class="flex gap-4 py-5 px-5 sm:px-6 border-b border-gray-100 dark:border-white/10 bg-white/60 dark:bg-zinc-950/60 backdrop-blur-xl transition-all"
>
	<!-- Avatar -->
	<div class="shrink-0 pt-1">
		<div
			class="w-11 h-11 rounded-full overflow-hidden bg-gray-100 dark:bg-zinc-800 ring-2 ring-white dark:ring-zinc-900 shadow-sm"
		>
			{#if userAvatar}
				<img
					src={userAvatar}
					alt={t('page48.aria.profile')}
					class="w-full h-full object-cover"
					onerror={(e) => {
						(e.target as HTMLImageElement).src =
							`https://ui-avatars.com/api/?name=${encodeURIComponent(userProfile.data?.name || '')}&background=fca5a5&color=fff`;
					}}
				/>
			{:else}
				<div
					class="w-full h-full bg-red-100 flex items-center justify-center text-red-500 font-bold"
				>
					?
				</div>
			{/if}
		</div>
	</div>

	<!-- Composer Content -->
	<div class="flex-1 min-w-0 flex flex-col pt-1.5">
		<!-- Queued thread posts -->
		{#if threadItems.length > 0}
			<div class="flex flex-col gap-1.5 mb-2" in:fade>
				{#each threadItems as item, i (i)}
					{@const summary = draftSummary(item)}
					<div
						class="flex items-start gap-2 rounded-xl border border-gray-200 dark:border-zinc-800 px-3 py-2"
					>
						<span class="mt-0.5 shrink-0 text-[11px] font-bold tabular-nums text-gray-400">
							{i + 1}
						</span>
						<div class="min-w-0 flex-1">
							<p class="truncate text-[13px] text-gray-700 dark:text-gray-200">
								{item.content.trim() || t('page48.aria.media')}
							</p>
							{#if summary}
								<p class="mt-0.5 text-[11px] text-gray-400 dark:text-gray-500">{summary}</p>
							{/if}
						</div>
						<button
							type="button"
							class="shrink-0 p-1.5 rounded-full text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors cursor-pointer"
							onclick={() => removeThreadItem(i)}
							aria-label={t('page48.thread.removePost')}
						>
							<X size={14} />
						</button>
					</div>
				{/each}
			</div>
		{/if}

		<div class="flex items-center gap-3">
			<div class="relative min-w-0 flex-1">
				<!-- Highlight layer. The textarea's own text is transparent so mentions,
				     hashtags and links can be coloured as they are typed. -->
				<div
					aria-hidden="true"
					class={`pointer-events-none absolute inset-0 select-none overflow-hidden text-gray-900 dark:text-gray-100 ${CONTENT_TEXT_CLASS} ${showToolRow ? 'pb-2' : ''}`}
				>
					{#each contentParts as part, i (i)}
						{#if part.tag}
							<span class="text-red-500">{part.text}</span>
						{:else if part.mention}
							<span class="font-semibold text-red-500">{part.text}</span>
						{:else if part.link}
							<span class="text-blue-500">{part.text}</span>
						{:else if part.spoiler}
							<span class="spoiler-hidden">||{part.text}||</span>
						{:else}
							{part.text}
						{/if}
					{/each}
				</div>
				<textarea
					bind:this={textareaEl}
					bind:value={content}
					placeholder={resolvedPlaceholder}
					maxlength={MAX_CONTENT_LENGTH}
					class={`relative block w-full resize-none bg-transparent text-transparent caret-gray-900 outline-none placeholder:text-gray-400 dark:caret-gray-100 dark:placeholder:text-gray-500 ${CONTENT_TEXT_CLASS} ${showToolRow ? 'pb-2' : ''}`}
					rows="1"
					oninput={(e) => {
						autoGrow(e.target as HTMLTextAreaElement);
						syncMentionState();
					}}
					onkeydown={handleMentionKeydown}
					onpaste={handlePaste}
					onblur={closeMentions}
					onfocus={() => (composerActive = true)}
				></textarea>
			</div>
			{#if !showToolRow}
				{@render submitButton()}
			{/if}
		</div>

		<!-- Embeddable link preview (YouTube/X/Instagram/TikTok/Spotify) -->
		{#if postEmbed}
			<div class="mt-2" in:fade>
				<PostEmbedView embed={postEmbed} compact />
			</div>
		{/if}

		<!-- Poll editor -->
		{#if pollOpen}
			<div class="mt-2 rounded-2xl border border-gray-200 dark:border-zinc-800 p-2" in:fade>
				{#each pollOptions as _, i}
					<div class="flex items-center gap-1 mb-2 last:mb-0">
						<div class="relative flex-1 min-w-0">
							<input
								bind:value={pollOptions[i]}
								type="text"
								maxlength={POLL_MAX_OPTION_LENGTH}
								placeholder={t('page48.poll.optionPlaceholder', { index: i + 1 })}
								aria-label={t('page48.poll.optionPlaceholder', { index: i + 1 })}
								class="w-full rounded-lg border border-gray-200 dark:border-zinc-800 pl-3 pr-14 py-2 text-[14px] text-gray-900 dark:text-gray-100 bg-transparent outline-none transition-colors placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:border-red-400 dark:focus:border-red-500"
							/>
							<span
								class={`pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[11px] font-medium tabular-nums ${pollCounterClass(
									pollOptions[i].length
								)}`}
							>
								{pollOptions[i].length}/{POLL_MAX_OPTION_LENGTH}
							</span>
						</div>
						{#if pollOptions.length > POLL_MIN_OPTIONS}
							<button
								type="button"
								class="p-2 rounded-full text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors cursor-pointer"
								onclick={() => removePollOption(i)}
								aria-label={t('page48.poll.removeOption', { index: i + 1 })}
							>
								<X size={16} />
							</button>
						{/if}
					</div>
				{/each}

				<div class="flex items-center justify-between mt-1">
					<button
						type="button"
						class="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[13px] font-semibold text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
						onclick={addPollOption}
						disabled={pollOptions.length >= POLL_MAX_OPTIONS}
					>
						<Plus size={15} />
						{t('page48.poll.addOption')}
					</button>
					<button
						type="button"
						class="p-2 rounded-full text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors cursor-pointer"
						onclick={closePoll}
						title={t('page48.poll.remove')}
						aria-label={t('page48.poll.remove')}
					>
						<Trash2 size={16} />
					</button>
				</div>

				{#if !pollReady}
					<p class="px-1 mt-1 text-[12px] text-amber-500">{t('page48.poll.hint')}</p>
				{/if}
			</div>
		{/if}

		<!-- Media Previews: the post's own media + newly picked, images and videos -->
		{#if existingMedia.length > 0 || media.length > 0}
			<div class="flex gap-2 mt-2 mb-2 overflow-x-auto pb-2 snap-x" in:fade>
				{#each existingMedia as item, i}
					<div class="relative shrink-0 snap-start">
						{#if item.type === 'video'}
							<video
								src={item.url ?? ''}
								muted
								playsinline
								class="h-32 w-auto rounded-xl border border-gray-200 dark:border-zinc-800 bg-black"
							></video>
						{:else}
							<img
								src={item.url_small || item.url_medium || item.url}
								alt={t('page48.composer.previewAlt')}
								class="h-32 w-auto rounded-xl border border-gray-200 dark:border-zinc-800 object-cover"
							/>
						{/if}
						<button
							class="absolute top-1 right-1 w-6 h-6 bg-black/60 hover:bg-black text-white rounded-full flex items-center justify-center transition-colors cursor-pointer"
							onclick={() => removeExistingMedia(i)}
						>
							<X size={14} />
						</button>
					</div>
				{/each}
				{#each media as item, i}
					<div class="relative shrink-0 snap-start">
						{#if item.type === 'video'}
							<video
								src={mediaPreviews[i]}
								muted
								playsinline
								class="h-32 w-auto rounded-xl border border-gray-200 dark:border-zinc-800 bg-black"
							></video>
						{:else}
							<img
								src={mediaPreviews[i]}
								alt={t('page48.composer.previewAlt')}
								class="h-32 w-auto rounded-xl border border-gray-200 dark:border-zinc-800 object-cover"
							/>
						{/if}
						<button
							class="absolute top-1 right-1 w-6 h-6 bg-black/60 hover:bg-black text-white rounded-full flex items-center justify-center transition-colors cursor-pointer"
							onclick={() => removeMedia(i)}
						>
							<X size={14} />
						</button>
					</div>
				{/each}
			</div>
		{/if}

		<!-- Quoted post being replied to by this composer -->
		{#if quote}
			<QuotedPostCard post={quote} removable={!editing} onRemove={removeQuote} />
		{/if}

		{#if showToolRow}
			<!-- Action Bar -->
			<div class="flex items-center justify-between mt-3 pt-2 border-t border-transparent">
				<div class="flex items-center gap-1">
					<!-- Media: photos and videos, mixed, one picker -->
					<button
						class="p-2 -ml-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-full transition-all disabled:opacity-50 group cursor-pointer"
						onclick={() => fileInput?.click()}
						disabled={media.length + existingMedia.length >= PAGE48_MAX_MEDIA ||
							probing ||
							isSubmitting ||
							pollOpen}
						title={t('page48.composer.addMedia')}
						aria-label={t('page48.composer.addMedia')}
					>
						{#if probing}
							<Loader2 size={20} class="animate-spin" />
						{:else}
							<ImageIcon size={20} class="group-hover:scale-110 transition-transform" />
						{/if}
					</button>
					<input
						type="file"
						accept="image/jpeg,image/png,image/webp,video/mp4,video/webm"
						multiple
						class="hidden"
						bind:this={fileInput}
						onchange={handleMediaSelect}
					/>

					<!-- Emoji Picker -->
					<button
						bind:this={emojiButton}
						class={`p-2 rounded-full transition-all disabled:opacity-50 group cursor-pointer hover:bg-red-50 dark:hover:bg-red-500/10 ${
							emojiOpen ? 'text-red-500' : 'text-gray-400 hover:text-red-500'
						}`}
						onclick={() => (emojiOpen = !emojiOpen)}
						disabled={isSubmitting}
						title={t('page48.composer.addEmoji')}
						aria-label={t('page48.composer.addEmoji')}
						aria-haspopup="dialog"
						aria-expanded={emojiOpen}
					>
						<Smile size={20} class="group-hover:scale-110 transition-transform" />
					</button>

					<!-- Poll (not available on replies, quotes or edits) -->
					{#if !isReply && !quotedPost && !editing}
						<button
							class={`p-2 rounded-full transition-all disabled:opacity-50 group cursor-pointer hover:bg-red-50 dark:hover:bg-red-500/10 ${
								pollOpen ? 'text-red-500' : 'text-gray-400 hover:text-red-500'
							}`}
							onclick={pollOpen ? closePoll : openPoll}
							disabled={media.length + existingMedia.length > 0 ||
								probing ||
								isSubmitting ||
								isThread}
							title={t('page48.poll.create')}
							aria-label={t('page48.poll.create')}
							aria-pressed={pollOpen}
						>
							<ChartNoAxesColumn size={20} class="group-hover:scale-110 transition-transform" />
						</button>
					{/if}

					<!-- Spoiler toggle: available on every post, replies included -->
					<button
						class={`p-2 rounded-full transition-all disabled:opacity-50 group cursor-pointer hover:bg-red-50 dark:hover:bg-red-500/10 ${
							spoilerOn ? 'text-red-500' : 'text-gray-400 hover:text-red-500'
						}`}
						onclick={() => (spoilerOn = !spoilerOn)}
						disabled={isSubmitting}
						title={t('page48.spoiler.mark')}
						aria-label={t('page48.spoiler.mark')}
						aria-pressed={spoilerOn}
					>
						<EyeOff size={20} class="group-hover:scale-110 transition-transform" />
					</button>
				</div>

				<!-- Character Counter + Submit Button -->
				<div class="flex items-center gap-3">
					{#if content.length > 0}
						<span
							class={`text-[13px] font-medium tabular-nums ${
								content.length >= MAX_CONTENT_LENGTH
									? 'text-red-500'
									: content.length >= MAX_CONTENT_LENGTH - 50
										? 'text-amber-500'
										: 'text-gray-400 dark:text-gray-500'
							}`}
							aria-live="polite"
						>
							{content.length}/{MAX_CONTENT_LENGTH}
						</span>
					{/if}

					<!-- Thread: only where a thread makes sense (never in the reply composer) -->
					{#if onPostThread}
						<button
							type="button"
							class="p-2 rounded-full transition-colors cursor-pointer text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 disabled:opacity-40 disabled:cursor-not-allowed"
							onclick={addToThread}
							disabled={!draftHasContent(currentDraft()) || isSubmitting || probing}
							title={t('page48.thread.addPost')}
							aria-label={t('page48.thread.addPost')}
						>
							<Plus size={18} />
						</button>
					{/if}

					{@render submitButton()}
				</div>
			</div>
		{/if}
	</div>
</div>

{#if mentionQuery !== null}
	<MentionSuggestions
		anchor={textareaEl}
		items={mentionItems}
		activeIndex={activeMentionIndex}
		loading={followingLoading}
		onHover={(index) => (mentionActive = index)}
		onPick={pickMention}
		onClose={closeMentions}
	/>
{/if}

{#if emojiOpen}
	<EmojiPicker anchor={emojiButton} onPick={insertEmoji} onClose={() => (emojiOpen = false)} />
{/if}

<style>
	/* Matches the published inline spoiler: a real blur of the glyphs. */
	.spoiler-hidden {
		filter: blur(6px);
		opacity: 0.8;
		user-select: none;
	}
</style>
