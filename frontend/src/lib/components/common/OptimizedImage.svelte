<script module lang="ts">
	const loadedImageUrls = new Set<string>();
</script>

<script lang="ts">
	import { ImageIcon, LoaderCircle } from 'lucide-svelte';
	import { onMount } from 'svelte';
	import { decode } from 'blurhash';

	interface Props {
		src?: string | null;
		blurHash?: string | null;
		alt?: string;
		class?: string;
		style?: string;
		loading?: 'lazy' | 'eager';
		objectFit?: 'cover' | 'contain' | 'fill' | 'none' | 'scale-down';
		aspectRatio?: string;
		fallback?: boolean;
		referrerPolicy?:
			| 'no-referrer'
			| 'no-referrer-when-downgrade'
			| 'origin'
			| 'origin-when-cross-origin'
			| 'same-origin'
			| 'strict-origin'
			| 'strict-origin-when-cross-origin'
			| 'unsafe-url';
		noBackground?: boolean;
		onclick?: (e: MouseEvent) => void;
		onkeydown?: (e: KeyboardEvent) => void;
	}

	let {
		src,
		blurHash,
		alt,
		class: className = '',
		style = '',
		loading = 'lazy',
		objectFit = 'cover',
		aspectRatio = 'auto',
		fallback = true,
		referrerPolicy,
		noBackground = false,
		onclick,
		onkeydown
	}: Props = $props();

	let isLoaded = $state(false);
	let isError = $state(false);
	let imgRef: HTMLImageElement | undefined = $state();
	let canvasRef: HTMLCanvasElement | undefined = $state();

	function handleLoad() {
		isLoaded = true;
		if (src) loadedImageUrls.add(src);
	}

	function handleError() {
		isError = true;
		isLoaded = true;
	}

	$effect(() => {
		if (blurHash && !isLoaded && canvasRef) {
			try {
				const pixels = decode(blurHash, 32, 32);
				const ctx = canvasRef.getContext('2d');
				if (ctx) {
					const imageData = ctx.createImageData(32, 32);
					imageData.data.set(pixels);
					ctx.putImageData(imageData, 0, 0);
				}
			} catch (e) {
				console.error('Failed to decode blurhash', e);
			}
		}
	});

	onMount(() => {
		if (imgRef?.complete) {
			handleLoad();
		}
	});

	// Synchronize state with src changes and initial cache check
	$effect.pre(() => {
		if (src) {
			const alreadyLoaded = loadedImageUrls.has(src);
			isLoaded = alreadyLoaded;
			isError = false;
		}
	});
</script>

<div
	class="relative overflow-hidden isolate z-0 {noBackground
		? ''
		: 'bg-gray-100 dark:bg-zinc-800'} transition-colors duration-300 {className}"
	style="aspect-ratio: {aspectRatio}; {style}; -webkit-mask-image: -webkit-radial-gradient(white, black);"
	{onclick}
	{onkeydown}
	role="presentation"
>
	<!-- Error State -->
	{#if isError && fallback}
		<div
			class="absolute inset-0 z-20 flex flex-col items-center justify-center bg-gray-50 dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800"
		>
			<ImageIcon class="w-8 h-8 text-gray-300 dark:text-zinc-700 mb-2" />
			<span class="text-[10px] uppercase tracking-widest text-gray-400 font-bold"
				>Failed to load</span
			>
		</div>
	{:else}
		<!-- Image (renders immediately to support progressive loading) -->
		{#if src}
			<!-- BlurHash Placeholder -->
			{#if blurHash && !isLoaded && !isError}
				<canvas
					bind:this={canvasRef}
					width="32"
					height="32"
					class="absolute inset-0 w-full h-full rounded-[inherit] transition-opacity duration-700 {isLoaded
						? 'opacity-0'
						: 'opacity-100'}"
				></canvas>
			{/if}

			<img
				bind:this={imgRef}
				{src}
				{alt}
				{loading}
				referrerpolicy={referrerPolicy}
				class="w-full h-full rounded-[inherit] transition-all duration-700 ease-out {isLoaded
					? 'opacity-100 blur-0'
					: 'opacity-100 blur-sm'}"
				style="object-fit: {objectFit};"
				onload={handleLoad}
				onerror={handleError}
			/>
		{/if}

		<!-- Loading Overlay (shows over the blurring image/canvas) -->
		{#if !isLoaded && !isError && !blurHash}
			<div
				class="absolute inset-0 z-10 flex items-center justify-center bg-white/5 dark:bg-black/5 border border-white/10 dark:border-black/10 backdrop-blur-[1px] transition-opacity duration-500"
			>
				<LoaderCircle class="w-5 h-5 text-primary-500/30 animate-spin" />
			</div>
		{/if}
	{/if}
</div>

<style>
	img {
		will-change: opacity, transform, filter;
	}
</style>
