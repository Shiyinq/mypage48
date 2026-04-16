<script module lang="ts">
	const loadedImageUrls = new Set<string>();
</script>

<script lang="ts">
	import { ImageIcon, LoaderCircle } from 'lucide-svelte';
	import { onMount } from 'svelte';

	interface Props {
		src?: string | null;
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
		onclick?: (e: MouseEvent) => void;
		onkeydown?: (e: KeyboardEvent) => void;
	}

	let {
		src,
		alt,
		class: className = '',
		style = '',
		loading = 'lazy',
		objectFit = 'cover',
		aspectRatio = 'auto',
		fallback = true,
		referrerPolicy,
		onclick,
		onkeydown
	}: Props = $props();

	let isLoaded = $state(false);
	let isError = $state(false);
	let imgRef: HTMLImageElement | undefined = $state();

	function handleLoad() {
		isLoaded = true;
		if (src) loadedImageUrls.add(src);
	}

	function handleError() {
		isError = true;
		isLoaded = true;
	}

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
	class="relative overflow-hidden bg-gray-100 dark:bg-zinc-800 transition-colors duration-300 {className}"
	style="aspect-ratio: {aspectRatio}; {style}"
	{onclick}
	{onkeydown}
	role="presentation"
>
	<!-- Placeholder / Skeleton -->
	{#if !isLoaded && !isError}
		<div
			class="absolute inset-0 z-0 animate-pulse bg-gradient-to-br from-gray-100 to-gray-200 dark:from-zinc-800 dark:to-zinc-700 flex items-center justify-center"
		>
			<LoaderCircle class="w-5 h-5 text-gray-300 dark:text-zinc-600 animate-spin" />
		</div>
	{/if}

	<!-- Error State -->
	{#if isError && fallback}
		<div
			class="absolute inset-0 flex flex-col items-center justify-center bg-gray-50 dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800"
		>
			<ImageIcon class="w-8 h-8 text-gray-300 dark:text-zinc-700 mb-2" />
			<span class="text-[10px] uppercase tracking-widest text-gray-400 font-bold"
				>Failed to load</span
			>
		</div>
	{:else}
		<img
			bind:this={imgRef}
			{src}
			{alt}
			{loading}
			referrerpolicy={referrerPolicy}
			class="w-full h-full transition-all duration-1000 ease-out {isLoaded
				? 'opacity-100 scale-100 blur-0'
				: 'opacity-0 scale-[1.05] blur-md'}"
			style="object-fit: {objectFit};"
			onload={handleLoad}
			onerror={handleError}
		/>
	{/if}
</div>

<style>
	img {
		will-change: opacity, transform, filter;
	}
</style>
