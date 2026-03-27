<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { liveStore, currentStream, otherLive, liveLoading } from '$lib/stores/live';
	import { showToast } from '$lib/stores/toast';
	import { API_BASE } from '$lib/apis/client';
	import type { LiveStatus } from '$lib/types';
	import IDNChat from '$lib/components/live/IDNChat.svelte';
	import ShowroomChat from '$lib/components/live/ShowroomChat.svelte';
	import GiftOverlay from '$lib/components/live/GiftOverlay.svelte';
	import ThemeToggle from '$lib/components/landing-page/ThemeToggle.svelte';
	import { theme, setTheme } from '$lib/stores/theme';
	import {
		ArrowLeft,
		Users,
		MessageCircle,
		MessageSquare,
		Info,
		ChevronRight,
		ChevronLeft,
		RefreshCw,
		Maximize2,
		Minimize2,
		Maximize,
		Minimize,
		Camera,
		Circle,
		Square,
		Volume2,
		VolumeX,
		PictureInPicture2,
		Play,
		Pause,
		Sun,
		Moon,
		RotateCw
	} from 'lucide-svelte';
	import { fade, fly } from 'svelte/transition';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import { getLiveLogoUrl } from '$lib/constants/live';

	const { t } = useTranslation();
	$: ({ platform, id } = $page.params);

	let videoElement: HTMLVideoElement;
	let hls: any;
	let loadingOtherLive = false;
	let initializing = false;
	let scriptLoaded = false;
	let lastInitializedId = '';
	let initCount = 0;
	let chatVisible = true;
	let isFocusMode = false;
	let isRecording = false;
	let logoError = false;
	$: logoUrl = getLiveLogoUrl(platform || '');
	let mediaRecorder: any = null;
	let recordedChunks: any[] = [];
	let sidebarMode: 'chat' | 'list' = 'chat';
	let volume = 1;
	let isMuted = false;
	let currentTime = 0;
	let duration = 0;
	let isPaused = false;
	let bufferedEnd = 0;
	let peakDuration = 0;
	let isFullscreen = false;
	let showControls = true;
	let controlsTimeout: any;
	let playerContainer: HTMLDivElement;
	let recordingDuration = 0;
	let recordingTimer: any = null;
	let refreshInterval: any = null;
	let ignoreNextVideoClick = false;
	let rotation = 0;
	let videoWidth = 0;
	let videoHeight = 0;
	let playerWidth = 0;
	let playerHeight = 0;

	$: videoAspectRatio = videoWidth > 0 && videoHeight > 0 ? videoWidth / videoHeight : 16 / 9;

	function rotateVideo() {
		rotation += 90;
	}

	function resetControlsTimeout(isTouch = false) {
		if (isTouch && !showControls) {
			ignoreNextVideoClick = true;
		}
		showControls = true;
		clearTimeout(controlsTimeout);
		controlsTimeout = setTimeout(() => {
			showControls = false;
		}, 5000);
	}

	function handleFullscreenChange() {
		isFullscreen = document.fullscreenElement !== null;
		resetControlsTimeout();
	}

	// Keep the largest duration we've seen to avoid shrinking scale during seeking/buffer resets
	$: if (currentTime > peakDuration) peakDuration = currentTime;
	$: if (duration > 0 && duration !== Infinity && duration > peakDuration) peakDuration = duration;
	$: displayDuration = peakDuration || currentTime;
	$: isLive = duration === Infinity || isNaN(duration) || duration === 0;

	$: memberName = $currentStream?.member?.name || null;
	$: roomIdentifier = $currentStream?.room_identifier || null;
	$: streamingUrls = $currentStream?.streaming_urls || [];

	$: if (scriptLoaded && platform && id && lastInitializedId !== `${platform}-${id}`) {
		lastInitializedId = `${platform}-${id}`;
		initPlayer();
		fetchOtherLive();
	}

	function getMemberId(m: LiveStatus | any) {
		if (m.platform === 'showroom') return m.room_id || m.room_url_key;
		return m.live_id || m.room_url_key;
	}

	const fallbackAvatar = 'https://placehold.co/640x960?text=NO%20IMAGE';

	async function initPlayer() {
		const currentInit = ++initCount;
		try {
			initializing = true;
			const p = platform as string;
			const i = id as string;
			if (!p || !i) throw new Error('Missing params');

			await liveStore.loadStream(p, i);

			// If a newer initialization has started, stop this one
			if (currentInit !== initCount) return;

			const current = $currentStream;
			if (current && current.streaming_urls && current.streaming_urls.length > 0) {
				const rawUrl = current.streaming_urls[0]?.url;
				if (!rawUrl) return;

				let streamUrl: string = rawUrl;

				// Use proxy for IDN or Showroom to bypass CORS
				if (p === 'idn' || p === 'showroom') {
					// @ts-ignore
					streamUrl = `${API_BASE}/jkt48/live/proxy?url=${encodeURIComponent(streamUrl as string)}`;
				}

				if (typeof window !== 'undefined' && (window as any).Hls && videoElement) {
					const Hls = (window as any).Hls;
					if (Hls.isSupported()) {
						if (hls) hls.destroy();
						hls = new Hls();
						hls.loadSource(streamUrl);
						hls.attachMedia(videoElement);
						hls.on(Hls.Events.MANIFEST_PARSED, () => {
							videoElement.play().catch((e) => console.log('Autoplay blocked', e));
							resetControlsTimeout();
						});

						hls.on(Hls.Events.ERROR, (event: any, data: any) => {
							if (data.type === Hls.ErrorTypes.NETWORK_ERROR && data.response?.code === 404) {
								console.log('Proxy/Stream 404 detected, redirecting to home');
								showToast($t('theater.live.offline'), 'error');
								goto('/jkt48/live');
							}
						});
					} else if (videoElement.canPlayType('application/vnd.apple.mpegurl')) {
						videoElement.src = streamUrl;
						videoElement.addEventListener('loadedmetadata', () => {
							videoElement.play().catch((e) => console.log('Autoplay blocked', e));
							resetControlsTimeout();
						});
					}
				}
			}
		} catch (e: any) {
			console.error('Player init failed:', e);
			if (currentInit !== initCount) return;

			// Handle 404 error from server (Offline)
			if (e?.status === 404) {
				showToast($t('theater.live.offline'), 'error');
				goto('/jkt48/live');
			}
		} finally {
			if (currentInit === initCount) {
				initializing = false;
			}
		}
	}

	async function fetchOtherLive() {
		try {
			const p = platform as string;
			const i = id as string;
			if (!p || !i) return;

			loadingOtherLive = true;
			await liveStore.loadOtherLive(p, i);
		} catch (e) {
			console.error('Failed to fetch other live members:', e);
		} finally {
			loadingOtherLive = false;
		}
	}

	onMount(() => {
		// Periodic refresh of stream info (viewer count)
		refreshInterval = setInterval(() => {
			if (platform && id && !initializing) {
				liveStore.refreshStreamInfo(platform, id).catch((e) => {
					if (e?.status === 404) {
						showToast($t('theater.live.offline'), 'error');
						goto('/jkt48/live');
					}
				});
				fetchOtherLive();
			}
		}, 30000);

		if ((window as any).Hls) {
			scriptLoaded = true;
			return;
		}

		// Load hls.js from CDN
		const script = document.createElement('script');
		script.src = 'https://cdn.jsdelivr.net/npm/hls.js@latest';
		script.onload = () => {
			scriptLoaded = true;
		};
		document.head.appendChild(script);
	});

	onDestroy(() => {
		if (hls) {
			hls.destroy();
		}
		if (recordingTimer) {
			clearInterval(recordingTimer);
		}
		if (refreshInterval) {
			clearInterval(refreshInterval);
		}
		liveStore.reset();
	});

	function toggleChat() {
		chatVisible = !chatVisible;
	}

	function toggleFocus() {
		isFocusMode = !isFocusMode;
		if (typeof document !== 'undefined') {
			if (isFocusMode) {
				document.body.style.overflow = 'hidden';
				// On mobile, hide chat when entering focus mode
				if (window.innerWidth < 1024) {
					chatVisible = false;
				}
			} else {
				document.body.style.overflow = 'auto';
				// When exiting focus mode, show chat again
				chatVisible = true;
			}
		}
	}

	async function refreshStream() {
		if (hls) {
			hls.destroy();
			hls = null;
		}
		if (videoElement) {
			videoElement.pause();
			videoElement.src = '';
			videoElement.load();
		}
		peakDuration = 0; // Reset on manual refresh
		await initPlayer();
	}

	function updateBufferAndDuration() {
		if (videoElement) {
			const buffered = videoElement.buffered;
			if (buffered.length > 0) {
				// The furthest buffered point is usually the 'live edge' for HLS
				const furthestBuffer = buffered.end(buffered.length - 1);
				if (furthestBuffer > peakDuration) {
					peakDuration = furthestBuffer;
				}

				// Standard buffered end for the current segment
				for (let i = 0; i < buffered.length; i++) {
					if (currentTime >= buffered.start(i) && currentTime <= buffered.end(i)) {
						bufferedEnd = buffered.end(i);
						break;
					}
				}
			}

			const nativeDuration = videoElement.duration;
			if (nativeDuration !== Infinity && !isNaN(nativeDuration)) {
				if (nativeDuration > peakDuration) peakDuration = nativeDuration;
			}
		}
	}

	function takeScreenshot() {
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
				alert(
					'Failed to capture screenshot. This might be due to security restrictions on the stream.'
				);
			}
		}
	}

	async function toggleRecording() {
		if (!videoElement) return;

		if (!isRecording) {
			try {
				const v = videoElement as any;
				let stream = v['captureStream'] ? v['captureStream']() : v['mozCaptureStream']();

				// Zero-Loss Strategy: Check for tracks INSTANTLY
				if (stream.getTracks().length === 0) {
					// ONLY delay if we hit a race condition/warmup (common after refresh)
					await new Promise((r) => setTimeout(r, 200));
					stream = v['captureStream'] ? v['captureStream']() : v['mozCaptureStream']();
				}

				if (!stream.getTracks().length) {
					console.warn('Tracks still empty, fallback strategy initiated.');
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
				recordingDuration = 0;
				recordingTimer = setInterval(() => {
					recordingDuration++;
				}, 1000);
			} catch (err) {
				console.error('Recording failed to start:', err);
				// Standard alert only if it's a persistent error
				alert('Record failed. Please ensure the video is playing and try again in a few seconds.');
			}
		} else {
			if (mediaRecorder) {
				mediaRecorder.stop();
				isRecording = false;
				if (recordingTimer) {
					clearInterval(recordingTimer);
					recordingTimer = null;
				}
			}
		}
	}

	function toggleMute() {
		isMuted = !isMuted;
		if (videoElement) videoElement.muted = isMuted;
	}

	function toggleTheme() {
		if ($theme === 'dark') {
			setTheme('light');
		} else {
			setTheme('dark');
		}
	}

	function handleVolumeChange(e: any) {
		volume = parseFloat(e.target.value);
		if (videoElement) {
			videoElement.volume = volume;
			if (volume > 0) isMuted = false;
		}
	}

	async function togglePiP() {
		try {
			if ((document as any).pictureInPictureElement) {
				await (document as any).exitPictureInPicture();
			} else if (videoElement) {
				await (videoElement as any).requestPictureInPicture();
			}
		} catch (error) {
			console.error('PiP failed', error);
		}
	}

	async function toggleFullscreen() {
		if (!playerContainer) return;
		try {
			if (!document.fullscreenElement) {
				await playerContainer.requestFullscreen();
			} else {
				await document.exitFullscreen();
			}
		} catch (err) {
			console.error('Fullscreen toggle failed:', err);
		}
	}

	function handleSeek(e: any) {
		if (videoElement) {
			const time = parseFloat(e.target.value);
			videoElement.currentTime = time;
		}
	}

	function togglePlayPause() {
		if (videoElement) {
			if (videoElement.paused) videoElement.play();
			else videoElement.pause();
		}
	}

	function formatTime(seconds: number) {
		if (isNaN(seconds) || seconds === Infinity) return '00:00';
		const h = Math.floor(seconds / 3600);
		const m = Math.floor((seconds % 3600) / 60);
		const s = Math.floor(seconds % 60);
		if (h > 0) {
			return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
		}
		return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
	}
</script>

<svelte:head>
	<title>Live Streaming | MyPage48</title>
</svelte:head>

<div
	class="flex flex-col lg:flex-row gap-4 transition-all duration-500 ease-in-out {isFocusMode
		? 'fixed inset-0 !top-0 !mt-0 z-[5000] bg-white dark:bg-zinc-950 p-2 sm:p-4 h-screen w-screen'
		: 'h-[calc(100vh-80px)] mt-4 px-4 pb-4'}"
>
	<!-- Main Player Area -->
	<div class="flex-[1.5] lg:flex-1 flex flex-col gap-4 min-h-0 p-1">
		<!-- Back Button & Info -->
		<div class="flex items-center justify-between">
			<div class="flex items-center gap-3">
				{#if !isFocusMode}
					<a
						href="/jkt48/live"
						class="flex items-center gap-2 text-slate-500 dark:text-slate-400 hover:text-red-600 transition-colors font-bold text-sm uppercase tracking-widest"
					>
						<ArrowLeft size={18} />
						{$t('theater.live.back')}
					</a>
					<div class="h-4 w-px bg-slate-200 dark:bg-zinc-800 ml-1 hidden sm:block"></div>
				{/if}
				{#if memberName}
					<div class="flex flex-col sm:flex-row items-baseline gap-1 sm:gap-2">
						<span
							class="text-xs font-black uppercase tracking-[0.15em] text-slate-900 dark:text-white leading-none"
							>{memberName}</span
						>
						<span
							class="text-[9px] font-bold text-slate-400 uppercase tracking-widest leading-none hidden sm:inline"
							>{platform?.toUpperCase()} {$t('theater.live.title')}</span
						>
					</div>
				{/if}
			</div>

			<!-- Live Badge removed from header -->
		</div>

		<!-- Video Player -->
		<div
			class="relative flex-1 bg-black rounded-3xl overflow-hidden border border-gray-100 dark:border-zinc-800 shadow-sm"
		>
			{#if initializing}
				<div
					class="absolute inset-0 flex items-center justify-center bg-zinc-950 p-8 text-center z-20"
					out:fade
				>
					<div class="flex flex-col items-center gap-6">
						<div
							class="w-16 h-16 border-4 border-white/10 border-t-red-600 rounded-full animate-spin"
						></div>
						<div>
							<div class="text-white font-black text-xl uppercase tracking-[0.2em] mb-2">
								{$t('theater.live.loading_stream')}
							</div>
							<div class="text-white/40 text-xs font-medium uppercase tracking-widest">
								{(platform || 'Live').toUpperCase()} Stream Gateway
							</div>
						</div>
					</div>
				</div>
			{:else if !$currentStream}
				<div
					class="absolute inset-0 flex flex-col items-center justify-center bg-zinc-950 text-white gap-6 px-6 text-center"
				>
					<div
						class="w-20 h-20 rounded-full bg-red-500/10 flex items-center justify-center text-red-500"
					>
						<Info size={40} />
					</div>
					<div>
						<h2 class="text-2xl font-black mb-2 uppercase tracking-tighter">Stream Offline</h2>
						<p class="text-zinc-500 max-w-sm mx-auto">
							This live session might have ended or is currently unavailable.
						</p>
					</div>
					<a
						href="/jkt48/live"
						class="px-8 py-3 rounded-2xl bg-white text-zinc-950 font-black uppercase tracking-widest text-xs hover:bg-red-600 hover:text-white transition-all"
					>
						Return Home
					</a>
				</div>
			{/if}

			<!-- svelte-ignore a11y-no-static-element-interactions -->
			<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
			<!-- svelte-ignore a11y-click-events-have-key-events -->
			<!-- svelte-ignore a11y-mouse-events-have-key-events -->
			<div
				bind:this={playerContainer}
				bind:clientWidth={playerWidth}
				bind:clientHeight={playerHeight}
				class="group/player relative w-full h-full flex items-center justify-center bg-black transition-all duration-300 {(isFullscreen ||
					isFocusMode) &&
				!showControls
					? 'cursor-none'
					: ''}"
				role="region"
				aria-label="Video Player"
				on:fullscreenchange={handleFullscreenChange}
				on:mousemove={() => resetControlsTimeout(false)}
				on:mouseleave={() => {
					showControls = false;
					clearTimeout(controlsTimeout);
				}}
				on:click={() => resetControlsTimeout(false)}
				on:touchstart={() => resetControlsTimeout(true)}
			>
				<!-- Top Info Overlay -->
				<div
					class="absolute inset-x-0 top-0 p-6 bg-gradient-to-b from-black/90 via-black/40 to-transparent transition-all duration-500 pointer-events-none z-[5500] {showControls
						? 'translate-y-0 opacity-100'
						: isFullscreen || isFocusMode
							? '-translate-y-full opacity-0'
							: 'opacity-0 -translate-y-full group-hover/player:translate-y-0 group-hover/player:opacity-100'}"
				>
					<div
						class="w-full flex items-center {isFullscreen
							? 'justify-between'
							: 'justify-end'} pointer-events-auto"
					>
						{#if isFullscreen}
							<div class="flex items-center gap-3 min-w-0">
								{#if memberName}
									<h2
										class="text-white text-lg sm:text-2xl font-black truncate drop-shadow-xl tracking-tight"
									>
										{memberName}
									</h2>
								{/if}
							</div>

							<div class="flex items-center gap-3 flex-shrink-0">
								<div
									class="flex items-center gap-2 {platform === 'showroom'
										? 'bg-[#121212] border border-white/5'
										: 'bg-red-600 shadow-lg shadow-red-600/30'} px-4 py-1.5 rounded-full"
								>
									<div class="w-1.5 h-1.5 rounded-full bg-white animate-pulse"></div>
									<span
										class="text-white text-[10px] font-black uppercase tracking-[0.1em] leading-none flex items-center"
									>
										{$t('theater.live.liveBadge')}
										<span class="mx-2 opacity-40 font-light text-[12px]">|</span>
										{#if !logoError}
											<img
												src={logoUrl}
												alt={platform}
												class="h-3 w-auto object-contain {platform === 'showroom'
													? ''
													: 'brightness-0 invert'} transition-all"
												on:error={() => (logoError = true)}
											/>
										{:else}
											{platform?.toUpperCase()}
										{/if}
									</span>
								</div>

								{#if ($currentStream?.view_num ?? 0) > 0}
									<div
										class="flex items-center gap-2 bg-black/60 backdrop-blur-md border border-white/10 px-4 py-1.5 rounded-full shadow-lg"
									>
										<Users size={14} class="text-sky-400" />
										<span class="text-white text-[11px] font-black tabular-nums">
											{$currentStream?.view_num?.toLocaleString() ?? 0}
										</span>
									</div>
								{/if}
							</div>
						{:else}
							<div
								class="flex items-center gap-2 {platform === 'showroom'
									? 'bg-[#121212] border border-white/5'
									: 'bg-red-600 shadow-lg shadow-red-600/20'} px-3 py-1 rounded-full animate-pulse"
							>
								<div class="w-1.5 h-1.5 rounded-full bg-white animate-pulse"></div>
								<span
									class="text-white text-[10px] font-black uppercase tracking-widest leading-none flex items-center"
								>
									{$t('theater.live.liveBadge')}
									<span class="mx-1.5 opacity-40 font-light text-[12px]">|</span>
									{#if !logoError}
										<img
											src={logoUrl}
											alt={platform}
											class="h-2.5 w-auto object-contain {platform === 'showroom'
												? ''
												: 'brightness-0 invert'}"
											on:error={() => (logoError = true)}
										/>
									{:else}
										{platform?.toUpperCase()}
									{/if}
								</span>
							</div>

							{#if ($currentStream?.view_num ?? 0) > 0}
								<div
									class="flex items-center gap-1.5 bg-black/40 backdrop-blur-sm border border-white/5 px-2.5 py-1 rounded-full"
								>
									<Users size={12} class="text-sky-400" />
									<span class="text-white text-[9px] font-black tabular-nums">
										{$currentStream?.view_num?.toLocaleString() ?? 0}
									</span>
								</div>
							{/if}
						{/if}
					</div>
				</div>

				<!-- svelte-ignore a11y-media-has-caption -->
				<!-- svelte-ignore a11y-click-events-have-key-events -->
				<video
					bind:this={videoElement}
					class="relative z-10 w-full h-full object-contain cursor-pointer bg-transparent transition-transform duration-300"
					style="transform: rotate({rotation}deg);"
					crossorigin="anonymous"
					autoplay
					playsinline
					on:timeupdate={() => {
						currentTime = videoElement?.currentTime || 0;
						updateBufferAndDuration();
					}}
					on:loadedmetadata={() => {
						duration = videoElement?.duration || 0;
						videoWidth = videoElement?.videoWidth || 0;
						videoHeight = videoElement?.videoHeight || 0;
						updateBufferAndDuration();
					}}
					on:play={() => (isPaused = false)}
					on:pause={() => (isPaused = true)}
					on:click={() => {
						if (ignoreNextVideoClick) {
							ignoreNextVideoClick = false;
							return;
						}
						togglePlayPause();
					}}
				></video>

				{#if roomIdentifier}
					<GiftOverlay {roomIdentifier} />
				{/if}

				<!-- Custom Player Overlay (Glassmorphism) -->
				<div
					class="absolute inset-x-0 bottom-0 p-4 bg-gradient-to-t from-black/80 via-black/40 to-transparent transition-all duration-500 pointer-events-none z-[5500] {showControls
						? 'translate-y-0 opacity-100'
						: isFullscreen || isFocusMode
							? 'translate-y-full opacity-0'
							: 'opacity-0 translate-y-full group-hover/player:translate-y-0 group-hover/player:opacity-100'}"
				>
					<div
						class="w-full flex flex-col gap-2 pointer-events-auto transition-all duration-300 px-4 sm:px-6"
					>
						<!-- Progress Bar -->
						<div class="flex flex-col gap-1 px-1">
							<div
								class="flex justify-between items-end text-[10px] font-black text-white/90 uppercase tracking-widest mb-0.5"
							>
								<span>{formatTime(currentTime)} / {formatTime(displayDuration)}</span>
							</div>

							<div class="group/progress relative h-6 flex items-center mb-1 cursor-pointer">
								<!-- Transparent track as a base -->
								<div
									class="absolute inset-x-0 h-1 bg-white/20 rounded-full pointer-events-none"
								></div>
								<!-- Played Bar (Red) -->
								<div
									class="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-red-600 rounded-full pointer-events-none transition-all z-10"
									style="width: {Math.min(100, (currentTime / (displayDuration || 1)) * 100)}%"
								></div>
								<!-- Slider Input (Invisible but interactive) -->
								<input
									type="range"
									min="0"
									max={displayDuration || 0}
									step="0.1"
									value={currentTime}
									on:input={handleSeek}
									class="absolute inset-x-0 w-full h-full bg-transparent appearance-none cursor-pointer z-20 custom-range"
								/>
							</div>
						</div>

						<!-- Controls Bar -->
						<div
							class="flex items-center justify-between gap-2 sm:gap-4 overflow-x-auto scrollbar-hide py-1"
						>
							<!-- Left Side: Play/Pause, Volume, PiP -->
							<div class="flex items-center gap-1 sm:gap-2 flex-shrink-0">
								<button
									class="w-10 h-10 flex items-center justify-center text-white hover:bg-white/10 rounded-full transition-all flex-shrink-0 cursor-pointer group/btn relative"
									on:click={togglePlayPause}
								>
									{#if isPaused}
										<Play size={22} fill="currentColor" class="ml-1" />
									{:else}
										<Pause size={22} fill="currentColor" />
									{/if}
									<div
										class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none"
									>
										{isPaused ? $t('theater.live.play') : $t('theater.live.pause')}
									</div>
								</button>

								<div class="flex items-center gap-1 group/volume">
									<button
										class="group/btn relative w-10 h-10 flex items-center justify-center text-white hover:bg-white/10 rounded-full transition-all flex-shrink-0 cursor-pointer"
										on:click={toggleMute}
									>
										{#if isMuted || volume === 0}
											<VolumeX size={18} />
										{:else}
											<Volume2 size={18} />
										{/if}
										<div
											class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none uppercase tracking-widest"
										>
											{isMuted ? $t('theater.live.unmute') : $t('theater.live.mute')}
										</div>
									</button>
									<input
										type="range"
										min="0"
										max="1"
										step="0.01"
										bind:value={volume}
										on:input={handleVolumeChange}
										class="w-0 opacity-0 group-hover/volume:w-16 sm:group-hover/volume:w-24 group-hover/volume:opacity-100 transition-all duration-300 h-1 bg-white/30 rounded-full appearance-none cursor-pointer accent-white"
									/>
								</div>

								<button
									class="group/btn relative w-10 h-10 flex items-center justify-center text-white hover:bg-white/10 rounded-full transition-all flex-shrink-0 cursor-pointer"
									on:click={togglePiP}
								>
									<PictureInPicture2 size={18} />
									<div
										class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none"
									>
										{$t('theater.live.pip')}
									</div>
								</button>
							</div>

							<!-- Right Side: Capture, Focus, Refresh, Chat -->
							<div class="flex items-center gap-1 sm:gap-2 flex-shrink-0">
								<!-- Screenshot -->
								<button
									class="group/btn relative w-10 h-10 flex items-center justify-center hover:bg-white/10 text-white rounded-full transition-all flex-shrink-0 cursor-pointer"
									on:click={takeScreenshot}
								>
									<Camera size={18} />
									<div
										class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none"
									>
										{$t('theater.live.screenshot')}
									</div>
								</button>

								<!-- Record -->
								<div class="flex items-center gap-1.5 min-w-[40px] transition-all duration-300">
									<button
										class="group/btn relative w-10 h-10 flex items-center justify-center {isRecording
											? 'bg-red-600 animate-pulse'
											: 'bg-white/10 hover:bg-white/20'} text-white rounded-full transition-all flex-shrink-0 active:scale-95 cursor-pointer"
										on:click={toggleRecording}
									>
										{#if isRecording}
											<Square size={16} fill="white" />
										{:else}
											<Circle size={16} fill="white" class="text-white" />
										{/if}
										<div
											class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none"
										>
											{isRecording ? $t('theater.live.stopRecord') : $t('theater.live.record')}
										</div>
									</button>
									{#if isRecording}
										<div
											class="text-white text-[11px] font-mono font-bold tabular-nums px-1.5 py-0.5 bg-red-600 rounded-sm shadow-sm"
											in:fly={{ x: -10, duration: 300 }}
										>
											{formatTime(recordingDuration)}
										</div>
									{/if}
								</div>

								<div class="w-px h-4 bg-white/20 mx-1"></div>

								{#if isFocusMode}
									<button
										class="group/btn relative w-10 h-10 flex items-center justify-center hover:bg-white/10 text-white rounded-full transition-all flex-shrink-0 cursor-pointer"
										on:click={toggleTheme}
									>
										{#if $theme === 'dark'}
											<Moon size={18} />
										{:else}
											<Sun size={18} />
										{/if}
										<div
											class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none uppercase tracking-widest"
										>
											{$t('theater.live.toggleTheme')}
										</div>
									</button>
								{/if}

								<!-- Focus -->
								<button
									class="group/btn relative w-10 h-10 flex items-center justify-center {isFocusMode
										? 'bg-white text-black'
										: 'hover:bg-white/10 text-white'} rounded-full transition-all flex-shrink-0 cursor-pointer"
									on:click={toggleFocus}
								>
									{#if isFocusMode}
										<Minimize2 size={18} />
									{:else}
										<Maximize2 size={18} />
									{/if}
									<div
										class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none uppercase tracking-widest"
									>
										{isFocusMode ? $t('theater.live.exitFocus') : $t('theater.live.focusMode')}
									</div>
								</button>

								<!-- Fullscreen -->
								<button
									class="group/btn relative w-10 h-10 flex items-center justify-center {isFullscreen
										? 'bg-white text-black'
										: 'hover:bg-white/10 text-white'} rounded-full transition-all flex-shrink-0 cursor-pointer"
									on:click={toggleFullscreen}
								>
									{#if isFullscreen}
										<Minimize size={18} />
									{:else}
										<Maximize size={18} />
									{/if}
									<div
										class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none uppercase tracking-widest"
									>
										{isFullscreen
											? $t('theater.live.exitFullscreen')
											: $t('theater.live.fullscreen')}
									</div>
								</button>

								<!-- Refresh -->
								<button
									class="group/btn relative w-10 h-10 flex items-center justify-center hover:bg-white/10 text-white rounded-full transition-all flex-shrink-0 cursor-pointer"
									on:click={refreshStream}
								>
									<RefreshCw size={18} class={$liveLoading ? 'animate-spin' : ''} />
									<div
										class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none"
									>
										{$t('theater.live.refresh')}
									</div>
								</button>

								<!-- Rotate -->
								<button
									class="group/btn relative w-10 h-10 flex items-center justify-center hover:bg-white/10 text-white rounded-full transition-all flex-shrink-0 cursor-pointer"
									on:click={rotateVideo}
								>
									<RotateCw size={18} class="transition-transform duration-500" />
									<div
										class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none uppercase tracking-widest"
									>
										{$t('theater.live.rotate')}
									</div>
								</button>


								<div class="w-px h-4 bg-white/20 mx-1"></div>

								<!-- Sidebar Toggle -->
								<button
									class="group/btn relative w-10 h-10 flex items-center justify-center {sidebarMode ===
									'list'
										? 'bg-white text-black'
										: 'hover:bg-white/10 text-white'} rounded-full transition-all flex-shrink-0 cursor-pointer"
									on:click={() => {
										sidebarMode = sidebarMode === 'chat' ? 'list' : 'chat';
										if (sidebarMode === 'list') fetchOtherLive();
										if (!chatVisible) chatVisible = true;
									}}
								>
									{#if sidebarMode === 'chat'}
										<Users size={18} />
									{:else}
										<MessageCircle size={18} />
									{/if}
									<div
										class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none"
									>
										{sidebarMode === 'chat'
											? $t('theater.subNav.members')
											: $t('theater.live.chat')}
									</div>
								</button>

								<!-- Chat Fold -->
								<button
									class="group/btn relative w-10 h-10 flex items-center justify-center {chatVisible
										? 'hover:bg-white/10 text-white'
										: 'bg-white text-black'} rounded-full transition-all flex-shrink-0 cursor-pointer"
									on:click={() => (chatVisible = !chatVisible)}
								>
									<ChevronRight size={18} class={chatVisible ? 'rotate-0' : 'rotate-180'} />
									<div
										class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none"
									>
										{chatVisible ? $t('theater.live.hideChat') : $t('theater.live.showChat')}
									</div>
								</button>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Sidebar (Chat & Member Info) -->
	{#if chatVisible}
		<div
			class="w-full lg:w-[320px] flex flex-col gap-4 min-h-0 p-1 {isFocusMode
				? 'h-[40%] lg:h-full lg:flex-none'
				: 'flex-1 lg:flex-none'}"
			transition:fly={{ x: 20, duration: 300 }}
		>
			<!-- Chat Window placeholder -->
			<div
				class="bg-white dark:bg-zinc-950 rounded-3xl border border-gray-100 dark:border-zinc-800 overflow-hidden flex flex-col shadow-sm {isFocusMode
					? 'flex-1'
					: 'flex-1 lg:h-full'}"
			>
				<div
					class="p-4 border-b border-gray-100 dark:border-zinc-900 flex items-center justify-between"
				>
					<div class="flex items-center gap-2">
						{#if sidebarMode === 'chat'}
							<h3
								class="font-black text-xs uppercase tracking-widest text-slate-900 dark:text-white flex items-center gap-2"
							>
								<MessageCircle size={14} class="text-red-600" />
								{$t('theater.live.chat')}
							</h3>
						{:else}
							<h3
								class="font-black text-xs uppercase tracking-widest text-slate-900 dark:text-white flex items-center gap-2"
							>
								<Users size={14} class="text-red-600" />
								{$t('theater.subNav.live')}
							</h3>
						{/if}
					</div>

					<div class="flex items-center gap-3">
						{#if sidebarMode === 'chat'}
							<div class="flex items-center gap-2">
								<div class="w-1.5 h-1.5 rounded-full bg-green-500"></div>
								<span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest"
									>{$t('theater.live.connected')}</span
								>
							</div>
						{/if}
					</div>
				</div>

				<!-- Sidebar Content -->
				<div class="flex-1 overflow-hidden flex flex-col">
					{#if sidebarMode === 'chat'}
						{#if platform === 'showroom' && id}
							<ShowroomChat roomId={id} />
						{:else if platform === 'idn' && roomIdentifier}
							<IDNChat {roomIdentifier} />
						{/if}
					{:else}
						<div class="flex-1 overflow-y-auto p-4 space-y-3">
							{#if loadingOtherLive}
								<div class="flex flex-col items-center justify-center h-full gap-3">
									<RefreshCw size={24} class="animate-spin text-slate-200 dark:text-zinc-800" />
									<span class="text-[9px] font-bold text-slate-400 uppercase tracking-widest"
										>Searching matches...</span
									>
								</div>
							{:else if $otherLive.length === 0}
								<div class="flex flex-col items-center justify-center h-full text-center gap-4">
									<div
										class="w-12 h-12 rounded-full bg-slate-50 dark:bg-zinc-900 flex items-center justify-center text-slate-300 dark:text-zinc-700"
									>
										<Users size={24} />
									</div>
									<p class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
										{$t('theater.live.empty')}
									</p>
								</div>
							{:else}
								{#each $otherLive as member}
									<a
										href="/jkt48/live/{member.platform}/{getMemberId(member)}"
										class="flex items-center gap-3 p-2.5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-100 dark:border-zinc-800/50 hover:border-red-500/30 hover:shadow-sm hover:shadow-red-500/5 transition-all group overflow-hidden relative"
									>
										<div class="relative flex-none">
											<div
												class="w-12 aspect-[3/4] rounded-lg overflow-hidden border border-slate-100 dark:border-zinc-800 bg-slate-100 dark:bg-zinc-800"
											>
												<img
													src={getExternalMediaUrl(member.member?.img) || fallbackAvatar}
													alt={member.member?.name}
													on:error={(e) => {
														if (e.currentTarget instanceof HTMLImageElement)
															e.currentTarget.src = fallbackAvatar;
													}}
													class="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-500"
												/>
											</div>
											<div class="absolute -top-1 -right-1 flex gap-0.5">
												<div
													class="px-1.5 py-0.5 bg-red-600 rounded-md text-[7px] font-black text-white uppercase tracking-tighter shadow-sm"
												>
													{$t('theater.live.liveBadge')}
												</div>
											</div>
										</div>
										<div class="flex-1 min-w-0">
											<div
												class="text-[10px] font-black text-slate-900 dark:text-white uppercase tracking-wider truncate mb-0.5 group-hover:text-red-600 transition-colors"
											>
												{member.member?.name ||
													(member.platform === 'idn' ? member.room_url_key : member.title)}
											</div>
											<div class="flex items-center gap-1.5">
												<span class="text-[8px] font-black text-slate-400 uppercase tracking-widest"
													>{member.platform?.toUpperCase()}</span
												>
												{#if member.view_num > 0}
													<div class="w-1 h-1 rounded-full bg-slate-200 dark:bg-zinc-800"></div>
													<span
														class="text-[8px] font-bold text-slate-400 uppercase tracking-widest flex items-center gap-1"
													>
														<div class="w-1 h-1 rounded-full bg-red-500"></div>
														{member.view_num?.toLocaleString()}
													</span>
												{/if}
											</div>
										</div>
										<div
											class="flex-none opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all"
										>
											<ChevronRight size={14} class="text-red-500" />
										</div>
									</a>
								{/each}
							{/if}
						</div>
					{/if}
				</div>

				<!-- Chat Input Area removed for read-only -->
			</div>
		</div>
	{/if}
</div>

<style>
	/* Hide scrollbar but keep functionality */
	.overflow-y-auto {
		scrollbar-width: thin;
		scrollbar-color: rgba(0, 0, 0, 0.1) transparent;
	}

	:global(.dark) .overflow-y-auto {
		scrollbar-color: rgba(255, 255, 255, 0.1) transparent;
	}

	:global(input[type='range']::-webkit-slider-thumb) {
		appearance: none;
		width: 14px;
		height: 14px;
		background: white;
		border-radius: 50%;
		cursor: pointer;
		box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
		border: 2px solid #ef4444; /* Match red theme */
	}

	:global(input[type='range']::-moz-range-thumb) {
		width: 14px;
		height: 14px;
		background: white;
		border-radius: 50%;
		cursor: pointer;
		box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
		border: 2px solid #ef4444;
	}

	/* Adjust volume slider thumb slightly smaller */
	:global(.group\/volume input[type='range']::-webkit-slider-thumb) {
		width: 12px;
		height: 12px;
		border: none;
	}

	:global(.group\/volume input[type='range']::-moz-range-thumb) {
		width: 12px;
		height: 12px;
		border: none;
	}
</style>
