<script lang="ts">
	import { Play } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		videoId: string;
		/** Playback offset in seconds, taken from the original `?t=`/`?start=`. */
		start?: number;
		/** Cap the rendered height (px); the box shrinks and centers instead. */
		maxHeight?: number;
		class?: string;
	}

	let { videoId, start, maxHeight = 510, class: klass = '' }: Props = $props();

	const { t } = useTranslation();

	/**
	 * "Lite" embed: only the thumbnail loads until the viewer clicks, so a busy feed
	 * never pays for dozens of iframes. Clicking swaps in the privacy-enhanced player.
	 */
	let playing = $state(false);
	let thumbLoaded = $state(false);

	// maxresdefault is missing on some videos; hqdefault always exists.
	const THUMBNAILS = ['maxresdefault', 'hqdefault'];
	let thumbnailIndex = $state(0);

	let thumbnailUrl = $derived(
		`https://i.ytimg.com/vi/${videoId}/${THUMBNAILS[thumbnailIndex]}.jpg`
	);

	// Same trick as VideoPlayer: keep 16:9 and cap the box by width so it centers.
	let wrapperStyle = $derived(
		`aspect-ratio: 16 / 9; max-width: min(100%, ${Math.round(maxHeight * (16 / 9))}px)`
	);

	let embedSrc = $derived(
		`https://www.youtube-nocookie.com/embed/${videoId}?autoplay=1&rel=0${
			start ? `&start=${start}` : ''
		}`
	);

	function play(event: MouseEvent) {
		// The card behind the embed is a link; the click must not navigate away.
		event.stopPropagation();
		playing = true;
	}

	function onThumbnailError() {
		if (thumbnailIndex < THUMBNAILS.length - 1) thumbnailIndex += 1;
	}
</script>

<div
	class={`relative mx-auto w-full overflow-hidden rounded-2xl border border-gray-100 bg-black dark:border-white/5 ${klass}`}
	style={wrapperStyle}
>
	{#if playing}
		<iframe
			src={embedSrc}
			title={t('page48.aria.youtubeVideo')}
			class="absolute inset-0 h-full w-full"
			allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
			referrerpolicy="strict-origin-when-cross-origin"
			allowfullscreen
		></iframe>
	{:else}
		<button
			type="button"
			class="group/yt absolute inset-0 h-full w-full cursor-pointer"
			onclick={play}
			aria-label={t('page48.aria.playVideo')}
		>
			<img
				src={thumbnailUrl}
				alt=""
				loading="lazy"
				decoding="async"
				class={`h-full w-full object-cover transition-opacity duration-200 ${thumbLoaded ? 'opacity-100' : 'opacity-0'}`}
				onload={() => (thumbLoaded = true)}
				onerror={onThumbnailError}
			/>
			<span class="absolute inset-0 bg-black/10 transition-colors group-hover/yt:bg-black/0"></span>
			<span
				class="absolute left-1/2 top-1/2 flex h-14 w-14 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full bg-black/70 text-white shadow-lg transition-transform group-hover/yt:scale-110 group-active/yt:scale-95"
			>
				<Play size={26} class="ml-0.5 fill-white" />
			</span>
		</button>
	{/if}
</div>
