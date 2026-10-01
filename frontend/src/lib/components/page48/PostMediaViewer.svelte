<script lang="ts">
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { fade, scale } from 'svelte/transition';
	import {
		X,
		ChevronLeft,
		ChevronRight,
		Download,
		PanelRightClose,
		PanelRightOpen
	} from 'lucide-svelte';
	import type { Page48Post } from '$lib/api/page48';
	import PostDetailContent from '$lib/components/page48/PostDetailContent.svelte';
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
	let images = $derived(post.images ?? []);
	let currentUrl = $derived(images[index]?.url ?? '');

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
		index = Math.max(0, Math.min(next, images.length - 1));
	}

	/** Same behaviour as the single-image lightbox: save the shown photo. */
	async function downloadImage() {
		const src = currentUrl;
		if (!src) return;
		try {
			const response = await fetch(src);
			const blob = await response.blob();
			const url = window.URL.createObjectURL(blob);
			const link = document.createElement('a');
			link.href = url;

			const name = src.split('/').pop()?.split('?')[0] || `page48-${index + 1}`;
			link.download = name.includes('.') ? name : `${name}.jpg`;

			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);
			window.URL.revokeObjectURL(url);
		} catch (error) {
			console.error('Download failed:', error);
			window.open(src, '_blank');
		}
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
		<div class="relative flex min-w-0 flex-1 items-center justify-center">
			<!-- Clicking the empty space around the photo closes the viewer. -->
			<div class="absolute inset-0" onclick={onClose} role="presentation"></div>

			{#if currentUrl}
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
				{#if images.length > 1}
					<span
						class="rounded-full border border-white/10 bg-zinc-900/80 px-3 py-1.5 font-mono text-xs font-bold tabular-nums text-white backdrop-blur-md"
					>
						{index + 1} / {images.length}
					</span>
				{/if}
				<button
					class="flex cursor-pointer items-center rounded-full border border-white/10 bg-zinc-900/80 p-2.5 text-white backdrop-blur-md transition-colors hover:bg-zinc-800"
					onclick={downloadImage}
					aria-label={t('page48.mediaViewer.download')}
					title={t('page48.mediaViewer.download')}
				>
					<Download class="h-5 w-5" />
				</button>
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

			{#if images.length > 1}
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
					disabled={index >= images.length - 1}
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
</style>
