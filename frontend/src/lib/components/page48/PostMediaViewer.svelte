<script lang="ts">
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { fade, scale } from 'svelte/transition';
	import {
		X,
		ChevronLeft,
		ChevronRight,
		Download,
		LoaderCircle,
		PanelRightClose,
		PanelRightOpen
	} from 'lucide-svelte';
	import type { Page48Post } from '$lib/api/page48';
	import PostDetailContent from '$lib/components/page48/PostDetailContent.svelte';
	import VideoPlayer from '$lib/components/page48/VideoPlayer.svelte';
	import { viewportStore } from '$lib/stores/viewport.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		post: Page48Post;
		isOpen: boolean;
		/** Photo the user clicked; the viewer opens on it. */
		initialIndex?: number;
		onClose: () => void;
	}

	let { post, isOpen, initialIndex = 0, onClose }: Props = $props();

	const { t } = useTranslation();

	let index = $state(0);
	/** Whether the post + comments pane is shown; toggled from the top-right corner. */
	let detailVisible = $state(true);
	/** True while a download is in flight, so the button can show a spinner. */
	let downloading = $state(false);
	let media = $derived(post.media ?? []);
	let current = $derived(media[index] ?? null);
	let currentUrl = $derived(current?.type === 'image' ? (current.url ?? '') : '');

	/** The detail pane only exists where there is room for it; mobile shows the photo alone. */
	let showDetailPane = $derived(viewportStore.isWide && detailVisible);

	let detailToggleLabel = $derived(
		detailVisible ? t('page48.mediaViewer.hideDetails') : t('page48.mediaViewer.showDetails')
	);

	// Start on the photo that was clicked, with the details open, every time the
	// viewer opens.
	$effect(() => {
		if (isOpen) {
			index = initialIndex;
			detailVisible = true;
		}
	});

	function goTo(next: number) {
		index = Math.max(0, Math.min(next, media.length - 1));
	}

	// Swipe to change photo on touch devices (the arrows are fiddly on a phone).
	const SWIPE_THRESHOLD = 40;
	let touchStartX = 0;
	let touchStartY = 0;
	/** Set when a swipe just navigated, so the click that follows does not close the viewer. */
	let swiped = false;

	function handleTouchStart(e: TouchEvent) {
		touchStartX = e.changedTouches[0].clientX;
		touchStartY = e.changedTouches[0].clientY;
		swiped = false;
	}

	function handleTouchEnd(e: TouchEvent) {
		if (media.length <= 1) return;
		const dx = e.changedTouches[0].clientX - touchStartX;
		const dy = e.changedTouches[0].clientY - touchStartY;
		// Only a mostly-horizontal drag navigates, so a stray vertical move is ignored.
		if (Math.abs(dx) < SWIPE_THRESHOLD || Math.abs(dx) <= Math.abs(dy)) return;
		swiped = true;
		goTo(dx < 0 ? index + 1 : index - 1);
	}

	/** Closing on backdrop click, unless the touch was a swipe. */
	function handleBackdropClick() {
		if (swiped) {
			swiped = false;
			return;
		}
		onClose();
	}

	/**
	 * Media is served from the storage origin, where the browser refuses to hand the
	 * bytes to `fetch` (no CORS headers). Route it through our same-origin proxy so
	 * the download button can save the file instead of falling back to a new tab.
	 */
	function proxiedSrc(src: string): string {
		return src.startsWith('http') ? `/proxy/image?url=${encodeURIComponent(src)}` : src;
	}

	/** Save a media file via a blob download, falling back to a new tab on failure. */
	async function downloadMedia(src: string, fallbackExt: string) {
		if (!src || downloading) return;
		const target = proxiedSrc(src);
		downloading = true;
		try {
			const response = await fetch(target);
			if (!response.ok) throw new Error(`HTTP ${response.status}`);
			const blob = await response.blob();
			const url = window.URL.createObjectURL(blob);
			const link = document.createElement('a');
			link.href = url;

			const name = src.split('/').pop()?.split('?')[0] || `page48-${index + 1}`;
			link.download = name.includes('.') ? name : `${name}.${fallbackExt}`;

			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);
			window.URL.revokeObjectURL(url);
		} catch (error) {
			console.error('Download failed:', error);
			window.open(target, '_blank');
		} finally {
			downloading = false;
		}
	}

	/** Same behaviour as the single-image lightbox: save the shown photo. */
	function downloadImage() {
		void downloadMedia(currentUrl, 'jpg');
	}

	/** Save the shown video. */
	function downloadVideo() {
		void downloadMedia(current.url ?? '', 'mp4');
	}

	// --- Keyboard + scroll lock ----------------------------------------------

	function handleKeyDown(e: KeyboardEvent) {
		if (e.key === 'Escape') onClose();
		if (e.key === 'ArrowLeft') goTo(index - 1);
		if (e.key === 'ArrowRight') goTo(index + 1);
	}

	$effect(() => {
		if (!browser || !isOpen) return;
		document.body.classList.add('modal-open');
		window.addEventListener('keydown', handleKeyDown);
		return () => {
			document.body.classList.remove('modal-open');
			window.removeEventListener('keydown', handleKeyDown);
		};
	});
</script>

{#if isOpen}
	<div
		class="fixed inset-0 z-[10010] flex bg-black/95 backdrop-blur-sm"
		transition:fade={{ duration: 150 }}
		role="dialog"
		aria-modal="true"
		aria-label={t('page48.mediaViewer.title')}
	>
		<!-- Left: the photo being viewed -->
		<div
			class="swipe-area relative flex min-w-0 flex-1 items-center justify-center"
			role="presentation"
			ontouchstart={handleTouchStart}
			ontouchend={handleTouchEnd}
		>
			<!-- Clicking the empty space around the photo closes the viewer. -->
			<div class="absolute inset-0" onclick={handleBackdropClick} role="presentation"></div>

			{#if current?.type === 'video'}
				<div class="relative max-h-[94vh] w-full max-w-[min(94vw,520px)]">
					<VideoPlayer
						src={current.url ?? ''}
						width={current.width}
						height={current.height}
						maxHeight={760}
						autoplay
						controls
						class="pointer-events-auto"
					/>
				</div>
			{:else if currentUrl}
				<img
					src={currentUrl}
					alt={t('page48.aria.media')}
					class="relative max-h-[94vh] max-w-full select-none object-contain shadow-2xl"
					draggable="false"
					in:scale={{ duration: 250, start: 0.95 }}
				/>
			{/if}

			<div class="absolute left-4 top-4 flex items-center gap-2">
				<button
					class="flex cursor-pointer items-center rounded-full border border-white/10 bg-zinc-900/80 p-2.5 text-white backdrop-blur-md transition-colors hover:bg-zinc-800"
					onclick={onClose}
					aria-label={t('page48.aria.close')}
				>
					<X class="h-5 w-5" />
				</button>
				{#if media.length > 1}
					<span
						class="rounded-full border border-white/10 bg-zinc-900/80 px-3 py-1.5 font-mono text-xs font-bold tabular-nums text-white backdrop-blur-md"
					>
						{index + 1} / {media.length}
					</span>
				{/if}
				{#if current?.type === 'image' || current?.type === 'video'}
					{@const downloadLabel =
						current.type === 'video'
							? t('page48.mediaViewer.downloadVideo')
							: t('page48.mediaViewer.download')}
					<button
						class="flex cursor-pointer items-center rounded-full border border-white/10 bg-zinc-900/80 p-2.5 text-white backdrop-blur-md transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed"
						onclick={current.type === 'video' ? downloadVideo : downloadImage}
						disabled={downloading}
						aria-label={downloadLabel}
						title={downloadLabel}
					>
						{#if downloading}
							<LoaderCircle class="h-5 w-5 animate-spin" />
						{:else}
							<Download class="h-5 w-5" />
						{/if}
					</button>
				{/if}
			</div>

			<!-- Toggle the post + comments pane (wide screens only) -->
			{#if viewportStore.isWide}
				<div class="absolute right-4 top-4 flex items-center gap-2">
					<button
						class="flex cursor-pointer items-center rounded-full border border-white/10 bg-zinc-900/80 p-2.5 text-white backdrop-blur-md transition-colors hover:bg-zinc-800"
						onclick={() => (detailVisible = !detailVisible)}
						aria-label={detailToggleLabel}
						title={detailToggleLabel}
					>
						{#if detailVisible}
							<PanelRightClose class="h-5 w-5" />
						{:else}
							<PanelRightOpen class="h-5 w-5" />
						{/if}
					</button>
				</div>
			{/if}

			{#if media.length > 1}
				<button
					class="absolute left-4 top-1/2 -translate-y-1/2 cursor-pointer rounded-full border border-white/10 bg-zinc-900/80 p-2.5 text-white backdrop-blur-md transition-all hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-20"
					onclick={() => goTo(index - 1)}
					disabled={index <= 0}
					aria-label={t('page48.aria.prevImage')}
				>
					<ChevronLeft class="h-6 w-6" />
				</button>
				<button
					class="absolute right-4 top-1/2 -translate-y-1/2 cursor-pointer rounded-full border border-white/10 bg-zinc-900/80 p-2.5 text-white backdrop-blur-md transition-all hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-20"
					onclick={() => goTo(index + 1)}
					disabled={index >= media.length - 1}
					aria-label={t('page48.aria.nextImage')}
				>
					<ChevronRight class="h-6 w-6" />
				</button>
			{/if}
		</div>

		<!--
			Right: the post exactly as the detail page renders it — same component,
			same replies, same reply composer — minus the photo on the left.
		-->
		{#if showDetailPane}
			<aside
				class="flex w-[460px] shrink-0 flex-col border-l border-gray-200 bg-white dark:border-zinc-800 dark:bg-zinc-950 xl:w-[520px]"
			>
				<div class="flex-1 overflow-y-auto overscroll-contain">
					<PostDetailContent
						postId={post.postId}
						hideMedia
						onDeleted={() => {
							onClose();
							void goto('/page48');
						}}
					/>
				</div>
			</aside>
		{/if}
	</div>
{/if}

<style>
	:global(body.modal-open) {
		overflow: hidden;
	}

	/* Left/right swipes navigate; vertical panning stays with the browser so the gesture
	   never fights the page, and pinch-zoom is still available. */
	.swipe-area {
		touch-action: pan-y pinch-zoom;
	}
</style>
