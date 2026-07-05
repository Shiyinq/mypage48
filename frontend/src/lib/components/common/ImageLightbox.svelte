<script lang="ts">
	import { fade, scale } from 'svelte/transition';
	import {
		X,
		ZoomIn,
		ZoomOut,
		RotateCcw,
		Download,
		ChevronLeft,
		ChevronRight
	} from 'lucide-svelte';
	import { browser } from '$app/environment';

	interface Props {
		src?: string;
		alt?: string;
		images?: string[];
		currentIndex?: number;
		onIndexChange?: (index: number) => void;
		isOpen?: boolean;
		onClose?: () => void;
	}

	let {
		src: singleSrc = '',
		alt = '',
		images = [],
		currentIndex = 0,
		onIndexChange = (_i: number) => {},
		isOpen = false,
		onClose = () => {}
	}: Props = $props();

	let isGallery = $derived(images.length > 1);
	let src = $derived(isGallery ? images[currentIndex] || '' : singleSrc);

	function goTo(index: number) {
		if (!isGallery) return;
		const clamped = Math.max(0, Math.min(index, images.length - 1));
		if (clamped !== currentIndex) {
			onIndexChange(clamped);
			resetZoom();
		}
	}

	function goNext() {
		goTo(currentIndex + 1);
	}

	function goPrev() {
		goTo(currentIndex - 1);
	}

	let zoomScale = $state(1);
	let translateX = $state(0);
	let translateY = $state(0);
	let isDragging = false;
	let startX = 0;
	let startY = 0;
	let isSwiping = false;

	function resetZoom() {
		zoomScale = 1;
		translateX = 0;
		translateY = 0;
	}

	function handleZoomIn() {
		zoomScale = Math.min(zoomScale + 0.5, 5);
	}

	function handleZoomOut() {
		zoomScale = Math.max(zoomScale - 0.5, 0.5);
		if (zoomScale === 1) resetZoom();
	}

	function handleMouseDown(e: MouseEvent) {
		isDragging = true;
		startX = e.clientX - translateX;
		startY = e.clientY - translateY;
	}

	function handleMouseMove(e: MouseEvent) {
		if (!isDragging) return;
		translateX = e.clientX - startX;
		translateY = e.clientY - startY;
	}

	function handleTouchStart(e: Event) {
		const touchEvent = e as TouchEvent;
		if (touchEvent.touches.length === 1) {
			isDragging = true;
			isSwiping = true;
			startX = touchEvent.touches[0].clientX - translateX;
			startY = touchEvent.touches[0].clientY - translateY;
		}
	}

	function handleTouchMove(e: Event) {
		const touchEvent = e as TouchEvent;
		if (!isDragging || touchEvent.touches.length !== 1) return;
		translateX = touchEvent.touches[0].clientX - startX;
		translateY = touchEvent.touches[0].clientY - startY;
	}

	function handleTouchEnd() {
		if (isSwiping && isGallery && zoomScale === 1) {
			const swipeThreshold = 50;
			const dx = translateX;
			if (Math.abs(dx) > swipeThreshold) {
				if (dx < 0) goNext();
				else goPrev();
			}
		}
		isDragging = false;
		isSwiping = false;
		resetZoom();
	}

	function handleMouseUp() {
		isDragging = false;
		isSwiping = false;
	}

	function handleKeyDown(e: KeyboardEvent) {
		if (!isOpen) return;
		if (e.key === 'Escape') onClose();
		if (e.key === '+') handleZoomIn();
		if (e.key === '-') handleZoomOut();
		if (e.key === 'ArrowLeft') goPrev();
		if (e.key === 'ArrowRight') goNext();
	}

	async function downloadImage() {
		try {
			const response = await fetch(src);
			const blob = await response.blob();
			const url = window.URL.createObjectURL(blob);
			const link = document.createElement('a');
			link.href = url;

			const filename = src.split('/').pop()?.split('?')[0] || alt || 'image';
			link.download = filename.includes('.') ? filename : `${filename}.jpg`;

			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);
			window.URL.revokeObjectURL(url);
		} catch (error) {
			console.error('Download failed:', error);
			window.open(src, '_blank');
		}
	}

	function handleWheel(e: WheelEvent) {
		if (e.deltaY < 0) {
			handleZoomIn();
		} else {
			handleZoomOut();
		}
	}

	$effect(() => {
		if (browser && isOpen) {
			document.body.classList.add('modal-open');
			window.addEventListener('keydown', handleKeyDown);
			return () => {
				document.body.classList.remove('modal-open');
				window.removeEventListener('keydown', handleKeyDown);
			};
		}
	});

	$effect(() => {
		if (!isOpen) resetZoom();
	});
</script>

{#if isOpen}
	<div
		class="fixed inset-0 z-[10010] flex items-center justify-center transition-all"
		transition:fade={{ duration: 200 }}
		role="dialog"
		aria-modal="true"
		aria-label="Image lightbox"
	>
		<!-- Backdrop -->
		<div
			class="absolute inset-0 bg-black/95 backdrop-blur-sm cursor-pointer"
			onclick={onClose}
			role="presentation"
		></div>

		<!-- Top Controls -->
		<div class="fixed top-4 right-4 md:top-6 md:right-6 flex items-center gap-2 md:gap-4 z-[10011]">
			{#if isGallery}
				<div
					class="flex items-center gap-1 md:gap-2 bg-zinc-900/80 backdrop-blur-md px-3 py-1.5 md:px-4 md:py-2 rounded-full border border-white/10 shadow-2xl"
				>
					<span class="text-white text-xs md:text-sm font-mono font-bold tabular-nums">
						{currentIndex + 1} / {images.length}
					</span>
				</div>
			{/if}
			<div
				class="flex items-center gap-1 md:gap-2 bg-zinc-900/80 backdrop-blur-md p-1 md:p-1.5 rounded-full border border-white/10 shadow-2xl"
			>
				<button
					onclick={handleZoomOut}
					class="p-1.5 md:p-2 hover:bg-white/10 rounded-full transition-colors text-white cursor-pointer"
					title="Zoom Out"
					aria-label="Zoom out"
				>
					<ZoomOut class="w-4 h-4 md:w-5 md:h-5" />
				</button>
				<div class="w-8 md:w-12 text-center text-white text-[10px] md:text-xs font-mono font-bold">
					{Math.round(zoomScale * 100)}%
				</div>
				<button
					onclick={handleZoomIn}
					class="p-1.5 md:p-2 hover:bg-white/10 rounded-full transition-colors text-white cursor-pointer"
					title="Zoom In"
					aria-label="Zoom in"
				>
					<ZoomIn class="w-4 h-4 md:w-5 md:h-5" />
				</button>
			</div>

			<button
				onclick={resetZoom}
				class="flex p-2.5 md:p-3 bg-zinc-900/80 hover:bg-zinc-800 backdrop-blur-md rounded-full transition-all text-white border border-white/10 shadow-2xl cursor-pointer"
				title="Reset Zoom"
				aria-label="Reset zoom"
			>
				<RotateCcw class="w-4 h-4 md:w-5 md:h-5" />
			</button>

			<button
				onclick={downloadImage}
				class="flex p-2.5 md:p-3 bg-zinc-900/80 hover:bg-zinc-800 backdrop-blur-md rounded-full transition-all text-white border border-white/10 shadow-2xl cursor-pointer"
				title="Download"
				aria-label="Download image"
			>
				<Download class="w-4 h-4 md:w-5 md:h-5" />
			</button>

			<button
				onclick={onClose}
				class="p-2.5 md:p-3 bg-red-600 hover:bg-red-700 backdrop-blur-md rounded-full transition-all text-white shadow-lg shadow-red-600/20 cursor-pointer"
				title="Close"
				aria-label="Close lightbox"
			>
				<X class="w-4 h-4 md:w-5 md:h-5" />
			</button>
		</div>

		<!-- Prev / Next Arrows -->
		{#if isGallery}
			<button
				onclick={goPrev}
				disabled={currentIndex <= 0}
				class="fixed left-4 md:left-6 top-1/2 -translate-y-1/2 z-[10011] p-2 md:p-3 bg-zinc-900/80 hover:bg-zinc-800 backdrop-blur-md rounded-full transition-all text-white border border-white/10 shadow-2xl disabled:opacity-20 disabled:cursor-not-allowed cursor-pointer"
				title="Previous"
				aria-label="Previous image"
			>
				<ChevronLeft class="w-5 h-5 md:w-6 md:h-6" />
			</button>
			<button
				onclick={goNext}
				disabled={currentIndex >= images.length - 1}
				class="fixed right-4 md:right-6 top-1/2 -translate-y-1/2 z-[10011] p-2 md:p-3 bg-zinc-900/80 hover:bg-zinc-800 backdrop-blur-md rounded-full transition-all text-white border border-white/10 shadow-2xl disabled:opacity-20 disabled:cursor-not-allowed cursor-pointer"
				title="Next"
				aria-label="Next image"
			>
				<ChevronRight class="w-5 h-5 md:w-6 md:h-6" />
			</button>
		{/if}

		<!-- Image Container -->
		<div
			class="relative w-full h-full flex items-center justify-center overflow-hidden cursor-grab active:cursor-grabbing pointer-events-none"
			role="presentation"
		>
			<div
				class="pointer-events-auto"
				onmousedown={handleMouseDown}
				onmousemove={handleMouseMove}
				onmouseup={handleMouseUp}
				onmouseleave={handleMouseUp}
				ontouchstart={handleTouchStart}
				ontouchmove={handleTouchMove}
				ontouchend={handleTouchEnd}
				onwheel={handleWheel}
				role="presentation"
			>
				<img
					{src}
					{alt}
					class="max-w-[90vw] max-h-[90vh] object-contain transition-transform duration-200 ease-out select-none shadow-2xl"
					style="transform: scale({zoomScale}) translate({translateX / zoomScale}px, {translateY /
						zoomScale}px)"
					draggable="false"
					in:scale={{ duration: 300, start: 0.9 }}
				/>
			</div>
		</div>
	</div>
{/if}

<style>
	:global(body.modal-open) {
		overflow: hidden;
	}
</style>
