<script lang="ts">
	import { onDestroy, onMount } from 'svelte';
	import { RefreshCw, AlertCircle } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	interface Props {
		id?: string; // youtube_id
		volume?: number;
		muted?: boolean;
		currentTime?: number;
		controls?: boolean;
		isFillMode?: boolean;
	}

	let {
		id = '',
		volume = 1,
		muted = false,
		currentTime = $bindable(0),
		controls = false,
		isFillMode = false
	}: Props = $props();

	let containerId = `yt-${Math.random().toString(36).substr(2, 9)}`;
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	let player: any = null;
	let playerReady = $state(false);
	let loading = $state(true);
	let error: string | null = $state(null);
	let rotation = $state(0);

	$effect(() => {
		if (player && typeof player.getCurrentTime === 'function' && !loading && !error) {
			const interval = setInterval(() => {
				try {
					const time = player.getCurrentTime();
					if (typeof time === 'number') {
						currentTime = time;
					}
				} catch {
					// ignore
				}
			}, 500);
			return () => clearInterval(interval);
		}
	});

	$effect(() => {
		if (playerReady && player && typeof player.setVolume === 'function') {
			if (muted || volume === 0) {
				player.mute();
			} else {
				player.unMute();
				player.setVolume(Math.round(volume * 100));
			}
		}
	});

	onMount(() => {
		if (typeof window !== 'undefined') {
			// eslint-disable-next-line @typescript-eslint/no-explicit-any
			const w = window as any;
			if (!w.YT) {
				const tag = document.createElement('script');
				tag.src = 'https://www.youtube.com/iframe_api';
				const firstScriptTag = document.getElementsByTagName('script')[0];
				firstScriptTag.parentNode?.insertBefore(tag, firstScriptTag);

				// Only assign if it doesn't exist to prevent overwriting other instances
				if (!w.onYouTubeIframeAPIReady) {
					w.onYouTubeIframeAPIReady = () => {
						window.dispatchEvent(new CustomEvent('youtube-api-ready'));
					};
				}

				window.addEventListener('youtube-api-ready', initPlayer, { once: true });
			} else if (w.YT && w.YT.Player) {
				initPlayer();
			} else {
				window.addEventListener('youtube-api-ready', initPlayer, { once: true });
			}
		}
	});

	function initPlayer() {
		// eslint-disable-next-line @typescript-eslint/no-explicit-any
		const w = window as any;
		if (!w.YT || !w.YT.Player) return;

		player = new w.YT.Player(containerId, {
			videoId: id,
			playerVars: {
				autoplay: 1,
				controls: controls ? 1 : 0,
				disablekb: 1,
				fs: 0,
				modestbranding: 1,
				rel: 0,
				showinfo: 0,
				mute: muted || volume === 0 ? 1 : 0
			},
			events: {
				// eslint-disable-next-line @typescript-eslint/no-explicit-any
				onReady: (event: any) => {
					loading = false;
					player = event.target;
					playerReady = true;
					const vol = Math.round(volume * 100);
					if (muted || volume === 0) {
						event.target.mute();
					} else {
						event.target.unMute();
						event.target.setVolume(vol);
					}
					event.target.playVideo();
				},
				// eslint-disable-next-line @typescript-eslint/no-explicit-any
				onError: (event: any) => {
					loading = false;
					error = 'Failed to load YouTube video';
					console.error('YouTube Player Error:', event.data);
				}
			}
		});
	}

	export function getCurrentTime() {
		if (player && typeof player.getCurrentTime === 'function') {
			return player.getCurrentTime();
		}
		return 0;
	}

	export function rotateVideo() {
		rotation += 90;
	}

	onDestroy(() => {
		if (player && typeof player.destroy === 'function') {
			player.destroy();
		}
	});
</script>

<div class="relative w-full h-full bg-black group/player overflow-hidden">
	<div
		class="absolute top-1/2 left-1/2 object-contain transition-all duration-300 {controls
			? ''
			: 'pointer-events-none'}"
		style="width: {isFillMode ? '180%' : '100%'}; height: {isFillMode ? '180%' : '100%'}; transform: translate(-50%, -50%) rotate({rotation}deg); display: flex; align-items: center; justify-content: center;"
	>
		<div
			id={containerId}
			class="w-full h-full"
			style={controls ? '' : 'pointer-events: none;'}
		></div>
	</div>

	<!-- Invisible overlay to prevent clicking iframe and passing clicks to parent -->
	<div
		class="absolute inset-0 z-10 {controls
			? 'pointer-events-none'
			: 'pointer-events-auto'} bg-transparent"
	></div>

	{#if loading}
		<div
			class="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm z-20"
		>
			<RefreshCw class="w-8 h-8 text-white animate-spin opacity-50" />
		</div>
	{/if}

	{#if error}
		<div
			class="absolute inset-0 flex flex-col items-center justify-center bg-zinc-900 z-20 p-4 text-center pointer-events-auto"
		>
			<AlertCircle class="w-8 h-8 text-red-500 mb-2 opacity-50" />
			<p class="text-[10px] font-black uppercase tracking-widest text-zinc-500">{error}</p>
			<button
				onclick={(e) => {
					e.stopPropagation();
					error = null;
					loading = true;
					initPlayer();
				}}
				class="mt-4 px-3 py-1 bg-zinc-800 hover:bg-zinc-700 text-white text-[10px] font-bold rounded-lg transition-colors cursor-pointer"
			>
				{t('theater.live.multiview.retry')}
			</button>
		</div>
	{/if}
</div>
