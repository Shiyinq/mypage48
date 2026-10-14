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
	import { onDestroy, onMount, tick } from 'svelte';
	import { fade } from 'svelte/transition';
	import EmojiPicker from '$lib/components/page48/EmojiPicker.svelte';
	import MentionSuggestions from '$lib/components/page48/MentionSuggestions.svelte';
	import QuotedPostCard from '$lib/components/page48/QuotedPostCard.svelte';
	import PostEmbedView from '$lib/components/page48/PostEmbedView.svelte';
	import ReplyAudiencePicker from '$lib/components/page48/ReplyAudiencePicker.svelte';
	import { page48Api, type Page48Post, type Page48ReplySetting } from '$lib/api/page48';
	import { REPLY_AUDIENCE_ICONS } from '$lib/constants/replyAudience';
	import { userProfile } from '$lib/stores/profile.svelte';
	import { showToast } from '$lib/stores/toast.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import {
		findActiveMention,
		findPostEmbed,
		parseEditor,
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
		type DraftMedia,
		type EditorPart,
		type MediaDraft,
		type MentionCandidate,
		type PostDraftInput
	} from '$lib/utils/page48';

	const { t } = useTranslation();

	interface Props {
		/** Publish a new post. Omitted in edit mode. */
		onPost?: (
			content: string,
			media: DraftMedia[],
			poll: { options: string[] } | null,
			quotedPostId: string | null,
			isSpoiler: boolean,
			replySettings: Page48ReplySetting
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
		/**
		 * Reports whether there is unsaved work, so a host modal can warn before
		 * closing. Fires with `false` once the draft is empty or after publishing.
		 */
		onDirtyChange?: (dirty: boolean) => void;
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
		mentionCandidates = [],
		onDirtyChange
	}: Props = $props();

	/** Edit mode: same composer, but it saves an existing post. */
	let editing = $derived(!!editingPost);

	let resolvedPlaceholder = $derived(placeholder ?? t('page48.composer.placeholder'));

	// Matches the backend limit (CreatePostRequest.content: max_length=2000).
	const MAX_CONTENT_LENGTH = 2000;

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
	/** Ordered media strip: the post's own media (edit) plus newly picked files. */
	// svelte-ignore state_referenced_locally
	let media = $state<DraftMedia[]>(
		(editingPost?.media ?? []).map((item) => ({ kind: 'existing', item }) as DraftMedia)
	);
	let probing = $state(false);
	/** Highlight the composer while files are dragged over it. */
	let dragOver = $state(false);
	/** Index of the media tile being dragged, to reorder it. */
	let dragIndex = $state<number | null>(null);
	let isSubmitting = $state(false);
	let emojiOpen = $state(false);
	let pollOpen = $state(false);
	/** Mark the active draft as a spoiler (each thread item carries its own flag). */
	// svelte-ignore state_referenced_locally
	let spoilerOn = $state(editingPost?.isSpoiler ?? false);
	/**
	 * Who may reply to the post being composed. Each post is independent (a thread
	 * can set it per item), so the active draft keeps its own value here.
	 */
	// svelte-ignore state_referenced_locally
	let replySettings = $state<Page48ReplySetting>(editingPost?.replySettings ?? 'everyone');
	/** Anchor + target of the "Who can reply?" panel; null means the active draft. */
	let audienceOpen = $state(false);
	let audienceAnchor = $state<HTMLElement>();
	let audienceThreadIndex = $state<number | null>(null);
	let audienceIcon = $derived(REPLY_AUDIENCE_ICONS[replySettings]);
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
	/** Anchor + target of the emoji picker; `emojiThreadIndex` null means the active draft. */
	let emojiAnchor = $state<HTMLElement>();
	let emojiThreadIndex = $state<number | null>(null);
	let fileInput = $state<HTMLInputElement>();
	/** Shared picker for adding media to an existing thread post (not the active one). */
	let threadFileInput = $state<HTMLInputElement>();
	let threadMediaTarget = $state<number | null>(null);
	/** Which thread post is currently validating/reading its picked files. */
	let threadMediaBusy = $state<number | null>(null);

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

	/** Grow a textarea to fit its content; used by the inline thread post editors. */
	function autosize(node: HTMLTextAreaElement, _value: string) {
		const resize = () => {
			node.style.height = 'auto';
			node.style.height = `${node.scrollHeight}px`;
		};
		// Measure only after the value binding and layout settle: doing it synchronously
		// at mount can run before the textarea's value is applied, collapsing a long
		// multi-line post to a single row until the user focuses or types.
		requestAnimationFrame(resize);
		node.addEventListener('input', resize);
		// Safety net for the "click / place cursor / tap" case.
		node.addEventListener('focus', resize);
		// A width change re-wraps the text, so re-measure (height changes are ignored
		// to avoid feeding our own resize back into the observer).
		let lastWidth = node.clientWidth;
		const observer = new ResizeObserver(() => {
			if (node.clientWidth === lastWidth) return;
			lastWidth = node.clientWidth;
			resize();
		});
		observer.observe(node);
		return {
			// Fires when the bound value changes programmatically (e.g. emoji inserted).
			update() {
				void tick().then(resize);
			},
			destroy() {
				node.removeEventListener('input', resize);
				node.removeEventListener('focus', resize);
				observer.disconnect();
			}
		};
	}

	// Live formatting: hashtags, mentions, links and markers are styled as they are typed.
	// `parseEditor` keeps the marker characters so this highlight layer stays the same length
	// as the textarea (see `markerClass` — every style here is width-neutral).
	let contentParts = $derived(parseEditor(content));
	// Live preview of a YouTube or X link, so the author sees the embed before posting.
	let postEmbed = $derived(findPostEmbed(contentParts));
	// Consecutive quote parts share one bar, mirroring how the published post renders them.
	let contentSegments = $derived.by(() => {
		const groups: { quote: boolean; parts: EditorPart[] }[] = [];
		for (const part of contentParts) {
			const quote = !!part.quote;
			const last = groups[groups.length - 1];
			if (last && last.quote === quote) last.parts.push(part);
			else groups.push({ quote, parts: [part] });
		}
		return groups;
	});

	/**
	 * Classes for a live formatting run. They must not change glyph advance widths, or the
	 * coloured layer would drift away from the transparent text in the textarea: bold is a
	 * stroke (not a heavier weight), italic is a skew (not a slanted face) and code is a
	 * background (not a monospace font).
	 */
	function markerClass(part: EditorPart): string {
		const classes: string[] = [];
		if (part.bold) classes.push('editor-bold');
		if (part.italic) classes.push('editor-italic');
		if (part.underline) classes.push('editor-underline');
		if (part.strike) classes.push('editor-strike');
		if (part.code) classes.push('editor-code');
		return classes.join(' ');
	}

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

	/** Open/close the emoji picker for the active draft (`index` null) or a thread post. */
	function toggleEmoji(anchor: HTMLElement | undefined, index: number | null) {
		if (emojiOpen && emojiThreadIndex === index) {
			emojiOpen = false;
			return;
		}
		emojiAnchor = anchor;
		emojiThreadIndex = index;
		emojiOpen = true;
	}

	/** Open/close the "Who can reply?" panel for the active draft (`index` null) or a thread post. */
	function toggleAudience(anchor: HTMLElement | undefined, index: number | null) {
		if (audienceOpen && audienceThreadIndex === index) {
			audienceOpen = false;
			return;
		}
		audienceAnchor = anchor;
		audienceThreadIndex = index;
		audienceOpen = true;
	}

	/** Apply a choice to whichever draft opened the panel. */
	function selectAudience(setting: Page48ReplySetting) {
		const index = audienceThreadIndex;
		if (index === null) {
			replySettings = setting;
			return;
		}
		const item = threadItems[index];
		if (item) item.replySettings = setting;
	}

	/** The setting the open panel reflects: the active draft, or a queued thread post. */
	function audienceValue(): Page48ReplySetting {
		if (audienceThreadIndex === null) return replySettings;
		return threadItems[audienceThreadIndex]?.replySettings ?? 'everyone';
	}

	/** Insert an emoji into whichever draft opened the picker. */
	async function insertEmoji(char: string) {
		const index = emojiThreadIndex;
		if (index === null) {
			// Active draft: insert at the caret and keep focus there.
			await insertAtCaret(char);
			return;
		}

		const item = threadItems[index];
		if (!item) return;
		if (item.content.length + char.length > MAX_CONTENT_LENGTH) {
			showToast(t('page48.composer.emojiTooLong'), 'error');
			return;
		}
		item.content += char;
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

	/**
	 * Validate picked files and shape them into draft entries, up to `room` of them.
	 * Shared by the active composer and the per-thread-post media picker.
	 */
	async function buildMediaDrafts(files: File[], room: number): Promise<DraftMedia[]> {
		const picked: DraftMedia[] = [];
		probing = true;
		try {
			for (const file of files.slice(0, room)) {
				const draft = await buildMediaDraft(file);
				if (!draft) continue;
				picked.push({ kind: 'new', draft, preview: URL.createObjectURL(file) });
			}
		} finally {
			probing = false;
		}
		return picked;
	}

	/** Add any mix of photos and videos to the active draft; up to `PAGE48_MAX_MEDIA`. */
	async function addMediaFiles(files: File[]) {
		if (files.length === 0) return;

		const room = PAGE48_MAX_MEDIA - media.length;
		if (room <= 0) {
			showToast(t('page48.composer.maxMedia'), 'error');
			return;
		}

		media = [...media, ...(await buildMediaDrafts(files, room))];
	}

	async function handleMediaSelect(e: Event) {
		const target = e.target as HTMLInputElement;
		const files = Array.from(target.files ?? []);
		target.value = '';
		await addMediaFiles(files);
	}

	/** Open the picker that adds media to a queued thread post instead of the active one. */
	function openThreadMediaPicker(index: number) {
		threadMediaTarget = index;
		threadFileInput?.click();
	}

	async function handleThreadMediaSelect(e: Event) {
		const target = e.target as HTMLInputElement;
		const files = Array.from(target.files ?? []);
		target.value = '';
		const index = threadMediaTarget;
		threadMediaTarget = null;
		if (index === null || files.length === 0) return;

		const item = threadItems[index];
		if (!item) return;
		const room = PAGE48_MAX_MEDIA - item.media.length;
		if (room <= 0) {
			showToast(t('page48.composer.maxMedia'), 'error');
			return;
		}

		threadMediaBusy = index;
		try {
			item.media = [...item.media, ...(await buildMediaDrafts(files, room))];
		} finally {
			threadMediaBusy = null;
		}
	}

	// --- Drag & drop: files to add, tiles to reorder ---

	function handleDragOver(e: DragEvent) {
		if (!e.dataTransfer?.types.includes('Files')) return;
		e.preventDefault();
		dragOver = true;
	}

	function handleDragLeave() {
		dragOver = false;
	}

	function handleDrop(e: DragEvent) {
		dragOver = false;
		const files = Array.from(e.dataTransfer?.files ?? []);
		if (files.length === 0) return;
		e.preventDefault();
		void addMediaFiles(files);
	}

	function handleMediaDragStart(index: number, e: DragEvent) {
		dragIndex = index;
		if (e.dataTransfer) {
			e.dataTransfer.effectAllowed = 'move';
			e.dataTransfer.setData('text/plain', String(index));
		}
	}

	function handleMediaDragOver(index: number, e: DragEvent) {
		if (dragIndex === null || dragIndex === index) return;
		e.preventDefault();
	}

	function handleMediaDrop(index: number, e: DragEvent) {
		if (dragIndex === null) return;
		e.preventDefault();
		e.stopPropagation();
		const from = dragIndex;
		dragIndex = null;
		if (from === index) return;

		const next = [...media];
		const [moved] = next.splice(from, 1);
		next.splice(index, 0, moved);
		media = next;
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

	/** Release blob URLs held by draft media (only newly picked files own one). */
	function revokeDraftMedia(entries: DraftMedia[]) {
		entries.forEach((entry) => {
			if (entry.kind === 'new') URL.revokeObjectURL(entry.preview);
		});
	}

	function removeMedia(index: number) {
		const entry = media[index];
		if (entry?.kind === 'new') URL.revokeObjectURL(entry.preview);
		media = media.filter((_, i) => i !== index);
	}

	/** The post currently being edited, in the shape the API expects. */
	function currentDraft(): PostDraftInput {
		return {
			content,
			media: [...media],
			poll: pollOpen ? { options: pollDraft } : null,
			quotedPostId: quote?.postId ?? null,
			isSpoiler: spoilerOn,
			replySettings
		};
	}

	function draftHasContent(draft: PostDraftInput): boolean {
		return (
			draft.content.trim().length > 0 ||
			draft.media.length > 0 ||
			(!!draft.poll && draft.poll.options.length >= POLL_MIN_OPTIONS) ||
			!!draft.quotedPostId
		);
	}

	/**
	 * Clear the active draft. `releaseMedia` is false when the media is handed off
	 * to a thread post, which keeps ownership of the same blob URLs.
	 */
	function resetDraft(releaseMedia = true) {
		content = '';
		if (releaseMedia) revokeDraftMedia(media);
		media = [];
		closePoll();
		spoilerOn = false;
		replySettings = 'everyone';
		audienceOpen = false;
		audienceThreadIndex = null;
		quoteOverride = undefined;
		emojiOpen = false;
		emojiThreadIndex = null;
		void tick().then(() => {
			if (textareaEl) textareaEl.style.height = 'auto';
		});
	}

	/** Park the current draft as a thread post and start a fresh one. */
	function addToThread() {
		const draft = currentDraft();
		if (!draftHasContent(draft)) return;

		threadItems = [...threadItems, draft];
		// The media moved into the thread post, so its blob URLs must stay alive.
		resetDraft(false);
	}

	function removeThreadItem(index: number) {
		const item = threadItems[index];
		if (item) revokeDraftMedia(item.media);
		threadItems = threadItems.filter((_, i) => i !== index);
		// Indices shifted, so an open picker would point at the wrong post.
		emojiOpen = false;
		emojiThreadIndex = null;
		audienceOpen = false;
		audienceThreadIndex = null;
	}

	/** Remove one media tile from a queued thread post. */
	function removeThreadMedia(itemIndex: number, mediaIndex: number) {
		const item = threadItems[itemIndex];
		if (!item) return;
		const entry = item.media[mediaIndex];
		if (entry?.kind === 'new') URL.revokeObjectURL(entry.preview);
		item.media = item.media.filter((_, i) => i !== mediaIndex);
	}

	// Poll editor (a poll can't be combined with media)
	function dropMedia() {
		revokeDraftMedia(media);
		media = [];
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

	/** Mirror the post counter colours: amber near the limit, red at the limit. */
	function contentCounterClass(length: number) {
		if (length >= MAX_CONTENT_LENGTH) return 'text-red-500';
		if (length >= MAX_CONTENT_LENGTH - 50) return 'text-amber-500';
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
					only.isSpoiler ?? false,
					only.replySettings ?? 'everyone'
				);
			}
			threadItems.forEach((item) => revokeDraftMedia(item.media));
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

	/** Whether the media strip still matches the post being edited (same items and order). */
	function mediaUnchanged(original: Page48Post['media']): boolean {
		if (media.length !== original.length) return false;
		return media.every(
			(entry, i) => entry.kind === 'existing' && entry.item.filename === original[i]?.filename
		);
	}

	/**
	 * Whether the user has unsaved work worth warning about. In edit mode this means
	 * the draft diverges from the original post; in create mode any content counts.
	 * A quote merely seeded by the host is not the user's doing (only a pasted one is).
	 */
	let hasDraft = $derived.by(() => {
		if (editing) {
			const original = editingPost;
			if (!original) return false;
			return (
				content.trim() !== (original.content ?? '').trim() ||
				spoilerOn !== (original.isSpoiler ?? false) ||
				replySettings !== (original.replySettings ?? 'everyone') ||
				!mediaUnchanged(original.media ?? [])
			);
		}

		return (
			content.trim().length > 0 ||
			media.length > 0 ||
			(pollOpen && pollDraft.length >= POLL_MIN_OPTIONS) ||
			threadItems.length > 0 ||
			!!quoteOverride
		);
	});

	$effect(() => {
		onDirtyChange?.(hasDraft);
	});

	// The modal owns the draft; release its blob URLs if it is closed without posting.
	onDestroy(() => {
		revokeDraftMedia(media);
		threadItems.forEach((item) => revokeDraftMedia(item.media));
	});
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

<!-- The author's avatar, reused for every thread post and the active composer. -->
{#snippet composerAvatar(sizeClass: string)}
	<div
		class={`${sizeClass} rounded-full overflow-hidden bg-gray-100 dark:bg-zinc-800 ring-2 ring-white dark:ring-zinc-900 shadow-sm`}
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
			<div class="w-full h-full bg-red-100 flex items-center justify-center text-red-500 font-bold">
				?
			</div>
		{/if}
	</div>
{/snippet}

<!-- Who-can-reply control for one queued thread post (each post is independent). -->
{#snippet threadAudienceButton(item: PostDraftInput, index: number)}
	{@const Icon = REPLY_AUDIENCE_ICONS[item.replySettings ?? 'everyone']}
	<button
		type="button"
		class="shrink-0 p-1.5 rounded-full text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
		onclick={(e) => toggleAudience(e.currentTarget, index)}
		disabled={isSubmitting}
		title={t('page48.replyAudience.title')}
		aria-label={t('page48.replyAudience.title')}
		aria-haspopup="dialog"
		aria-expanded={audienceOpen && audienceThreadIndex === index}
	>
		<Icon size={15} />
	</button>
{/snippet}

<!-- Who-can-reply control on the active draft (posts, threads and replies). -->
{#snippet activeAudienceButton()}
	{@const AudienceIcon = audienceIcon}
	<button
		class="p-2 rounded-full transition-all disabled:opacity-50 group cursor-pointer text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10"
		onclick={(e) => toggleAudience(e.currentTarget, null)}
		disabled={isSubmitting}
		title={t('page48.replyAudience.title')}
		aria-label={t('page48.replyAudience.title')}
		aria-haspopup="dialog"
		aria-expanded={audienceOpen && audienceThreadIndex === null}
	>
		<AudienceIcon size={20} class="group-hover:scale-110 transition-transform" />
	</button>
{/snippet}

<!-- One run of the live formatting layer painted behind the textarea. -->
{#snippet editorPart(part: EditorPart)}
	{@const mk = markerClass(part)}
	{#if part.marker}
		<span class="editor-marker">{part.text}</span>
	{:else if part.tag}
		<span class="text-red-500 {mk}">{part.text}</span>
	{:else if part.mention}
		<span class="font-semibold text-red-500 {mk}">{part.text}</span>
	{:else if part.link}
		<span class="text-blue-500 {mk}">{part.text}</span>
	{:else if part.spoiler}
		<span class="spoiler-hidden {mk}">{part.text}</span>
	{:else}
		<span class={mk}>{part.text}</span>
	{/if}
{/snippet}

<!-- A drop target for files, not a landmark; the textarea/submit stay the controls. -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
	class={`py-5 px-5 sm:px-6 border-b border-gray-100 dark:border-white/10 bg-white/60 dark:bg-zinc-950/60 backdrop-blur-xl transition-all ${dragOver ? 'ring-2 ring-inset ring-red-400/70' : ''}`}
	ondragover={handleDragOver}
	ondragleave={handleDragLeave}
	ondrop={handleDrop}
>
	<!-- Queued thread posts: each one stays editable, with its own avatar rail. -->
	{#each threadItems as item, i (item)}
		<div class="flex gap-3" in:fade>
			<div class="flex shrink-0 flex-col items-center self-stretch pt-1">
				{@render composerAvatar('w-10 h-10')}
				<div class="my-1 w-0.5 flex-1 rounded-full bg-gray-200 dark:bg-zinc-800"></div>
			</div>

			<div class="min-w-0 flex-1 pb-4">
				<div class="flex items-start gap-2">
					<span
						class="mt-1 shrink-0 text-[11px] font-bold tabular-nums text-gray-300 dark:text-zinc-600"
					>
						{i + 1}
					</span>
					<textarea
						use:autosize={item.content}
						bind:value={item.content}
						maxlength={MAX_CONTENT_LENGTH}
						placeholder={resolvedPlaceholder}
						rows="1"
						class={`block min-w-0 flex-1 resize-none bg-transparent outline-none placeholder:text-gray-400 dark:placeholder:text-gray-500 ${CONTENT_TEXT_CLASS}`}
					></textarea>
					<!-- Character counter for this thread post -->
					{#if item.content.length > 0}
						<span
							class={`mt-1 shrink-0 text-[12px] font-medium tabular-nums ${contentCounterClass(
								item.content.length
							)}`}
							aria-live="polite"
						>
							{item.content.length}/{MAX_CONTENT_LENGTH}
						</span>
					{/if}
					<!-- Media picker for this thread post -->
					<button
						type="button"
						class="shrink-0 p-1.5 rounded-full text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
						onclick={() => openThreadMediaPicker(i)}
						disabled={item.media.length >= PAGE48_MAX_MEDIA || probing || isSubmitting}
						title={t('page48.composer.addMedia')}
						aria-label={t('page48.composer.addMedia')}
					>
						{#if threadMediaBusy === i}
							<Loader2 size={15} class="animate-spin" />
						{:else}
							<ImageIcon size={15} />
						{/if}
					</button>
					<!-- Emoji picker for this thread post -->
					<button
						type="button"
						class={`shrink-0 p-1.5 rounded-full transition-colors cursor-pointer hover:bg-red-50 dark:hover:bg-red-500/10 disabled:opacity-40 disabled:cursor-not-allowed ${
							emojiOpen && emojiThreadIndex === i
								? 'text-red-500'
								: 'text-gray-400 hover:text-red-500'
						}`}
						onclick={(e) => toggleEmoji(e.currentTarget, i)}
						disabled={isSubmitting}
						title={t('page48.composer.addEmoji')}
						aria-label={t('page48.composer.addEmoji')}
						aria-haspopup="dialog"
						aria-expanded={emojiOpen && emojiThreadIndex === i}
					>
						<Smile size={15} />
					</button>
					<!-- Spoiler toggle for this thread post -->
					<button
						type="button"
						class={`shrink-0 p-1.5 rounded-full transition-colors cursor-pointer hover:bg-red-50 dark:hover:bg-red-500/10 ${
							item.isSpoiler ? 'text-red-500' : 'text-gray-400 hover:text-red-500'
						}`}
						onclick={() => (item.isSpoiler = !item.isSpoiler)}
						disabled={isSubmitting}
						title={t('page48.spoiler.mark')}
						aria-label={t('page48.spoiler.mark')}
						aria-pressed={item.isSpoiler ?? false}
					>
						<EyeOff size={15} />
					</button>
					{@render threadAudienceButton(item, i)}
					<button
						type="button"
						class="shrink-0 p-1.5 rounded-full text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors cursor-pointer"
						onclick={() => removeThreadItem(i)}
						aria-label={t('page48.thread.removePost')}
						title={t('page48.thread.removePost')}
					>
						<X size={15} />
					</button>
				</div>

				<!-- Media previews for this thread post -->
				{#if item.media.length > 0}
					<div class="mt-2 flex gap-2 overflow-x-auto pb-1">
						{#each item.media as entry, mi (entry.kind === 'existing' ? entry.item.filename : entry.preview)}
							{@const isVideo =
								entry.kind === 'existing'
									? entry.item.type === 'video'
									: entry.draft.type === 'video'}
							{@const src =
								entry.kind === 'existing'
									? entry.item.url_small || entry.item.url_medium || entry.item.url
									: entry.preview}
							<div class="relative shrink-0">
								{#if isVideo}
									<video
										{src}
										muted
										playsinline
										class="h-28 w-auto rounded-xl border border-gray-200 dark:border-zinc-800 bg-black"
									></video>
								{:else}
									<img
										{src}
										alt={t('page48.composer.previewAlt')}
										class="h-28 w-auto rounded-xl border border-gray-200 dark:border-zinc-800 object-cover"
									/>
								{/if}
								<button
									type="button"
									class="absolute top-1 right-1 w-6 h-6 bg-black/60 hover:bg-black text-white rounded-full flex items-center justify-center transition-colors cursor-pointer"
									onclick={() => removeThreadMedia(i, mi)}
									aria-label={t('page48.thread.removeMedia')}
									title={t('page48.thread.removeMedia')}
								>
									<X size={13} />
								</button>
							</div>
						{/each}
					</div>
				{/if}

				<!-- Spoiler marker so a marked thread post is recognisable at a glance. -->
				{#if item.isSpoiler}
					<div
						class="mt-2 inline-flex items-center gap-1.5 rounded-full bg-red-50 px-2 py-0.5 text-[11px] font-medium text-red-500 dark:bg-red-500/10"
					>
						<EyeOff size={12} />
						{t('page48.spoiler.badge')}
					</div>
				{/if}

				<!-- Poll and quote can't be edited inline; surface them so they're not lost. -->
				{#if item.poll}
					<div class="mt-2 flex items-center gap-1.5 text-[12px] text-gray-500 dark:text-gray-400">
						<ChartNoAxesColumn size={14} />
						<span>{t('page48.poll.create')}</span>
					</div>
				{/if}
				{#if item.quotedPostId}
					<div class="mt-1.5 text-[12px] text-gray-500 dark:text-gray-400">
						{t('page48.repostMenu.quote')}
					</div>
				{/if}
			</div>
		</div>
	{/each}

	<!-- Shared picker for adding media to a queued thread post. -->
	<input
		type="file"
		accept="image/jpeg,image/png,image/webp,video/mp4,video/webm"
		multiple
		class="hidden"
		bind:this={threadFileInput}
		onchange={handleThreadMediaSelect}
	/>

	<!-- Active composer: the post being written right now -->
	<div class="flex gap-3">
		<div class="shrink-0 pt-1">
			{@render composerAvatar('w-10 h-10')}
		</div>

		<!-- Composer Content -->
		<div class="flex-1 min-w-0 flex flex-col pt-1.5">
			<div class="flex items-center gap-3">
				<div class="relative min-w-0 flex-1">
					<!-- Highlight layer. The textarea's own text is transparent so mentions,
				     hashtags and links can be coloured as they are typed. -->
					<div
						aria-hidden="true"
						class={`pointer-events-none absolute inset-0 select-none overflow-hidden text-gray-900 dark:text-gray-100 ${CONTENT_TEXT_CLASS} ${showToolRow ? 'pb-2' : ''}`}
					>
						{#each contentSegments as segment, i (i)}
							{#if segment.quote}
								<span class="editor-quote">
									{#each segment.parts as part, j (j)}{@render editorPart(part)}{/each}
								</span>
							{:else}
								{#each segment.parts as part, j (j)}{@render editorPart(part)}{/each}
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
			{#if media.length > 0}
				<div class="flex gap-2 mt-2 mb-2 overflow-x-auto pb-2 snap-x" in:fade>
					{#each media as entry, i (entry.kind === 'existing' ? entry.item.filename : entry.preview)}
						{@const isVideo =
							entry.kind === 'existing'
								? entry.item.type === 'video'
								: entry.draft.type === 'video'}
						{@const src =
							entry.kind === 'existing'
								? entry.item.url_small || entry.item.url_medium || entry.item.url
								: entry.preview}
						<!-- Each tile is a movable handle; the remove button stays the control. -->
						<!-- svelte-ignore a11y_no_static_element_interactions -->
						<div
							class={`relative shrink-0 snap-start cursor-grab active:cursor-grabbing ${
								dragIndex === i ? 'opacity-40' : ''
							}`}
							draggable="true"
							ondragstart={(event) => handleMediaDragStart(i, event)}
							ondragover={(event) => handleMediaDragOver(i, event)}
							ondrop={(event) => handleMediaDrop(i, event)}
							ondragend={() => (dragIndex = null)}
							title={t('page48.composer.dragToReorder')}
						>
							{#if isVideo}
								<video
									{src}
									muted
									playsinline
									class="h-32 w-auto rounded-xl border border-gray-200 dark:border-zinc-800 bg-black"
								></video>
							{:else}
								<img
									{src}
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
							disabled={media.length >= PAGE48_MAX_MEDIA || probing || isSubmitting || pollOpen}
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
								emojiOpen && emojiThreadIndex === null
									? 'text-red-500'
									: 'text-gray-400 hover:text-red-500'
							}`}
							onclick={() => toggleEmoji(emojiButton, null)}
							disabled={isSubmitting}
							title={t('page48.composer.addEmoji')}
							aria-label={t('page48.composer.addEmoji')}
							aria-haspopup="dialog"
							aria-expanded={emojiOpen && emojiThreadIndex === null}
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
								disabled={media.length > 0 || probing || isSubmitting || isThread}
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

						<!-- Who can reply: shown on posts, threads, edits and replies alike -->
						{@render activeAudienceButton()}
					</div>

					<!-- Character Counter + Submit Button -->
					<div class="flex items-center gap-3">
						{#if content.length > 0}
							<span
								class={`text-[13px] font-medium tabular-nums ${contentCounterClass(content.length)}`}
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

{#if emojiOpen && emojiAnchor}
	<EmojiPicker anchor={emojiAnchor} onPick={insertEmoji} onClose={() => (emojiOpen = false)} />
{/if}

{#if audienceOpen}
	<ReplyAudiencePicker
		anchor={audienceAnchor}
		value={audienceValue()}
		onSelect={selectAudience}
		onClose={() => (audienceOpen = false)}
	/>
{/if}

<style>
	/* Matches the published inline spoiler: a real blur of the glyphs. */
	.spoiler-hidden {
		filter: blur(6px);
		opacity: 0.8;
		user-select: none;
	}

	/* Live formatting preview. Every rule here is width-neutral on purpose: the highlight
	   layer sits behind the textarea, which renders the same characters in one uniform
	   style, so any change to glyph advance widths would misalign the coloured text. */
	.editor-marker {
		opacity: 0.4;
	}
	.editor-bold {
		-webkit-text-stroke: 0.6px currentColor;
	}
	.editor-italic {
		display: inline-block;
		transform: skewX(-9deg);
	}
	.editor-underline {
		text-decoration: underline;
	}
	.editor-strike {
		text-decoration: line-through;
	}
	.editor-code {
		background: rgb(0 0 0 / 0.07);
		border-radius: 3px;
	}
	:global(.dark) .editor-code {
		background: rgb(255 255 255 / 0.12);
	}
	/* Quote bar for `> ` lines. Painted as a background (not a border or padding) so it adds
	   no width and the layer stays aligned with the textarea. */
	.editor-quote {
		background-image: linear-gradient(to right, rgb(0 0 0 / 0.22) 0 3px, transparent 3px);
	}
	:global(.dark) .editor-quote {
		background-image: linear-gradient(to right, rgb(255 255 255 / 0.32) 0 3px, transparent 3px);
	}
</style>
