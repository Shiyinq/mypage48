<script lang="ts">
	import { ChevronLeft, ChevronRight } from 'lucide-svelte';
	import { OptimizedImage } from '$lib/components/common';
	import type { Page48Image } from '$lib/api/page48';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		images: Page48Image[];
		/**
		 * Index of the leading visible slide. Bindable so the parent (e.g. the
		 * lightbox) can drive it and read it back after a swipe.
		 */
		index?: number;
		/** Called on a tap/click on a slide (opens the lightbox at that slide). */
		onOpen?: (index: number) => void;
	}

	let { images, index = $bindable(0), onOpen }: Props = $props();

	const { t } = useTranslation();

	let track = $state<HTMLDivElement>();
	/** Where the pointer went down, to tell a tap apart from a swipe. */
	let pointerStartX = 0;
	/** Set when the swipe itself moved `index`, so the effect below leaves it alone. */
	let indexFromSwipe = false;

	// Two slides are visible at once, so the last reachable position already shows
	// the final two images — that's why the leading index tops out at length - 2.
	let maxIndex = $derived(Math.max(0, images.length - 2));
	let hasOverflow = $derived(maxIndex > 0);
	/** Photo the badge points at: the last one visible in the strip. */
	let visibleTo = $derived(Math.min(index + 2, images.length));

	/**
	 * Scroll offset that lines slide `i` up with the left edge, clamped to the
	 * scrollable range (the final slides can't reach the left edge).
	 */
	function targetOffset(slideIndex: number): number {
		const el = track;
		const slide = el?.children[slideIndex] as HTMLElement | undefined;
		if (!el || !slide) return 0;

		const maxScroll = Math.max(0, el.scrollWidth - el.clientWidth);
		return Math.min(slide.offsetLeft, maxScroll);
	}

	// Keep the requested slide in view. A swipe already updates `index` itself, so
	// the tolerance below stops this from fighting the browser's snap.
	$effect(() => {
		const el = track;
		if (!el) return;

		const target = targetOffset(index);
		if (indexFromSwipe) {
			// The strip is already where the user dragged it; scrolling to the
			// target here would yank it back to the previous stop.
			indexFromSwipe = false;
			return;
		}
		if (Math.abs(el.scrollLeft - target) > 4) {
			el.scrollTo({ left: target, behavior: 'smooth' });
		}
	});

	/**
	 * Leading slide = the snap stop closest to the current scroll offset. Comparing
	 * against the clamped offsets keeps both ends correct: with two slides visible
	 * the first stop is `0` (not `1`) and the last stop is `length - 2`.
	 */
	function handleScroll() {
		const el = track;
		if (!el) return;

		const maxScroll = Math.max(0, el.scrollWidth - el.clientWidth);
		let leading = 0;
		let smallestDelta = Infinity;
		for (let i = 0; i <= maxIndex; i += 1) {
			const slide = el.children[i] as HTMLElement | undefined;
			if (!slide) continue;

			const delta = Math.abs(Math.min(slide.offsetLeft, maxScroll) - el.scrollLeft);
			if (delta < smallestDelta) {
				smallestDelta = delta;
				leading = i;
			}
		}

		if (leading !== index) {
			indexFromSwipe = true;
			index = leading;
		}
	}

	function goTo(next: number) {
		index = Math.max(0, Math.min(next, maxIndex));
	}

	function handleSlideClick(slideIndex: number, event: MouseEvent) {
		// Ignore the click that ends a swipe/drag.
		if (Math.abs(event.clientX - pointerStartX) > 8) return;
		onOpen?.(slideIndex);
	}
</script>

<div class="relative isolate">
	<div
		bind:this={track}
		onscroll={handleScroll}
		class="scrollbar-hide relative flex snap-x snap-mandatory gap-1.5 overflow-x-auto overscroll-x-contain"
	>
		{#each images as image, i (image.filename)}
			<button
				type="button"
				class="relative aspect-[4/5] w-[48%] shrink-0 cursor-zoom-in snap-start overflow-hidden rounded-2xl border border-gray-100 bg-gray-100 dark:border-white/5 dark:bg-zinc-800"
				onpointerdown={(event) => (pointerStartX = event.clientX)}
				onclick={(event) => handleSlideClick(i, event)}
				aria-label={t('page48.aria.viewImage', { index: i + 1, total: images.length })}
			>
				<OptimizedImage
					src={image.url}
					srcMedium={image.url_medium}
					srcSmall={image.url_small}
					blurHash={image.blurHash}
					alt={t('page48.aria.media')}
					class="h-full w-full object-cover"
					objectFit="cover"
					sizes="(max-width: 640px) 50vw, 300px"
				/>
			</button>
		{/each}
	</div>

	{#if hasOverflow}
		<span
			class="pointer-events-none absolute right-2 top-2 rounded-full bg-black/60 px-2 py-0.5 text-[11px] font-semibold tabular-nums text-white backdrop-blur-sm"
		>
			{visibleTo}/{images.length}
		</span>

		<!-- Arrows: wide screens only, mobile swipes instead; revealed on card hover -->
		{#if index > 0}
			<button
				type="button"
				class="absolute left-2 top-1/2 hidden h-9 w-9 -translate-y-1/2 cursor-pointer items-center justify-center rounded-full bg-black/50 text-white opacity-0 backdrop-blur-sm transition-opacity pointer-events-none group-hover:pointer-events-auto group-hover:opacity-100 focus-visible:pointer-events-auto focus-visible:opacity-100 sm:flex"
				onclick={() => goTo(index - 1)}
				aria-label={t('page48.aria.prevImage')}
			>
				<ChevronLeft size={18} />
			</button>
		{/if}
		{#if index < maxIndex}
			<button
				type="button"
				class="absolute right-2 top-1/2 hidden h-9 w-9 -translate-y-1/2 cursor-pointer items-center justify-center rounded-full bg-black/50 text-white opacity-0 backdrop-blur-sm transition-opacity pointer-events-none group-hover:pointer-events-auto group-hover:opacity-100 focus-visible:pointer-events-auto focus-visible:opacity-100 sm:flex"
				onclick={() => goTo(index + 1)}
				aria-label={t('page48.aria.nextImage')}
			>
				<ChevronRight size={18} />
			</button>
		{/if}
	{/if}
</div>
