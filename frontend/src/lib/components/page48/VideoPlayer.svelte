<script lang="ts">
	import { onMount } from 'svelte';
	import { Play, Volume2, VolumeX } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { page48SoundStore, setPage48Sound } from '$lib/stores/page48.svelte';

	interface Props {
		src: string;
		width?: number;
		height?: number;
		autoplay?: boolean;
		loop?: boolean;
		controls?: boolean;
		/** Cap the rendered height (px); the box shrinks and centers instead. */
		maxHeight?: number;
		/**
		 * Immersive mode: fill the container and letterbox the video over a blurred
		 * copy of itself (TikTok-style), instead of cropping it.
		 */
		immersive?: boolean;
		class?: string;
	}

	let {
		src,
		width = 0,
		height = 0,
		autoplay = false,
		loop = false,
		controls = true,
		maxHeight = 0,
		immersive = false,
		class: klass = ''
	}: Props = $props();

	const { t } = useTranslation();

	let wrapperEl: HTMLDivElement | undefined = $state();
	let videoEl: HTMLVideoElement | undefined = $state();
	let playing = $state(false);
	let progress = $state(0);
	let duration = $state(0);

	// Sound preference is global: unmuting one video unmutes the rest too.
	let muted = $derived(!page48SoundStore.enabled);

	// Letterbox the video without letting a very tall clip take over the feed.
	let clampedRatio = $derived(
		width > 0 && height > 0 ? Math.min(Math.max(width / height, 0.5625), 1.91) : 16 / 9
	);

	// With a height cap, constrain the width instead so the box stays centered.
	let wrapperStyle = $derived(
		immersive
			? ''
			: maxHeight > 0
				? `aspect-ratio: ${clampedRatio}; max-width: ${Math.round(maxHeight * clampedRatio)}px`
				: `aspect-ratio: ${clampedRatio}`
	);

	function togglePlay() {
		const v = videoEl;
		if (!v) return;
		if (v.paused) void v.play().catch(() => {});
		else v.pause();
	}

	function toggleMute() {
		setPage48Sound(muted);
	}

	// Keep the element's *property* in sync (the attribute alone isn't reliable
	// for the autoplay/unmute flow).
	$effect(() => {
		const v = videoEl;
		if (v) v.muted = muted;
	});

	function onTimeUpdate() {
		const v = videoEl;
		if (!v || !Number.isFinite(v.duration) || v.duration === 0) return;
		progress = v.currentTime / v.duration;
	}

	function seek(e: MouseEvent) {
		const v = videoEl;
		if (!v || !Number.isFinite(v.duration)) return;
		const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
		v.currentTime = ((e.clientX - rect.left) / rect.width) * v.duration;
	}

	function formatTime(seconds: number): string {
		if (!Number.isFinite(seconds) || seconds < 0) return '0:00';
		const m = Math.floor(seconds / 60);
		const s = Math.floor(seconds % 60);
		return `${m}:${s.toString().padStart(2, '0')}`;
	}

	onMount(() => {
		const v = videoEl;
		if (!v || !wrapperEl) return;

		let observer: IntersectionObserver | undefined;
		if (autoplay) {
			// Autoplay is muted-only (browser policy); pause once out of view.
			observer = new IntersectionObserver(
				(entries) => {
					for (const entry of entries) {
						if (entry.isIntersecting) {
							v.muted = muted;
							void v.play().catch(() => {});
						} else {
							v.pause();
						}
					}
				},
				{ threshold: 0.5 }
			);
			observer.observe(wrapperEl);
		}
		return () => observer?.disconnect();
	});
</script>

<div
	bind:this={wrapperEl}
	class={`relative w-full ${!immersive && maxHeight > 0 ? 'mx-auto' : ''} bg-gray-100 dark:bg-zinc-800 ${immersive ? '' : 'rounded-2xl'} overflow-hidden group/vid ${klass}`}
	style={wrapperStyle}
>
	{#if immersive}
		<!-- Blurred fill so the (uncropped) video never leaves empty space -->
		<video
			{src}
			muted
			playsinline
			preload="auto"
			aria-hidden="true"
			tabindex="-1"
			class="absolute inset-0 w-full h-full object-cover scale-110 blur-2xl opacity-70 pointer-events-none"
		></video>
	{/if}

	<video
		bind:this={videoEl}
		{src}
		{loop}
		{muted}
		playsinline
		preload="metadata"
		class={`${immersive ? 'relative' : ''} w-full h-full object-contain`}
		onplay={() => (playing = true)}
		onpause={() => (playing = false)}
		ontimeupdate={onTimeUpdate}
		onloadedmetadata={() => {
			if (videoEl && Number.isFinite(videoEl.duration)) duration = videoEl.duration;
		}}
	></video>

	<!-- Click anywhere to toggle play/pause -->
	<button
		class="absolute inset-0 cursor-pointer"
		onclick={togglePlay}
		aria-label={playing ? t('page48.video.pause') : t('page48.video.play')}
	>
		{#if !playing}
			<span class="absolute inset-0 flex items-center justify-center">
				<span
					class="w-14 h-14 rounded-full bg-black/50 backdrop-blur flex items-center justify-center"
				>
					<Play size={26} class="text-white translate-x-0.5" fill="currentColor" />
				</span>
			</span>
		{/if}
	</button>

	<!-- Always-visible mute toggle (hover-only controls were hard to reach) -->
	<button
		class="absolute top-3 right-3 z-[1] w-10 h-10 sm:w-9 sm:h-9 rounded-full bg-black/55 hover:bg-black/75 backdrop-blur text-white flex items-center justify-center cursor-pointer transition-colors"
		onclick={toggleMute}
		aria-label={muted ? t('page48.video.unmute') : t('page48.video.mute')}
	>
		{#if muted}
			<VolumeX size={18} class="sm:w-4 sm:h-4" />
		{:else}
			<Volume2 size={18} class="sm:w-4 sm:h-4" />
		{/if}
	</button>

	{#if controls}
		<div
			class="absolute bottom-0 left-0 right-0 p-3 flex items-center gap-3 bg-gradient-to-t from-black/70 to-transparent opacity-0 group-hover/vid:opacity-100 focus-within:opacity-100 transition-opacity"
		>
			<button
				class="text-white cursor-pointer shrink-0"
				onclick={toggleMute}
				aria-label={muted ? t('page48.video.unmute') : t('page48.video.mute')}
			>
				{#if muted}
					<VolumeX size={18} />
				{:else}
					<Volume2 size={18} />
				{/if}
			</button>
			<button
				class="flex-1 h-1 bg-white/40 rounded-full cursor-pointer"
				onclick={seek}
				aria-label={t('page48.video.seek')}
			>
				<span class="block h-full bg-white rounded-full" style:width={`${progress * 100}%`}></span>
			</button>
			<span class="text-white text-[12px] sm:text-[11px] tabular-nums shrink-0">
				{formatTime(progress * (duration || 0))} / {formatTime(duration)}
			</span>
		</div>
	{/if}
</div>
