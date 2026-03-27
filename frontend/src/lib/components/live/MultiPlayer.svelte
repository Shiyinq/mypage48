<script lang="ts">
	import { onMount, onDestroy, createEventDispatcher } from 'svelte';
	import { fade, scale, slide } from 'svelte/transition';
	import { live as liveApi } from '$lib/apis/live';
	import { API_BASE } from '$lib/apis/client';
	import { RefreshCw, AlertCircle, Circle, Square } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import GiftOverlay from './GiftOverlay.svelte';

	import { giftEvents, type GiftEvent } from '$lib/stores/gift';
	
	const { t } = useTranslation();

	export let platform = ''; // 'showroom' or 'idn'
	export let id = ''; // room_id or live_id
	export let volume = 1;
	export let muted = false;
	export let roomIdentifier = ''; // IDN username

	function getExternalMediaUrl(url?: string) {
		if (!url) return '';
		if (url.includes('idn.app')) {
			try {
				const u = new URL(url);
				u.searchParams.delete('timestamp');
				return u.toString();
			} catch (e) {
				return url;
			}
		}
		return url;
	}

	let videoElement: HTMLVideoElement;
	let hls: any;
	let loading = true;
	let error: string | null = null;
	let initializing = false;
	let currentPlatform = '';
	let currentId = '';
	
	export let isRecording = false;
	let mediaRecorder: any = null;
	let recordedChunks: any[] = [];

	let isEffectivelyMuted = false;
	$: isEffectivelyMuted = muted || (isNaN(Number(volume)) ? false : Number(volume) === 0);

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

	$: if (videoElement || volume !== undefined || muted !== undefined) {
		syncAudioState();
	}

	// Hardware Hammer: Reinforce mute every 200ms for 10s after playback starts
	let hammerInterval: any;
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

	const dispatch = createEventDispatcher();

	async function initPlayer() {
		if (typeof window === 'undefined' || initializing) return;
		if (!videoElement || !platform || !id) return;
		
		// Prevent redundant re-init if source hasn't changed
		if (platform === currentPlatform && id === currentId && (hls || videoElement.src)) return;
		
		initializing = true;
		loading = true;
		error = null;
		
		currentPlatform = platform;
		currentId = id;

		if (hls) {
			hls.destroy();
			hls = null;
		}

		try {
			const res = await liveApi.getStreamingUrl(platform, id);
			if (res && res.streaming_urls && res.streaming_urls.length > 0) {
				let streamUrl = res.streaming_urls[0].url;
				
				if (platform === 'idn' || platform === 'showroom') {
					streamUrl = `${API_BASE}/jkt48/live/proxy?url=${encodeURIComponent(streamUrl)}`;
				}

				if ((window as any).Hls && (window as any).Hls.isSupported()) {
					const Hls = (window as any).Hls;
					hls = new Hls({
						enableWorker: true,
						lowLatencyMode: true,
						backBufferLength: 60
					});
					
					hls.loadSource(streamUrl);
					hls.attachMedia(videoElement);
					
					hls.on(Hls.Events.MANIFEST_PARSED, () => {
						syncAudioState(); // Force sync when starting
						startHammer(); // Start the hammer
						videoElement.play().catch(e => console.log('Autoplay blocked', e));
						loading = false;
					});

					hls.on(Hls.Events.ERROR, (event: any, data: any) => {
						if (data.type === Hls.ErrorTypes.NETWORK_ERROR && data.response?.code === 404) {
							console.log('Proxy/Stream 404 detected, triggering offline');
							dispatch('offline');
							error = $t('theater.live.offline'); 
							hls.destroy();
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
									error = $t('theater.live.multiview.stream_error', { details: data.details });
									hls.destroy();
									loading = false;
									break;
							}
						}
					});
				} else if (videoElement.canPlayType('application/vnd.apple.mpegurl')) {
					videoElement.src = streamUrl;
					videoElement.addEventListener('loadedmetadata', () => {
						videoElement.play().catch(e => console.log('Autoplay blocked', e));
						loading = false;
					});
				} else {
					error = $t('theater.live.multiview.hls_not_supported');
					loading = false;
				}
			} else {
				error = $t('theater.live.multiview.no_stream_found');
				loading = false;
			}
		} catch (e: any) {
			console.error('MultiPlayer init failed:', e);
			if (e?.status === 404) {
				dispatch('offline');
			}
			error = $t('theater.live.multiview.failed_load_stream');
			loading = false;
		} finally {
			initializing = false;
		}
	}

	export function takeScreenshot(memberName?: string) {
		if (!videoElement) return;

		const canvas = document.createElement('canvas');
		canvas.width = videoElement.videoWidth;
		canvas.height = videoElement.videoHeight;
		const ctx = canvas.getContext('2d');

		if (ctx) {
			try {
				ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);
				const dataUrl = canvas.toDataURL('image/png');
				const link = document.createElement('a');
				const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
				const name = memberName ? memberName.replace(/\s+/g, '_') : 'JKT48_Live';
				link.download = `Screenshot_${name}_${timestamp}.png`;
				link.href = dataUrl;
				link.click();
			} catch (err) {
				console.error('Screenshot failed:', err);
			}
		}
	}

	export async function toggleRecording(memberName?: string) {
		if (!videoElement) return;

		if (!isRecording) {
			try {
				const v = videoElement as any;
				let stream = v['captureStream'] ? v['captureStream']() : v['mozCaptureStream']();

				// Zero-Loss Strategy: Check for tracks INSTANTLY
				if (stream.getTracks().length === 0) {
					await new Promise((r) => setTimeout(r, 200));
					stream = v['captureStream'] ? v['captureStream']() : v['mozCaptureStream']();
				}

				// Try common mime types
				const types = [
					'video/webm;codecs=vp9,opus',
					'video/webm;codecs=vp8,opus',
					'video/webm',
					'video/mp4'
				];

				let selectedType = '';
				for (const type of types) {
					if (MediaRecorder.isTypeSupported(type)) {
						selectedType = type;
						break;
					}
				}

				mediaRecorder = new MediaRecorder(stream, selectedType ? { mimeType: selectedType } : {});

				recordedChunks = [];
				mediaRecorder.ondataavailable = (e: any) => {
					if (e.data.size > 0) {
						recordedChunks.push(e.data);
					}
				};

				mediaRecorder.onstop = () => {
					const blob = new Blob(recordedChunks, { type: selectedType || 'video/webm' });
					const url = URL.createObjectURL(blob);
					const link = document.createElement('a');
					const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
					const name = memberName ? memberName.replace(/\s+/g, '_') : 'JKT48_Live';
					const ext = selectedType.includes('mp4') ? 'mp4' : 'webm';
					link.href = url;
					link.download = `Recording_${name}_${timestamp}.${ext}`;
					link.click();
					URL.revokeObjectURL(url);
				};

				mediaRecorder.start();
				isRecording = true;
			} catch (err) {
				console.error('Recording failed to start:', err);
			}
		} else {
			if (mediaRecorder) {
				mediaRecorder.stop();
				isRecording = false;
			}
		}
	}

	onMount(() => {
		if ((window as any).Hls) {
			initPlayer();
		} else {
			// Checklist to ensure only one script is added
			if (!document.getElementById('hls-js-script')) {
				const script = document.createElement('script');
				script.id = 'hls-js-script';
				script.src = 'https://cdn.jsdelivr.net/npm/hls.js@latest';
				script.onload = () => {
					// Trigger init for all players waiting
					window.dispatchEvent(new CustomEvent('hls-js-loaded'));
					initPlayer();
				};
				document.head.appendChild(script);
			} else {
				// Wait for the script to load if already added by another component
				window.addEventListener('hls-js-loaded', initPlayer, { once: true });
			}
		}
	});

	onDestroy(() => {
		if (hls) hls.destroy();
	});

	// Re-init if platform or id changes
	$: if (platform && id && videoElement) {
		initPlayer();
	}
</script>

<div class="relative w-full h-full bg-black group/player overflow-hidden">
	<!-- svelte-ignore a11y-media-has-caption -->
	<video
		bind:this={videoElement}
		class="w-full h-full object-contain"
		playsinline
		muted={isEffectivelyMuted}
		on:play={syncAudioState}
		on:playing={syncAudioState}
		on:volumechange={syncAudioState}
	></video>

	<!-- Multi-view Floating Gift Overlay -->
	<GiftOverlay {roomIdentifier} />

	{#if loading}
		<div class="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm z-10">
			<RefreshCw class="w-8 h-8 text-white animate-spin opacity-50" />
		</div>
	{/if}

	{#if error}
		<div class="absolute inset-0 flex flex-col items-center justify-center bg-zinc-900 z-10 p-4 text-center">
			<AlertCircle class="w-8 h-8 text-red-500 mb-2 opacity-50" />
			<p class="text-[10px] font-black uppercase tracking-widest text-zinc-500">{error}</p>
			<button 
				on:click={initPlayer}
				class="mt-4 px-3 py-1 bg-zinc-800 hover:bg-zinc-700 text-white text-[10px] font-bold rounded-lg transition-colors"
			>
				{$t('theater.live.multiview.retry')}
			</button>
		</div>
	{/if}
</div>
