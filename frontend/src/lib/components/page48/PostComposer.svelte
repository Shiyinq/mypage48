<script lang="ts">
	import { Image as ImageIcon, Video as VideoIcon, X, Loader2 } from 'lucide-svelte';
	import { fade } from 'svelte/transition';
	import { userProfile } from '$lib/stores/profile.svelte';
	import { showToast } from '$lib/stores/toast.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import {
		probeVideo,
		PAGE48_VIDEO_ALLOWED_TYPES,
		PAGE48_VIDEO_MAX_BYTES,
		PAGE48_VIDEO_MAX_SECONDS,
		type VideoDraft
	} from '$lib/utils/page48';

	const { t } = useTranslation();

	interface Props {
		onPost: (content: string, images: File[], video: VideoDraft | null) => Promise<void>;
		isReply?: boolean;
		placeholder?: string;
	}

	let { onPost, isReply = false, placeholder }: Props = $props();

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
	let fileInput: HTMLInputElement;
	let videoInput: HTMLInputElement;

	function handleFileSelect(e: Event) {
		const target = e.target as HTMLInputElement;
		if (!target.files) return;

		const newFiles = Array.from(target.files);
		if (images.length + newFiles.length > 4) {
			alert(t('page48.composer.maxPhotos'));
			return;
		}

		for (const file of newFiles) {
			if (!file.type.startsWith('image/')) continue;
			if (file.size > 3 * 1024 * 1024) {
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

	async function handleSubmit() {
		if (!content.trim() && images.length === 0 && !video) return;
		if (isSubmitting) return;

		try {
			isSubmitting = true;
			await onPost(content, images, video);
			content = '';
			images = [];
			imagePreviews.forEach(URL.revokeObjectURL);
			imagePreviews = [];
			clearVideo();
		} catch (error) {
			console.error(error);
		} finally {
			isSubmitting = false;
		}
	}

	let userAvatar = $derived(
		userProfile.data?.profilePicture_small ||
			(userProfile.data
				? `https://ui-avatars.com/api/?name=${encodeURIComponent(userProfile.data.name || '')}&background=fca5a5&color=fff`
				: null)
	);
</script>

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
		<!-- Active Username -->
		{#if userProfile.data}
			<span class="font-semibold text-[15px] tracking-tight text-gray-900 dark:text-gray-100"
				>{userProfile.data.name}</span
			>
		{/if}

		<textarea
			bind:value={content}
			placeholder={resolvedPlaceholder}
			maxlength={MAX_CONTENT_LENGTH}
			class="w-full bg-transparent text-gray-900 dark:text-gray-100 text-[15px] resize-none outline-none placeholder:text-gray-400 dark:placeholder:text-gray-500 mt-1 pb-2 leading-relaxed"
			rows="1"
			oninput={(e) => {
				const target = e.target as HTMLTextAreaElement;
				target.style.height = 'auto';
				target.style.height = target.scrollHeight + 'px';
			}}
		></textarea>

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

		<!-- Action Bar -->
		<div class="flex items-center justify-between mt-3 pt-2 border-t border-transparent">
			<div class="flex items-center gap-1">
				<!-- Image Input -->
				<button
					class="p-2 -ml-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-full transition-all disabled:opacity-50 group cursor-pointer"
					onclick={() => fileInput.click()}
					disabled={images.length >= 4 || !!video || probing || isSubmitting}
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
					onclick={() => videoInput.click()}
					disabled={!!video || images.length > 0 || probing || isSubmitting}
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

				<button
					class="px-5 py-2 bg-black dark:bg-white text-white dark:text-black rounded-full font-semibold text-[14px] disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer hover:bg-gray-800 dark:hover:bg-gray-200 transition-all flex items-center gap-2 active:scale-95 shadow-sm"
					disabled={(!content.trim() && images.length === 0 && !video) || isSubmitting || probing}
					onclick={handleSubmit}
				>
					{#if isSubmitting}
						<Loader2 size={16} class="animate-spin" />
					{/if}
					{isReply ? t('page48.composer.reply') : t('page48.composer.submit')}
				</button>
			</div>
		</div>
	</div>
</div>
