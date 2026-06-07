<script lang="ts">
	import { onDestroy, untrack } from 'svelte';
	import { fade } from 'svelte/transition';
	import { live as liveApi } from '$lib/apis/live';
	import { API_BASE } from '$lib/apis/client';
	import { captureVideoScreenshot, startVideoRecording, downloadRecording } from '$lib/utils/media';
	import { RefreshCw, AlertCircle } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { hlsSettings } from '$lib/stores/hlsSettings.svelte';
	import GiftOverlay from './GiftOverlay.svelte';

	const { t } = useTranslation();

	let videoElement: HTMLVideoElement | undefined = $state();
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	let hls: any;
	let loading = $state(true);
	let error: string | null = $state(null);
	let initializing = false;
	let currentPlatform = '';
	let currentId = '';
	let isBuffering = $state(false);
	let autoplayBlocked = $state(false);

	interface Props {
		platform?: string; // 'showroom' or 'idn'
		id?: string; // room_id or live_id
		volume?: number;
		muted?: boolean;
		roomIdentifier?: string; // IDN username
		isRecording?: boolean;
		onoffline?: () => void;
	}

	let {
		platform = '',
		id = '',
		volume = 1,
		muted = false,
		roomIdentifier = '',
		isRecording = $bindable(false),
		onoffline
	}: Props = $props();
	let mediaRecorder: MediaRecorder | null = null;
	let recordedChunks: Blob[] = [];

	let isEffectivelyMuted = $state(false);
	$effect(() => {
		isEffectivelyMuted = muted || (isNaN(Number(volume)) ? false : Number(volume) === 0);
	});

	function syncAudioState() {
		if (!videoElement) return;
		const vol = Number(volume);

		if (!isNaN(vol)) {
			// Double-lock volume to 0 if effectively muted
			const targetVolume = isEffectivelyMuted ? 0 : Math.max(0, Math.min(1, vol));
			if (videoElement.volume !== targetVolume) {
				videoElement.volume = targetVolume;
			}
		}

		if (videoElement.muted !== isEffectivelyMuted) {
			videoElement.muted = isEffectivelyMuted;
			// For attribute-level binding (more persistent in some browsers)
			if (isEffectivelyMuted) {
				videoElement.setAttribute('muted', 'true');
			} else {
				videoElement.removeAttribute('muted');
			}
		}
	}

	$effect(() => {
		if (videoElement || volume !== undefined || muted !== undefined) {
			syncAudioState();
		}
	});

	// Hardware Hammer: Reinforce mute every 200ms for 10s after playback starts
	let hammerInterval: ReturnType<typeof setInterval> | undefined;
	function startHammer() {
		if (hammerInterval) clearInterval(hammerInterval);
		let count = 0;
		hammerInterval = setInterval(() => {
			if (isEffectivelyMuted) syncAudioState();
			count++;
			if (count > 50) clearInterval(hammerInterval); // Stop after 10s
		}, 200);
	}

	// Floating Gift Logic - Handled by GiftOverlay component

	async function initPlayer(force = false) {
		if (typeof window === 'undefined' || initializing) return;
		if (!videoElement || !platform || !id) return;

		// Prevent redundant re-init if source hasn't changed
		if (!force && platform === currentPlatform && id === currentId && (hls || videoElement.src)) {
			return;
		}

		initializing = true;
		loading = true;
		error = null;

		currentPlatform = platform;
		currentId = id;

		if (hls) {
			hls.destroy();
			hls = null;
		}
		if (videoElement) {
			videoElement.pause();
			videoElement.src = '';
			videoElement.load();
		}

		try {
			const res = await liveApi.getStreamingUrl(platform, id);
			if (res && res.streaming_urls && res.streaming_urls.length > 0) {
				let streamUrl = res.streaming_urls[0].url;

				if (platform === 'idn' || platform === 'showroom') {
					streamUrl = `${API_BASE}/jkt48/live/proxy?url=${encodeURIComponent(streamUrl)}`;
				}

				// eslint-disable-next-line @typescript-eslint/no-explicit-any
				const w = window as any;
				if (w.Hls && w.Hls.isSupported()) {
					const Hls = w.Hls;
					hls = new Hls({
						enableWorker: true,
						lowLatencyMode: true,
						backBufferLength: 60,
						// Tuned for proxied live streams
						liveSyncDurationCount: hlsSettings.config.liveSyncDurationCount,
						liveMaxLatencyDurationCount: hlsSettings.config.liveMaxLatencyDurationCount,
						liveDurationInfinity: true,
						// Aggressive retry for network errors (proxy can be flaky)
						manifestLoadingMaxRetry: 6,
						manifestLoadingRetryDelay: 1000,
						levelLoadingMaxRetry: 6,
						levelLoadingRetryDelay: 1000,
						fragLoadingMaxRetry: 6,
						fragLoadingRetryDelay: 1000,
						// Lower buffer thresholds for faster start
						maxBufferLength: 10,
						maxMaxBufferLength: 30,
						maxBufferSize: 30 * 1000 * 1000, // 30MB
						maxBufferHole: 0.5,
						// Increase timeouts for slow proxy
						fragLoadingTimeOut: 30000,
						manifestLoadingTimeOut: 15000,
						levelLoadingTimeOut: 15000
					});

					hls.loadSource(streamUrl);
					hls.attachMedia(videoElement);

					hls.on(Hls.Events.MANIFEST_PARSED, () => {
						syncAudioState(); // Force sync when starting
						startHammer(); // Start the hammer
						videoElement?.play().catch((e: Error) => {
							if (e.name === 'NotAllowedError') {
								autoplayBlocked = true;
							}
						});
						loading = false;
					});

					hls.on(
						Hls.Events.ERROR,
						(
							event: unknown,
							data: { type: string; fatal?: boolean; details?: string; response?: { code: number } }
						) => {
							if (data.type === Hls.ErrorTypes.NETWORK_ERROR && data.response?.code === 404) {
								console.log('Proxy/Stream 404 detected, triggering offline');
								onoffline?.();
								error = t('theater.live.offline');
								if (hls) hls.destroy();
								loading = false;
								return;
							}

							if (data.fatal) {
								switch (data.type) {
									case Hls.ErrorTypes.NETWORK_ERROR:
										console.log('Fatal network error encountered, try to recover');
										hls.startLoad();
										break;
									case Hls.ErrorTypes.MEDIA_ERROR:
										console.log('Fatal media error encountered, try to recover');
										hls.recoverMediaError();
										break;
									default:
										console.error('Fatal unrecoverable error:', data);
										error = t('theater.live.multiview.stream_error', {
											details: data.details || 'Unknown error'
										});
										if (hls) hls.destroy();
										loading = false;
										break;
								}
							}
						}
					);
				} else if (videoElement.canPlayType('application/vnd.apple.mpegurl')) {
					videoElement.src = streamUrl;
					videoElement.addEventListener('loadedmetadata', () => {
						videoElement?.play().catch((_e: Error) => {
							if (_e.name === 'NotAllowedError') {
								autoplayBlocked = true;
							}
						});
						loading = false;
					});
				} else {
					error = t('theater.live.multiview.hls_not_supported');
					loading = false;
				}
			} else {
				error = t('theater.live.multiview.no_stream_found');
				loading = false;
			}
		} catch (_e: unknown) {
			console.error('MultiPlayer init failed:', _e);
			if ((_e as { status?: number })?.status === 404) {
				onoffline?.();
			}
			error = t('theater.live.multiview.failed_load_stream');
			loading = false;
		} finally {
			initializing = false;
		}
	}

	$effect(() => {
		// React to hlsSettings.mode changes
		if (hlsSettings.mode && hls) {
			console.log('HLS mode changed, re-initializing player to flush buffers...');
			untrack(() => {
				setTimeout(() => initPlayer(true), 100);
			});
		}
	});

	function retryPlayback() {
		if (!videoElement) return;
		autoplayBlocked = false;
		videoElement.play().catch((_e) => {
			if (_e.name === 'NotAllowedError') {
				autoplayBlocked = true;
			}
		});
	}

	export function takeScreenshot(memberName?: string) {
		if (videoElement) captureVideoScreenshot(videoElement, memberName || 'JKT48_Live');
	}

	export async function toggleRecording(memberName?: string) {
		if (!videoElement) return;

		if (!isRecording) {
			mediaRecorder = await startVideoRecording(videoElement, (blob) => {
				recordedChunks.push(blob);
			});

			if (mediaRecorder) {
				recordedChunks = [];
				isRecording = true;
				mediaRecorder.onstop = () => {
					downloadRecording(recordedChunks, memberName || 'JKT48_Live');
					isRecording = false;
				};
			}
		} else if (mediaRecorder) {
			mediaRecorder.stop();
		}
	}

	$effect(() => {
		if (platform && id && videoElement) {
			// eslint-disable-next-line @typescript-eslint/no-explicit-any
			const w = window as any;
			if (w.Hls) {
				untrack(() => initPlayer());
			} else {
				// Checklist to ensure only one script is added
				if (!document.getElementById('hls-js-script')) {
					const script = document.createElement('script');
					script.id = 'hls-js-script';
					script.src = 'https://cdn.jsdelivr.net/npm/hls.js@latest';
					script.onload = () => {
						// Trigger init for all players waiting
						window.dispatchEvent(new CustomEvent('hls-js-loaded'));
						untrack(() => initPlayer());
					};
					document.head.appendChild(script);
				} else {
					// Wait for the script to load if already added by another component
					const handleLoaded = () => untrack(() => initPlayer());
					window.addEventListener('hls-js-loaded', handleLoaded, { once: true });
				}
			}
		}
	});

	onDestroy(() => {
		if (hls) {
			hls.destroy();
			hls = null;
		}
		if (hammerInterval) {
			clearInterval(hammerInterval);
		}
	});
</script>

<div class="relative w-full h-full bg-black group/player overflow-hidden">
	<video
		bind:this={videoElement}
		class="w-full h-full object-contain"
		playsinline
		muted={isEffectivelyMuted}
		onplay={syncAudioState}
		onplaying={() => {
			syncAudioState();
			isBuffering = false;
		}}
		onwaiting={() => (isBuffering = true)}
		onstalled={() => (isBuffering = true)}
		oncanplay={() => (isBuffering = false)}
		onpause={() => (isBuffering = false)}
		onvolumechange={syncAudioState}
	></video>

	{#if autoplayBlocked}
		<button
			class="absolute inset-0 flex flex-col items-center justify-center bg-black/60 backdrop-blur-[2px] z-20 group/autoplay cursor-pointer"
			onclick={(e) => {
				e.stopPropagation();
				retryPlayback();
			}}
		>
			<div
				class="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center border-2 border-white/40 group-hover/autoplay:scale-110 group-hover/autoplay:bg-white/30 transition-all duration-300"
			>
				<RefreshCw class="w-8 h-8 text-white" />
			</div>
			<p class="mt-4 text-[10px] font-black uppercase tracking-[0.2em] text-white">
				{t('theater.live.multiview.tap_to_play')}
			</p>
			<p class="mt-1 text-white/40 text-[8px] font-bold uppercase tracking-widest text-center px-4">
				{t('theater.live.autoplay_description')}
			</p>
		</button>
	{:else if isBuffering && !loading}
		<div
			class="absolute inset-0 flex items-center justify-center bg-black/20 backdrop-blur-[1px] z-[15] pointer-events-none"
			transition:fade
		>
			<div class="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
		</div>
	{/if}

	<!-- Multi-view Floating Gift Overlay -->
	<GiftOverlay {roomIdentifier} />

	{#if loading}
		<div
			class="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm z-10"
		>
			<RefreshCw class="w-8 h-8 text-white animate-spin opacity-50" />
		</div>
	{/if}

	{#if error}
		<div
			class="absolute inset-0 flex flex-col items-center justify-center bg-zinc-900 z-10 p-4 text-center"
		>
			<AlertCircle class="w-8 h-8 text-red-500 mb-2 opacity-50" />
			<p class="text-[10px] font-black uppercase tracking-widest text-zinc-500">{error}</p>
			<button
				onclick={() => initPlayer(true)}
				class="mt-4 px-3 py-1 bg-zinc-800 hover:bg-zinc-700 text-white text-[10px] font-bold rounded-lg transition-colors"
			>
				{t('theater.live.multiview.retry')}
			</button>
		</div>
	{/if}
</div>
