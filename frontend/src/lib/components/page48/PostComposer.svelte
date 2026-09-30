<script lang="ts">
	import {
		Image as ImageIcon,
		ChartNoAxesColumn,
		Plus,
		Smile,
		Trash2,
		Video as VideoIcon,
		X,
		Loader2
	} from 'lucide-svelte';
	import { onMount, tick } from 'svelte';
	import { fade } from 'svelte/transition';
	import EmojiPicker from '$lib/components/page48/EmojiPicker.svelte';
	import QuotedPostCard from '$lib/components/page48/QuotedPostCard.svelte';
	import type { Page48Post } from '$lib/api/page48';
	import { userProfile } from '$lib/stores/profile.svelte';
	import { showToast } from '$lib/stores/toast.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import {
		probeVideo,
		PAGE48_IMAGE_MAX_BYTES,
		PAGE48_MAX_IMAGES,
		PAGE48_VIDEO_ALLOWED_TYPES,
		PAGE48_VIDEO_MAX_BYTES,
		PAGE48_VIDEO_MAX_SECONDS,
		POLL_MAX_OPTION_LENGTH,
		POLL_MAX_OPTIONS,
		POLL_MIN_OPTIONS,
		type PostDraftInput,
		type VideoDraft
	} from '$lib/utils/page48';

	const { t } = useTranslation();

	interface Props {
		onPost: (
			content: string,
			images: File[],
			video: VideoDraft | null,
			poll: { options: string[] } | null
		) => Promise<void>;
		/** Only provided where threads make sense (the feed, not the reply composer). */
		onPostThread?: (drafts: PostDraftInput[]) => Promise<void>;
		isReply?: boolean;
		placeholder?: string;
		/** Focus the textarea on mount (e.g. when the composer is opened in a modal). */
		autofocus?: boolean;
		/** When set, this composer publishes a quote of that post. */
		quotedPost?: Page48Post | null;
		onRemoveQuote?: () => void;
	}

	let {
		onPost,
		onPostThread,
		isReply = false,
		placeholder,
		autofocus = false,
		quotedPost = null,
		onRemoveQuote
	}: Props = $props();

	let resolvedPlaceholder = $derived(placeholder ?? t('page48.composer.placeholder'));

	// Matches the backend limit (CreatePostRequest.content: max_length=500).
	const MAX_CONTENT_LENGTH = 500;

	let content = $state('');
	let images = $state<File[]>([]);
	let imagePreviews = $state<string[]>([]);
	let video = $state<VideoDraft | null>(null);
	let videoPreview = $state<string | null>(null);
	let probing = $state(false);
	let isSubmitting = $state(false);
	let emojiOpen = $state(false);
	let pollOpen = $state(false);
	/** Reply mode hides the tool row until the user engages the composer. */
	let composerActive = $state(false);
	let pollOptions = $state<string[]>(['', '']);
	/** Posts already queued for the thread (the active draft is the one below). */
	let threadItems = $state<PostDraftInput[]>([]);
	let textareaEl = $state<HTMLTextAreaElement>();
	let emojiButton = $state<HTMLButtonElement>();
	let fileInput = $state<HTMLInputElement>();
	let videoInput = $state<HTMLInputElement>();

	// Focus when the composer is opened as a modal. Deferred by one frame because the
	// modal is portalled (its node is moved to <body> right after mount), and moving a
	// node in the DOM blurs anything focused inside it during that same mount pass.
	onMount(() => {
		if (!autofocus) return;
		requestAnimationFrame(() => textareaEl?.focus());
	});

	function autoGrow(el: HTMLTextAreaElement) {
		el.style.height = 'auto';
		el.style.height = el.scrollHeight + 'px';
	}

	/** Insert an emoji at the caret, keeping focus and the caret in the textarea. */
	async function insertEmoji(char: string) {
		const el = textareaEl;
		if (!el) {
			if (content.length + char.length <= MAX_CONTENT_LENGTH) content += char;
			return;
		}

		const start = el.selectionStart ?? content.length;
		const end = el.selectionEnd ?? start;
		if (content.length - (end - start) + char.length > MAX_CONTENT_LENGTH) {
			showToast(t('page48.composer.emojiTooLong'), 'error');
			return;
		}

		content = content.slice(0, start) + char + content.slice(end);
		const caret = start + char.length;

		await tick();
		el.focus();
		el.setSelectionRange(caret, caret);
		autoGrow(el);
	}

	function handleFileSelect(e: Event) {
		const target = e.target as HTMLInputElement;
		if (!target.files) return;

		const newFiles = Array.from(target.files);
		if (images.length + newFiles.length > PAGE48_MAX_IMAGES) {
			alert(t('page48.composer.maxPhotos'));
			return;
		}

		for (const file of newFiles) {
			if (!file.type.startsWith('image/')) continue;
			if (file.size > PAGE48_IMAGE_MAX_BYTES) {
				alert(t('page48.composer.maxSize'));
				continue;
			}
			images = [...images, file];
			imagePreviews = [...imagePreviews, URL.createObjectURL(file)];
		}

		// Images and a video can't be combined: picking images drops the video.
		if (images.length > 0) clearVideo();

		// Reset input
		target.value = '';
	}

	function removeImage(index: number) {
		URL.revokeObjectURL(imagePreviews[index]);
		images = images.filter((_, i) => i !== index);
		imagePreviews = imagePreviews.filter((_, i) => i !== index);
	}

	async function handleVideoSelect(e: Event) {
		const target = e.target as HTMLInputElement;
		const file = target.files?.[0];
		target.value = '';
		if (!file) return;

		if (!PAGE48_VIDEO_ALLOWED_TYPES.includes(file.type)) {
			showToast(t('page48.composer.videoInvalidType'), 'error');
			return;
		}
		if (file.size > PAGE48_VIDEO_MAX_BYTES) {
			showToast(t('page48.composer.videoTooLarge'), 'error');
			return;
		}

		probing = true;
		try {
			const meta = await probeVideo(file);
			if (!Number.isFinite(meta.duration) || meta.duration <= 0) {
				showToast(t('page48.composer.videoUnreadable'), 'error');
				return;
			}
			if (meta.duration > PAGE48_VIDEO_MAX_SECONDS + 0.5) {
				showToast(t('page48.composer.videoTooLong'), 'error');
				return;
			}

			// A video can't be combined with images: drop any attached photos.
			images.forEach((_, i) => URL.revokeObjectURL(imagePreviews[i]));
			images = [];
			imagePreviews = [];

			clearVideo();
			video = {
				file,
				width: meta.width,
				height: meta.height,
				duration: meta.duration
			};
			videoPreview = URL.createObjectURL(file);
		} catch {
			showToast(t('page48.composer.videoUnreadable'), 'error');
		} finally {
			probing = false;
		}
	}

	function clearVideo() {
		if (videoPreview) URL.revokeObjectURL(videoPreview);
		videoPreview = null;
		video = null;
	}

	/** The post currently being edited, in the shape the API expects. */
	function currentDraft(): PostDraftInput {
		return {
			content,
			images: [...images],
			video,
			poll: pollOpen ? { options: pollDraft } : null
		};
	}

	function draftHasContent(draft: PostDraftInput): boolean {
		return (
			draft.content.trim().length > 0 ||
			draft.images.length > 0 ||
			!!draft.video ||
			(!!draft.poll && draft.poll.options.length >= POLL_MIN_OPTIONS)
		);
	}

	function resetDraft() {
		content = '';
		images = [];
		imagePreviews.forEach(URL.revokeObjectURL);
		imagePreviews = [];
		clearVideo();
		closePoll();
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
		if (draft.images.length > 0)
			parts.push(t('page48.aria.imageCount', { count: draft.images.length }));
		if (draft.video) parts.push(t('page48.composer.addVideo'));
		if (draft.poll) parts.push(t('page48.poll.create'));
		return parts.join(' · ');
	}

	// Poll editor (a poll can't be combined with images or a video)
	function dropMedia() {
		imagePreviews.forEach(URL.revokeObjectURL);
		images = [];
		imagePreviews = [];
		clearVideo();
	}

	function openPoll() {
		dropMedia();
		pollOpen = true;
	}

	function closePoll() {
		pollOpen = false;
		pollOptions = ['', ''];
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
		if (!pollReady || isSubmitting) return;

		const drafts = [...threadItems];
		const active = currentDraft();
		// A quote may be published with no text of its own.
		if (draftHasContent(active) || quotedPost) drafts.push(active);
		if (drafts.length === 0) return;

		// Extra drafts only exist when a thread handler was provided.
		const publishAsThread = drafts.length > 1 && !!onPostThread;

		try {
			isSubmitting = true;
			if (publishAsThread) {
				await onPostThread?.(drafts);
			} else {
				const [only] = drafts;
				await onPost(only.content, only.images, only.video, only.poll);
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
		(draftHasContent(currentDraft()) || threadItems.length > 0 || !!quotedPost) && pollReady
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
		{isThread
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
			<textarea
				bind:this={textareaEl}
				bind:value={content}
				placeholder={resolvedPlaceholder}
				maxlength={MAX_CONTENT_LENGTH}
				class={`min-w-0 flex-1 bg-transparent text-gray-900 dark:text-gray-100 text-[17px] sm:text-[20px] resize-none outline-none placeholder:text-gray-400 dark:placeholder:text-gray-500 leading-relaxed ${showToolRow ? 'pb-2' : ''}`}
				rows="1"
				oninput={(e) => autoGrow(e.target as HTMLTextAreaElement)}
				onfocus={() => (composerActive = true)}
			></textarea>
			{#if !showToolRow}
				{@render submitButton()}
			{/if}
		</div>

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

		<!-- Image Previews -->
		{#if imagePreviews.length > 0}
			<div class="flex gap-2 mt-2 mb-2 overflow-x-auto pb-2 snap-x" in:fade>
				{#each imagePreviews as preview, i}
					<div class="relative shrink-0 snap-start">
						<img
							src={preview}
							alt={t('page48.composer.previewAlt')}
							class="h-32 w-auto rounded-xl border border-gray-200 dark:border-zinc-800 object-cover"
						/>
						<button
							class="absolute top-1 right-1 w-6 h-6 bg-black/60 hover:bg-black text-white rounded-full flex items-center justify-center transition-colors cursor-pointer"
							onclick={() => removeImage(i)}
						>
							<X size={14} />
						</button>
					</div>
				{/each}
			</div>
		{/if}

		<!-- Video Preview -->
		{#if videoPreview}
			<div class="relative mt-2 mb-2 w-full max-w-[320px]" in:fade>
				<video
					src={videoPreview}
					controls
					playsinline
					muted
					class="w-full rounded-xl border border-gray-200 dark:border-zinc-800 bg-black max-h-80"
				></video>
				<button
					class="absolute top-1 right-1 w-6 h-6 bg-black/60 hover:bg-black text-white rounded-full flex items-center justify-center transition-colors cursor-pointer"
					onclick={clearVideo}
					aria-label={t('page48.composer.removeVideo')}
				>
					<X size={14} />
				</button>
			</div>
		{/if}

		<!-- Quoted post being replied to by this composer -->
		{#if quotedPost}
			<QuotedPostCard post={quotedPost} removable onRemove={onRemoveQuote} />
		{/if}

		{#if showToolRow}
			<!-- Action Bar -->
			<div class="flex items-center justify-between mt-3 pt-2 border-t border-transparent">
				<div class="flex items-center gap-1">
					<!-- Image Input -->
					<button
						class="p-2 -ml-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-full transition-all disabled:opacity-50 group cursor-pointer"
						onclick={() => fileInput?.click()}
						disabled={images.length >= PAGE48_MAX_IMAGES ||
							!!video ||
							probing ||
							isSubmitting ||
							pollOpen}
						title={t('page48.composer.addPhoto')}
					>
						<ImageIcon size={20} class="group-hover:scale-110 transition-transform" />
					</button>
					<input
						type="file"
						accept="image/jpeg,image/png,image/webp"
						multiple
						class="hidden"
						bind:this={fileInput}
						onchange={handleFileSelect}
					/>

					<!-- Video Input -->
					<button
						class="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-full transition-all disabled:opacity-50 group cursor-pointer"
						onclick={() => videoInput?.click()}
						disabled={!!video || images.length > 0 || probing || isSubmitting || pollOpen}
						title={t('page48.composer.addVideo')}
					>
						{#if probing}
							<Loader2 size={20} class="animate-spin" />
						{:else}
							<VideoIcon size={20} class="group-hover:scale-110 transition-transform" />
						{/if}
					</button>
					<input
						type="file"
						accept="video/mp4,video/webm"
						class="hidden"
						bind:this={videoInput}
						onchange={handleVideoSelect}
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

					<!-- Poll (not available on replies or quotes) -->
					{#if !isReply && !quotedPost}
						<button
							class={`p-2 rounded-full transition-all disabled:opacity-50 group cursor-pointer hover:bg-red-50 dark:hover:bg-red-500/10 ${
								pollOpen ? 'text-red-500' : 'text-gray-400 hover:text-red-500'
							}`}
							onclick={pollOpen ? closePoll : openPoll}
							disabled={images.length > 0 || !!video || probing || isSubmitting || isThread}
							title={t('page48.poll.create')}
							aria-label={t('page48.poll.create')}
							aria-pressed={pollOpen}
						>
							<ChartNoAxesColumn size={20} class="group-hover:scale-110 transition-transform" />
						</button>
					{/if}
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

{#if emojiOpen}
	<EmojiPicker anchor={emojiButton} onPick={insertEmoji} onClose={() => (emojiOpen = false)} />
{/if}
