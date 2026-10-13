<script lang="ts">
	import { Maximize2 } from 'lucide-svelte';
	import type { Page48MediaItem } from '$lib/api/page48';
	import OptimizedImage from '$lib/components/common/OptimizedImage.svelte';
	import PostMediaCarousel from '$lib/components/page48/PostMediaCarousel.svelte';
	import VideoPlayer from '$lib/components/page48/VideoPlayer.svelte';
	import { measureMissingImageSizes, mediaRatio } from '$lib/utils/page48';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		/** Ordered media (images and videos mixed); empty renders nothing. */
		media?: Page48MediaItem[];
		/** Opens the media viewer at this index. Omit to render the media read-only. */
		onOpen?: (index: number) => void;
		/** Carousel position, shared with the caller's media viewer. */
		index?: number;
	}

	let { media = [], onOpen, index = $bindable(0) }: Props = $props();

	const { t } = useTranslation();

	// A lone photo may not get taller than this; the box is capped by width instead.
	const IMAGE_MAX_HEIGHT = 500;

	// Older posts stored no dimensions; measure the photos in the browser instead.
	$effect(() => {
		const images = media.filter((item) => item.type === 'image');
		if (images.length) return measureMissingImageSizes(images);
	});
</script>

{#snippet photo(item: Page48MediaItem)}
	<OptimizedImage
		src={item.url}
		srcMedium={item.url_medium}
		srcSmall={item.url_small}
		blurHash={item.blurHash}
		alt={t('page48.aria.media')}
		class="w-full h-full object-cover"
		objectFit="cover"
		sizes="(max-width: 640px) 100vw, 600px"
	/>
{/snippet}

{#if media.length === 1 && media[0].type === 'image'}
	{@const ratio = mediaRatio(media[0])}
	{@const box =
		'relative mx-auto block w-full overflow-hidden rounded-2xl border border-gray-100 bg-gray-100 dark:border-white/5 dark:bg-zinc-800'}
	{@const boxStyle = `aspect-ratio: ${ratio}; max-width: min(100%, ${Math.round(
		IMAGE_MAX_HEIGHT * ratio
	)}px);`}
	<!-- Keep the photo's own ratio and cap the box by width, so it fills exactly. -->
	<div class="pointer-events-none relative z-[1] mt-3">
		{#if onOpen}
			<button
				type="button"
				class={`pointer-events-auto cursor-zoom-in ${box}`}
				style={boxStyle}
				onclick={() => onOpen(0)}
				aria-label={t('page48.aria.viewImage', { index: 1, total: 1 })}
			>
				{@render photo(media[0])}
			</button>
		{:else}
			<div class={`pointer-events-auto ${box}`} style={boxStyle}>
				{@render photo(media[0])}
			</div>
		{/if}
	</div>
{:else if media.length === 1 && media[0].type === 'video'}
	{@const video = media[0]}
	{@const videoRatio =
		video.width > 0 && video.height > 0
			? Math.min(Math.max(video.width / video.height, 0.5625), 1.91)
			: 16 / 9}
	<div class="pointer-events-none relative z-[1] mt-3">
		<!-- Hug the player (same width VideoPlayer caps itself to) so the corner button
		     sits inside a portrait video instead of beside it. -->
		<div class="relative mx-auto w-full" style={`max-width: ${Math.round(510 * videoRatio)}px;`}>
			<VideoPlayer
				src={video.url ?? ''}
				width={video.width}
				height={video.height}
				maxHeight={510}
				controls
				class="pointer-events-auto"
			/>
			{#if onOpen}
				<!-- Inline playback stays, but the viewer (and its download button) is only
				     reachable through this —unlike a carousel video, a lone one doesn't open it. -->
				<button
					type="button"
					class="pointer-events-auto absolute left-3 top-3 z-[2] flex h-10 w-10 sm:h-9 sm:w-9 cursor-pointer items-center justify-center rounded-full bg-black/55 text-white backdrop-blur transition-colors hover:bg-black/75"
					onclick={() => onOpen(0)}
					aria-label={t('page48.aria.openVideo')}
					title={t('page48.aria.openVideo')}
				>
					<Maximize2 size={18} class="sm:h-4 sm:w-4" />
				</button>
			{/if}
		</div>
	</div>
{:else if media.length > 1}
	<!-- Mixed or multiple: a swipeable carousel; photo slides open the viewer. -->
	<div class="pointer-events-none relative z-[1] mt-3">
		<div class="pointer-events-none">
			<PostMediaCarousel {media} bind:index onOpen={(i) => onOpen?.(i)} />
		</div>
	</div>
{/if}
