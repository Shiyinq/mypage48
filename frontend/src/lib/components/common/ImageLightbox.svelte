<script lang="ts">
	import { run, passive } from 'svelte/legacy';

	import { fade, scale } from 'svelte/transition';
	import { X, ZoomIn, ZoomOut, RotateCcw, Download } from 'lucide-svelte';
	import { onMount, onDestroy } from 'svelte';
	import { browser } from '$app/environment';

	interface Props {
		src?: string;
		alt?: string;
		isOpen?: boolean;
		onClose?: () => void;
	}

	let { src = '', alt = '', isOpen = false, onClose = () => {} }: Props = $props();

	let zoomScale = $state(1);
	let translateX = $state(0);
	let translateY = $state(0);
	let isDragging = false;
	let startX = 0;
	let startY = 0;

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

	function handleMouseUp() {
		isDragging = false;
	}

	function handleKeyDown(e: KeyboardEvent) {
		if (!isOpen) return;
		if (e.key === 'Escape') onClose();
		if (e.key === '+') handleZoomIn();
		if (e.key === '-') handleZoomOut();
	}

	async function downloadImage() {
		try {
			const response = await fetch(src);
			const blob = await response.blob();
			const url = window.URL.createObjectURL(blob);
			const link = document.createElement('a');
			link.href = url;

			// Try to extract filename from src or use alt
			const filename = src.split('/').pop()?.split('?')[0] || alt || 'image';
			link.download = filename.includes('.') ? filename : `${filename}.jpg`;

			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);
			window.URL.revokeObjectURL(url);
		} catch (error) {
			console.error('Download failed:', error);
			// Fallback: just open in new tab if fetch fails
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

	onMount(() => {
		window.addEventListener('keydown', handleKeyDown);
		return () => window.removeEventListener('keydown', handleKeyDown);
	});

	onDestroy(() => {
		if (browser) document.body.classList.remove('modal-open');
	});

	run(() => {
		if (browser && isOpen) {
			document.body.classList.add('modal-open');
		} else if (browser) {
			document.body.classList.remove('modal-open');
		}
	});

	run(() => {
		if (!isOpen) resetZoom();
	});
</script>

{#if isOpen}
	<div
		class="fixed inset-0 z-[10000] flex items-center justify-center transition-all"
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

		<!-- Controls -->
		<div class="fixed top-4 right-4 md:top-6 md:right-6 flex items-center gap-2 md:gap-4 z-[10001]">
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
				use:passive={['touchstart', () => handleTouchStart]}
				use:passive={['touchmove', () => handleTouchMove]}
				ontouchend={handleMouseUp}
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
