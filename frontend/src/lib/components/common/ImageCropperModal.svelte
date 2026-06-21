<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import {
		Maximize,
		RefreshCcw,
		X,
		Check,
		Image,
		Pencil,
		Crop,
		Undo2,
		SlidersHorizontal
	} from 'lucide-svelte';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import { portal } from '$lib/actions/portal';

	interface Props {
		imageUrl: string;
		defaultRatio?: number | string | null; // e.g. 1 for 1:1, null for free
		onClose: () => void;
		onSave: (base64: string) => void;
	}

	let { imageUrl, defaultRatio = 'original', onClose, onSave }: Props = $props();
	const { t } = useTranslation();

	let rawImageUrl = $derived(
		imageUrl.startsWith('data:image/') ||
			imageUrl.startsWith('blob:') ||
			imageUrl.startsWith('http')
			? imageUrl
			: getExternalMediaUrl(imageUrl)
	);

	let actualImageUrl = $derived(
		typeof window !== 'undefined' &&
			rawImageUrl.startsWith('http') &&
			!rawImageUrl.includes(window.location.host)
			? `/proxy/image?url=${encodeURIComponent(rawImageUrl)}`
			: rawImageUrl
	);

	let containerRef: HTMLDivElement | undefined = $state();
	let imageRef: HTMLImageElement | undefined = $state();
	let isProcessing = $state(false);
	let isImageLoaded = $state(false);

	// State
	let scale = $state(1);
	let panX = $state(0);
	let panY = $state(0);
	let mode = $state<'crop' | 'draw'>('crop');

	// Crop box state (w, h, x, y in pixels relative to container)
	let cbW = $state(200);
	let cbH = $state(200);
	let cbX = $state(0);
	let cbY = $state(0);

	// Drawing state
	const colors = [
		'#ef4444',
		'#3b82f6',
		'#22c55e',
		'#eab308', // Basic
		'#000000',
		'#ffffff', // B/W
		'#DE1578',
		'#1A9D9C',
		'#F18921',
		'#c08081' // Teams: Love, Dream, Passion, Trainee
	];
	let activeColor = $state(colors[0]);
	let brushSize = $state(5);
	let showThicknessSlider = $state(false);
	let drawCanvasRef: HTMLCanvasElement | undefined = $state();
	let drawingCtx: CanvasRenderingContext2D | null = null;

	interface Point {
		x: number;
		y: number;
	}
	interface DrawPath {
		color: string;
		width: number;
		points: Point[];
	}

	let paths = $state<DrawPath[]>([]);
	let isDrawing = false;

	let containerW = $state(0);
	let containerH = $state(0);

	let imgW = $state(0);
	let imgH = $state(0);
	let origW = $state(0);
	let origH = $state(0);

	let isDraggingImg = false;
	let startPanX = 0;
	let startPanY = 0;
	let startX = 0;
	let startY = 0;

	// Multi-touch for pinch zoom
	let activePointers = new Map<number, PointerEvent>();
	let initialPinchDist = 0;
	let initialPinchScale = 1;

	// Ratio options
	const ratios = [
		{ label: 'imageEditor.ratios.free', value: null },
		{ label: 'imageEditor.ratios.original', value: 'original' },
		{ label: 'imageEditor.ratios.square', value: 1 },
		{ label: 'imageEditor.ratios.sixteenNine', value: 16 / 9 },
		{ label: 'imageEditor.ratios.nineSixteen', value: 9 / 16 },
		{ label: 'imageEditor.ratios.fourThree', value: 4 / 3 },
		{ label: 'imageEditor.ratios.threeFour', value: 3 / 4 }
	];

	// Gunakan IIFE agar Svelte compiler tidak cerewet soal initial value dari prop
	let activeRatio = $state<number | string | null>((() => defaultRatio)());

	const initImage = () => {
		if (!imageRef || !containerRef) return;
		containerW = containerRef.clientWidth;
		containerH = containerRef.clientHeight;

		origW = imageRef.naturalWidth;
		origH = imageRef.naturalHeight;

		// Calculate container fit
		const ratioOrig = origW / origH;
		const ratioContainer = containerW / containerH;

		if (ratioOrig > ratioContainer) {
			imgW = containerW;
			imgH = containerW / ratioOrig;
		} else {
			imgH = containerH;
			imgW = containerH * ratioOrig;
		}

		// Initial center pan
		panX = 0;
		panY = 0;

		resetCropBox();
		isImageLoaded = true;
	};

	const resetCropBox = () => {
		if (containerW === 0 || containerH === 0) return;
		scale = 1;

		let maxW = imgW > 0 ? imgW : Math.max(50, containerW - 80);
		let maxH = imgH > 0 ? imgH : Math.max(50, containerH - 80);

		let r: number | null = null;
		if (activeRatio === 'original' && origH > 0) {
			r = origW / origH;
		} else if (typeof activeRatio === 'number') {
			r = activeRatio;
		}

		if (r) {
			if (r > maxW / maxH) {
				cbW = maxW;
				cbH = maxW / r;
			} else {
				cbH = maxH;
				cbW = maxH * r;
			}
		} else {
			// Bebas
			cbW = maxW;
			cbH = maxH;
		}

		cbX = (containerW - cbW) / 2;
		cbY = (containerH - cbH) / 2;
	};

	$effect(() => {
		if (drawCanvasRef && isImageLoaded && !drawingCtx) {
			drawingCtx = drawCanvasRef.getContext('2d');
			redrawCanvas();
		}
	});

	const getCanvasPoint = (e: PointerEvent): Point => {
		if (!imageRef) return { x: 0, y: 0 };
		const rect = imageRef.getBoundingClientRect();
		const xScaled = e.clientX - rect.left;
		const yScaled = e.clientY - rect.top;

		const ratioX = origW / rect.width;
		const ratioY = origH / rect.height;

		return {
			x: xScaled * ratioX,
			y: yScaled * ratioY
		};
	};

	const redrawCanvas = () => {
		if (!drawCanvasRef || !drawingCtx) return;
		drawingCtx.clearRect(0, 0, origW, origH);

		drawingCtx.lineCap = 'round';
		drawingCtx.lineJoin = 'round';

		for (const path of paths) {
			if (path.points.length === 0) continue;

			drawingCtx.strokeStyle = path.color;
			drawingCtx.lineWidth = path.width * (origW / imgW);

			drawingCtx.beginPath();
			drawingCtx.moveTo(path.points[0].x, path.points[0].y);
			if (path.points.length === 1) {
				// Draw a dot for single click
				drawingCtx.lineTo(path.points[0].x, path.points[0].y + 0.1);
			} else {
				for (let i = 1; i < path.points.length; i++) {
					drawingCtx.lineTo(path.points[i].x, path.points[i].y);
				}
			}
			drawingCtx.stroke();
		}
	};

	const undoDraw = () => {
		if (paths.length > 0) {
			paths = paths.slice(0, -1);
			redrawCanvas();
		}
	};

	// Image Pan Handlers
	const onImgPointerDown = (e: PointerEvent) => {
		// Ignore if interacting with handles
		if ((e.target as HTMLElement).closest('.handle')) return;
		(e.target as HTMLElement).setPointerCapture(e.pointerId);
		activePointers.set(e.pointerId, e);

		if (activePointers.size === 1) {
			if (mode === 'draw') {
				isDrawing = true;
				const pt = getCanvasPoint(e);
				paths = [...paths, { color: activeColor, width: brushSize, points: [pt] }];
				redrawCanvas();
			} else {
				isDraggingImg = true;
				startX = e.clientX;
				startY = e.clientY;
				startPanX = panX;
				startPanY = panY;
			}
		} else if (activePointers.size === 2) {
			isDrawing = false;
			isDraggingImg = false;
			const pts = Array.from(activePointers.values());
			initialPinchDist = Math.hypot(
				pts[0].clientX - pts[1].clientX,
				pts[0].clientY - pts[1].clientY
			);
			initialPinchScale = scale;
		}
	};

	const onImgPointerMove = (e: PointerEvent) => {
		if (mode === 'draw' && isDrawing && paths.length > 0) {
			const pt = getCanvasPoint(e);
			paths[paths.length - 1].points.push(pt);
			redrawCanvas();
		} else if (isDraggingImg) {
			panX = startPanX + (e.clientX - startX);
			panY = startPanY + (e.clientY - startY);
		}
	};

	const onWheel = (e: WheelEvent) => {
		e.preventDefault();
		const zoomSensitivity = 0.001;
		const delta = -e.deltaY * zoomSensitivity;
		const newScale = Math.max(0.1, scale * (1 + delta));
		scale = newScale;
	};

	let isDraggingHandle = false;
	let isDraggingBox = false;
	let activeHandle = '';
	let startCbW = 0;
	let startCbH = 0;
	let startCbX = 0;
	let startCbY = 0;

	const onHandleDown = (e: PointerEvent, handle: string) => {
		e.stopPropagation();
		(e.target as HTMLElement).setPointerCapture(e.pointerId);
		isDraggingHandle = true;
		activeHandle = handle;
		startX = e.clientX;
		startY = e.clientY;
		startCbW = cbW;
		startCbH = cbH;
		startCbX = cbX;
		startCbY = cbY;
	};

	let startCbXDrag = 0;
	let startCbYDrag = 0;

	const onBoxPointerDown = (e: PointerEvent) => {
		e.stopPropagation();
		(e.target as HTMLElement).setPointerCapture(e.pointerId);
		isDraggingBox = true;
		startX = e.clientX;
		startY = e.clientY;
		startCbXDrag = cbX;
		startCbYDrag = cbY;
	};

	const onHandleMove = (e: PointerEvent) => {
		const dx = e.clientX - startX;
		const dy = e.clientY - startY;

		let newW = startCbW;
		let newH = startCbH;
		let newX = startCbX;
		let newY = startCbY;

		let isN = activeHandle.includes('n');
		let isS = activeHandle.includes('s');
		let isE = activeHandle.includes('e');
		let isW = activeHandle.includes('w');

		let dw = isE ? dx : isW ? -dx : 0;
		let dh = isS ? dy : isN ? -dy : 0;

		let ratio: number | null = null;
		if (activeRatio === 'original') ratio = origW / origH;
		else if (typeof activeRatio === 'number') ratio = activeRatio;

		if (ratio) {
			let magW = Math.abs(dw);
			let magH = Math.abs(dh);
			if (magW > magH) {
				dh = dw / ratio;
			} else {
				dw = dh * ratio;
			}
		}

		newW = startCbW + dw;
		newH = startCbH + dh;

		if (newW < 50) {
			newW = 50;
			if (ratio) newH = 50 / ratio;
		}
		if (newH < 50) {
			newH = 50;
			if (ratio) newW = 50 * ratio;
		}

		if (isW) newX = startCbX + (startCbW - newW);
		if (isN) newY = startCbY + (startCbH - newH);

		// Clamp
		if (newX < 0) {
			newX = 0;
			newW = startCbW + startCbX;
			if (ratio) {
				newH = newW / ratio;
				if (isN) newY = startCbY + (startCbH - newH);
			}
		}
		if (newY < 0) {
			newY = 0;
			newH = startCbH + startCbY;
			if (ratio) {
				newW = newH * ratio;
				if (isW) newX = startCbX + (startCbW - newW);
			}
		}
		if (newX + newW > containerW && containerW > 0) {
			newW = containerW - newX;
			if (ratio) {
				newH = newW / ratio;
				if (isN) newY = startCbY + (startCbH - newH);
			}
		}
		if (newY + newH > containerH && containerH > 0) {
			newH = containerH - newY;
			if (ratio) {
				newW = newH * ratio;
				if (isW) newX = startCbX + (startCbW - newW);
			}
		}

		cbW = newW;
		cbH = newH;
		cbX = newX;
		cbY = newY;
	};

	const onBoxMove = (e: PointerEvent) => {
		const dx = e.clientX - startX;
		const dy = e.clientY - startY;

		let newX = startCbXDrag + dx;
		let newY = startCbYDrag + dy;

		// Clamp
		if (newX < 0) newX = 0;
		if (newY < 0) newY = 0;
		if (newX + cbW > containerW && containerW > 0) newX = containerW - cbW;
		if (newY + cbH > containerH && containerH > 0) newY = containerH - cbH;

		cbX = newX;
		cbY = newY;
	};

	const onGlobalPointerMove = (e: PointerEvent) => {
		if (activePointers.has(e.pointerId)) {
			activePointers.set(e.pointerId, e);
		}

		if (activePointers.size === 2) {
			const pts = Array.from(activePointers.values());
			const dist = Math.hypot(pts[0].clientX - pts[1].clientX, pts[0].clientY - pts[1].clientY);
			if (initialPinchDist > 0) {
				const newScale = initialPinchScale * (dist / initialPinchDist);
				scale = Math.max(0.1, Math.min(10, newScale));
			}
		} else if (isDrawing) {
			onImgPointerMove(e);
		} else if (isDraggingImg) {
			onImgPointerMove(e);
		} else if (isDraggingHandle) {
			onHandleMove(e);
		} else if (isDraggingBox) {
			onBoxMove(e);
		}
	};

	const onGlobalPointerUp = (e: PointerEvent) => {
		activePointers.delete(e.pointerId);
		if (activePointers.size < 2) initialPinchDist = 0;

		isDrawing = false;
		isDraggingImg = false;
		isDraggingHandle = false;
		isDraggingBox = false;
		activeHandle = '';
	};

	const generateCrop = async () => {
		isProcessing = true;
		try {
			const canvas = document.createElement('canvas');
			const ctx = canvas.getContext('2d');
			if (!ctx) throw new Error('No 2d context');

			// Calculate crop area in original image coordinates
			const imgLeftContainer = containerW / 2 + panX - (imgW * scale) / 2;
			const imgTopContainer = containerH / 2 + panY - (imgH * scale) / 2;

			const cropLeftLocal = cbX - imgLeftContainer;
			const cropTopLocal = cbY - imgTopContainer;

			const scaleOrig = origW / (imgW * scale);
			const cropLeftOrig = cropLeftLocal * scaleOrig;
			const cropTopOrig = cropTopLocal * scaleOrig;
			const cropWidthOrig = cbW * scaleOrig;
			const cropHeightOrig = cbH * scaleOrig;

			canvas.width = cropWidthOrig;
			canvas.height = cropHeightOrig;

			// Draw image onto canvas
			ctx.drawImage(
				imageRef!,
				cropLeftOrig,
				cropTopOrig,
				cropWidthOrig,
				cropHeightOrig,
				0,
				0,
				cropWidthOrig,
				cropHeightOrig
			);

			// Draw the drawing layer if there are paths
			if (drawCanvasRef && paths.length > 0) {
				ctx.drawImage(
					drawCanvasRef,
					cropLeftOrig,
					cropTopOrig,
					cropWidthOrig,
					cropHeightOrig,
					0,
					0,
					cropWidthOrig,
					cropHeightOrig
				);
			}

			const base64 = canvas.toDataURL('image/jpeg', 0.95);
			onSave(base64);
		} catch (error) {
			console.error('Crop failed', error);
		} finally {
			isProcessing = false;
		}
	};

	const onKeyDown = (e: KeyboardEvent) => {
		if (e.key === 'Escape') {
			onClose();
		}
	};
</script>

<svelte:window
	onpointermove={onGlobalPointerMove}
	onpointerup={onGlobalPointerUp}
	onpointercancel={onGlobalPointerUp}
	onkeydown={onKeyDown}
/>

<div
	use:portal
	class="fixed top-0 left-0 w-full h-[100dvh] z-[9999] flex flex-col bg-black overflow-hidden"
>
	<!-- Top Bar -->
	<div class="relative flex items-center justify-between p-4 bg-black/50 text-white z-10">
		<button
			type="button"
			class="p-2 rounded-full hover:bg-white/10 transition-colors cursor-pointer z-20"
			onclick={onClose}
			aria-label={t('common.close')}
			title={t('common.close')}
		>
			<X class="w-6 h-6" />
		</button>

		<h2
			class="absolute left-1/2 -translate-x-1/2 text-sm font-bold uppercase tracking-wider hidden sm:block z-10"
		>
			{t('imageEditor.title')}
		</h2>

		<div class="flex items-center gap-2 sm:gap-4 z-20">
			<!-- Mode Toggle -->
			<div class="bg-white/10 rounded-full p-1 flex items-center">
				<button
					class="p-2 rounded-full transition-colors cursor-pointer {mode === 'crop'
						? 'bg-white text-black'
						: 'text-white hover:bg-white/20'}"
					onclick={() => (mode = 'crop')}
					title={t('imageEditor.crop')}
				>
					<Crop class="w-4 h-4 sm:w-5 sm:h-5" />
				</button>
				<button
					class="p-2 rounded-full transition-colors cursor-pointer {mode === 'draw'
						? 'bg-white text-black'
						: 'text-white hover:bg-white/20'}"
					onclick={() => (mode = 'draw')}
					title={t('imageEditor.draw')}
				>
					<Pencil class="w-4 h-4 sm:w-5 sm:h-5" />
				</button>
			</div>

			<button
				type="button"
				class="p-2 rounded-full hover:bg-white/10 transition-colors cursor-pointer"
				onclick={() => {
					if (mode === 'crop') {
						panX = 0;
						panY = 0;
						activeRatio = defaultRatio;
						resetCropBox();
					} else {
						paths = [];
						redrawCanvas();
					}
				}}
				title={t('imageEditor.reset')}
			>
				<RefreshCcw class="w-5 h-5" />
			</button>
			<button
				class="bg-red-600 hover:bg-red-700 active:bg-red-800 text-white px-4 sm:px-6 py-2 rounded-full font-bold shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer flex items-center gap-2 text-sm sm:text-base"
				onclick={generateCrop}
				disabled={isProcessing}
			>
				{#if isProcessing}
					<div
						class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"
					></div>
				{:else}
					<Check class="w-5 h-5" />
				{/if}
				{t('imageEditor.done')}
			</button>
		</div>
	</div>

	<!-- Editor Area -->
	<div
		class="flex-1 relative overflow-hidden flex items-center justify-center touch-none"
		bind:this={containerRef}
		bind:clientWidth={containerW}
		bind:clientHeight={containerH}
		onwheel={onWheel}
	>
		<!-- Image layer -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div
			class="absolute flex items-center justify-center {mode === 'crop'
				? 'cursor-move'
				: 'cursor-pencil'}"
			style="width: {imgW}px; height: {imgH}px; transform: translate({panX}px, {panY}px) scale({scale});"
			onpointerdown={onImgPointerDown}
		>
			<img
				bind:this={imageRef}
				src={actualImageUrl}
				alt="Crop target"
				class="w-full h-full object-contain select-none shadow-2xl pointer-events-none"
				crossorigin="anonymous"
				onload={initImage}
			/>

			{#if isImageLoaded}
				<canvas
					bind:this={drawCanvasRef}
					width={origW}
					height={origH}
					class="absolute inset-0 w-full h-full pointer-events-none"
				></canvas>
			{/if}
		</div>

		{#if !isImageLoaded}
			<!-- Loading Spinner while fetching the raw image -->
			<div
				class="absolute inset-0 flex items-center justify-center z-50 pointer-events-none bg-black/40"
			>
				<div
					class="w-8 h-8 border-4 border-white/20 border-t-white rounded-full animate-spin"
				></div>
			</div>
		{/if}

		{#if isImageLoaded}
			{#if mode === 'crop'}
				<!-- Mask Overlay -->
				<div class="absolute inset-0 pointer-events-none" style="background: rgba(0,0,0,0.6);">
					<div
						class="absolute border border-white shadow-[0_0_0_9999px_rgba(0,0,0,0.6)] mix-blend-destination"
						style="width: {cbW}px; height: {cbH}px; left: {cbX}px; top: {cbY}px; border-radius: {activeRatio ===
						1
							? '50%'
							: '0'}; box-sizing: border-box;"
					></div>
				</div>

				<!-- Crop Box Guidelines and Handles -->
				<div
					class="absolute box-border border-2 border-white pointer-events-none"
					style="width: {cbW}px; height: {cbH}px; left: {cbX}px; top: {cbY}px; box-sizing: border-box;"
				>
					<!-- The draggable area -->
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<div
						class="absolute inset-0 cursor-move pointer-events-auto"
						onpointerdown={onBoxPointerDown}
					></div>

					<!-- Grid lines -->
					<div class="absolute w-full h-1/3 top-1/3 border-y border-white/30"></div>
					<div class="absolute h-full w-1/3 left-1/3 border-x border-white/30"></div>

					<!-- Handles (NW, NE, SW, SE) -->
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<div
						class="handle absolute w-10 h-10 -left-5 -top-5 cursor-nwse-resize pointer-events-auto flex items-center justify-center p-2"
						onpointerdown={(e) => onHandleDown(e, 'nw')}
					>
						<div class="w-full h-full border-l-4 border-t-4 border-white"></div>
					</div>
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<div
						class="handle absolute w-10 h-10 -right-5 -top-5 cursor-nesw-resize pointer-events-auto flex items-center justify-center p-2"
						onpointerdown={(e) => onHandleDown(e, 'ne')}
					>
						<div class="w-full h-full border-r-4 border-t-4 border-white"></div>
					</div>
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<div
						class="handle absolute w-10 h-10 -left-5 -bottom-5 cursor-nesw-resize pointer-events-auto flex items-center justify-center p-2"
						onpointerdown={(e) => onHandleDown(e, 'sw')}
					>
						<div class="w-full h-full border-l-4 border-b-4 border-white"></div>
					</div>
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<div
						class="handle absolute w-10 h-10 -right-5 -bottom-5 cursor-nwse-resize pointer-events-auto flex items-center justify-center p-2"
						onpointerdown={(e) => onHandleDown(e, 'se')}
					>
						<div class="w-full h-full border-r-4 border-b-4 border-white"></div>
					</div>
				</div>
			{:else}
				<!-- Subtle indicator of the cropped area while drawing -->
				<div
					class="absolute box-border border-2 border-white/30 border-dashed pointer-events-none"
					style="width: {cbW}px; height: {cbH}px; left: {cbX}px; top: {cbY}px; border-radius: {activeRatio ===
					1
						? '50%'
						: '0'}; box-sizing: border-box;"
				></div>
			{/if}
		{/if}

		{#if mode === 'draw' && showThicknessSlider}
			<div
				class="absolute bottom-6 left-1/2 -translate-x-1/2 bg-zinc-900/95 border border-zinc-700 rounded-full px-6 py-3 flex items-center gap-4 shadow-xl backdrop-blur-sm z-20"
			>
				<div class="w-1.5 h-1.5 bg-zinc-400 rounded-full shrink-0"></div>
				<input
					type="range"
					min="1"
					max="25"
					bind:value={brushSize}
					class="w-32 sm:w-48 accent-white cursor-pointer"
				/>
				<div class="w-4 h-4 bg-zinc-400 rounded-full shrink-0"></div>
			</div>
		{/if}
	</div>

	<!-- Bottom Tools (Ratios) -->
	<div
		class="h-28 bg-zinc-900 border-t border-zinc-800 flex items-center overflow-x-auto px-4 custom-scrollbar gap-3 z-10 md:justify-center"
	>
		{#if mode === 'crop'}
			{#each ratios as r}
				<button
					type="button"
					class="flex flex-col items-center gap-2 shrink-0 group transition-all cursor-pointer"
					onclick={() => {
						activeRatio = r.value;
						resetCropBox();
					}}
				>
					<div
						class="w-12 h-12 rounded-full flex items-center justify-center transition-all {activeRatio ===
						r.value
							? 'bg-red-600/20 text-red-400 border border-red-500/50'
							: 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'}"
					>
						{#if r.label === 'imageEditor.ratios.free'}
							<Maximize class="w-5 h-5" />
						{:else if r.label === 'imageEditor.ratios.original'}
							<Image class="w-5 h-5" />
						{:else}
							<div
								class="border-2 border-current rounded-sm"
								style="width: 20px; height: {20 / (typeof r.value === 'number' ? r.value : 1)}px;"
							></div>
						{/if}
					</div>
					<span
						class="text-[10px] font-bold {activeRatio === r.value
							? 'text-red-400'
							: 'text-zinc-500'}"
					>
						{t(r.label)}
					</span>
				</button>
			{/each}
		{:else}
			<div class="flex items-center gap-3 px-2 w-full max-w-md mx-auto justify-between">
				<!-- Thickness toggle -->
				<div class="flex items-center gap-3 shrink-0">
					<button
						type="button"
						class="flex flex-col items-center gap-1 transition-colors cursor-pointer {showThicknessSlider
							? 'text-white'
							: 'text-zinc-400 hover:text-white'}"
						onclick={() => (showThicknessSlider = !showThicknessSlider)}
						title={t('imageEditor.thickness')}
					>
						<SlidersHorizontal class="w-5 h-5" />
						<span class="text-[10px] font-bold">{t('imageEditor.size')}</span>
					</button>

					<!-- Undo -->
					<button
						type="button"
						class="flex flex-col items-center gap-1 text-zinc-400 hover:text-white disabled:opacity-50 transition-colors cursor-pointer"
						onclick={undoDraw}
						disabled={paths.length === 0}
					>
						<Undo2 class="w-5 h-5" />
						<span class="text-[10px] font-bold">{t('imageEditor.undo')}</span>
					</button>
				</div>

				<div class="w-px h-8 bg-zinc-700 shrink-0"></div>

				<!-- Colors -->
				<div class="flex gap-2 sm:gap-3 overflow-x-auto custom-scrollbar flex-1 pb-1">
					{#each colors as color}
						<button
							type="button"
							class="w-8 h-8 sm:w-10 sm:h-10 shrink-0 rounded-full border-2 transition-transform cursor-pointer {activeColor ===
							color
								? 'scale-110 border-white'
								: 'border-transparent hover:scale-105'}"
							style="background-color: {color};"
							onclick={() => (activeColor = color)}
							aria-label="Color {color}"
						></button>
					{/each}
				</div>
			</div>
		{/if}
	</div>
</div>

<style>
	/* Hide standard scrollbar */
	.custom-scrollbar::-webkit-scrollbar {
		height: 4px;
	}
	.custom-scrollbar::-webkit-scrollbar-track {
		background: transparent;
	}
	.custom-scrollbar::-webkit-scrollbar-thumb {
		background: #3f3f46;
		border-radius: 4px;
	}

	/* Custom SVG Pencil Cursor */
	.cursor-pencil {
		cursor:
			url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z'/%3E%3C/svg%3E")
				0 24,
			crosshair;
	}
</style>
