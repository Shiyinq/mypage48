<script lang="ts">
	import type { Page48Image, Page48Video } from '$lib/api/page48';
	import OptimizedImage from '$lib/components/common/OptimizedImage.svelte';
	import PostImageCarousel from '$lib/components/page48/PostImageCarousel.svelte';
	import VideoPlayer from '$lib/components/page48/VideoPlayer.svelte';
	import { imageRatio, measureMissingImageSizes } from '$lib/utils/page48';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		images?: Page48Image[];
		videos?: Page48Video[];
		/** Opens the media viewer at this index. Omit to render the media read-only. */
		onOpen?: (index: number) => void;
		/** Carousel position, shared with the caller's media viewer. */
		index?: number;
	}

	let { images = [], videos = [], onOpen, index = $bindable(0) }: Props = $props();

	const { t } = useTranslation();

	// A lone photo may not get taller than this; the box is capped by width
	// instead (see below) so its ratio always matches the photo.
	const IMAGE_MAX_HEIGHT = 500;

	// Older posts stored no dimensions; measure the photo in the browser instead.
	$effect(() => {
		if (images.length) return measureMissingImageSizes(images);
	});

	let singleImageRatio = $derived(images.length === 1 ? imageRatio(images[0]) : 16 / 9);

	// Only a video that actually has a URL can play; the stored one is nullable.
	let video = $derived.by(() => {
		const found = videos.find((item) => item.url);
		if (!found?.url) return null;
		return { url: found.url, width: found.width, height: found.height };
	});
</script>

{#snippet photo(image: Page48Image)}
	<OptimizedImage
		src={image.url}
		srcMedium={image.url_medium}
		srcSmall={image.url_small}
		blurHash={image.blurHash}
		alt={t('page48.aria.media')}
		class="w-full h-full object-cover"
		objectFit="cover"
		sizes="(max-width: 640px) 100vw, 600px"
	/>
{/snippet}

<!-- Images: a single one inline, several as a swipeable carousel. The wrapper is
     decoration so the empty margins beside a centred photo still open the card; the
     media itself opts back in. -->
{#if images.length > 0}
	<div class="pointer-events-none relative z-[1] mt-3">
		{#if images.length === 1}
			{@const image = images[0]}
			{@const box =
				'relative mx-auto block w-full overflow-hidden rounded-2xl border border-gray-100 bg-gray-100 dark:border-white/5 dark:bg-zinc-800'}
			{@const boxStyle = `aspect-ratio: ${singleImageRatio}; max-width: min(100%, ${Math.round(
				IMAGE_MAX_HEIGHT * singleImageRatio
			)}px);`}
			<!-- Same trick as VideoPlayer: keep the photo's own ratio and cap the box by
			     width, so the photo fills it exactly (no crop, no letterbox bars). -->
			{#if onOpen}
				<button
					type="button"
					class={`pointer-events-auto cursor-zoom-in ${box}`}
					style={boxStyle}
					onclick={() => onOpen(0)}
					aria-label={t('page48.aria.viewImage', { index: 1, total: 1 })}
				>
					{@render photo(image)}
				</button>
			{:else}
				<div class={`pointer-events-auto ${box}`} style={boxStyle}>
					{@render photo(image)}
				</div>
			{/if}
		{:else}
			<!-- Not interactive itself: the empty space beside the slides has to fall
			     through to the card, so only the slides and arrows opt in. -->
			<div class="pointer-events-none">
				<PostImageCarousel {images} bind:index onOpen={(i) => onOpen?.(i)} />
			</div>
		{/if}
	</div>
{/if}

<!-- Video (single, X/Twitter style: click to play) -->
{#if video}
	<div class="pointer-events-none relative z-[1] mt-3">
		<VideoPlayer
			src={video.url}
			width={video.width}
			height={video.height}
			maxHeight={510}
			controls
			class="pointer-events-auto"
		/>
	</div>
{/if}
