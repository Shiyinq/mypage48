<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { liveStore, liveList, currentStream, otherLive, liveLoading } from '$lib/stores/live';
	import { showToast } from '$lib/stores/toast';
	import { isImmersive } from '$lib/stores/ui';
	import { API_BASE } from '$lib/apis/client';
	import type { LiveStatus } from '$lib/types';
	import IDNChat from '$lib/components/live/IDNChat.svelte';
	import ShowroomChat from '$lib/components/live/ShowroomChat.svelte';
	import GiftOverlay from '$lib/components/live/GiftOverlay.svelte';
	import { theme, setTheme } from '$lib/stores/theme';
	import {
		ArrowLeft,
		Users,
		MessageCircle,
		Info,
		ChevronRight,
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
		RotateCw,
		Tv,
		ExternalLink
	} from 'lucide-svelte';
	import { fade, fly } from 'svelte/transition';
	import {
		getExternalMediaUrl,
		captureVideoScreenshot,
		startVideoRecording,
		downloadRecording
	} from '$lib/utils/media';
	import PlatformLogo from '$lib/components/live/PlatformLogo.svelte';
	import LiveStats from '$lib/components/live/LiveStats.svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';

	interface Props {
		/** Base path determines back-links and other-live member hrefs.
		 *  Use '/jkt48/live' for public pages, '/theater/live' for theater pages. */
		basePath?: string;
	}

	let { basePath = '/jkt48/live' }: Props = $props();

	/** Placeholder header for mobile sync - only for theater mode */
	const { t } = useTranslation();

	let videoElement: HTMLVideoElement | undefined = $state();
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	let hls: any;
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	let Hls: any;
	let loadingOtherLive = $state(false);
	let initializing = $state(false);
	let lastInitializedId = $state('');
	let initCount = 0;
	let chatVisible = $state(true);
	let isFocusMode = $state(false); // Will be set in onMount for desktop/laptop
	let isRecording = $state(false);
	let mediaRecorder: MediaRecorder | null = null;
	let recordedChunks: Blob[] = [];
	let sidebarMode: 'chat' | 'list' = $state('chat');
	let volume = $state(1);
	let isMuted = $state(false);
	let currentTime = $state(0);
	let duration = $state(0);
	let isPaused = $state(true);

	let peakDuration = $state(0);
	let isFullscreen = $state(false);
	let showControls = $state(true);
	let controlsTimeout: ReturnType<typeof setTimeout> | undefined = $state();
	let playerContainer: HTMLDivElement | undefined = $state();
	let recordingDuration = $state(0);
	let recordingTimer: ReturnType<typeof setInterval> | null = null;
	let refreshInterval: ReturnType<typeof setInterval> | null = null;
	let ignoreNextVideoClick = $state(false);
	let rotation = $state(0);
	// let videoWidth = $state(0);
	// let videoHeight = $state(0);
	let playerWidth = $state(0);
	let playerHeight = $state(0);
	let isBuffering = $state(false);
	let autoplayBlocked = $state(false);

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

	function getMemberId(
		m: LiveStatus | { platform?: string; room_id?: string; room_url_key?: string; live_id?: string }
	) {
		if (m.platform === 'showroom') return m.room_id || m.room_url_key;
		return m.live_id || m.room_url_key;
	}

	const fallbackAvatar = 'https://placehold.co/640x960?text=NO%20IMAGE';

	async function initPlayer() {
		if (typeof window === 'undefined') return;
		if (!Hls) {
			const mod = await import('hls.js');
			Hls = mod.default;
		}
		const currentInit = ++initCount;
		try {
			initializing = true;
			const p = platform as string;
			const i = id as string;
			if (!p || !i) throw new Error('Missing params');

			await liveStore.loadStream(p, i);

			if (currentInit !== initCount) return;

			const current = $currentStream;
			if (current && current.streaming_urls && current.streaming_urls.length > 0) {
				const rawUrl = current.streaming_urls[0]?.url;
				if (!rawUrl) return;

				let streamUrl: string = rawUrl;

				// Use proxy for IDN or Showroom to bypass CORS
				if (p === 'idn' || p === 'showroom') {
					streamUrl = `${API_BASE}/jkt48/live/proxy?url=${encodeURIComponent(streamUrl as string)}`;
				}

				if (typeof window !== 'undefined' && videoElement) {
					if (Hls.isSupported()) {
						if (hls) hls.destroy();
						hls = new Hls();
						hls.loadSource(streamUrl);
						hls.attachMedia(videoElement);
						hls.on(Hls.Events.MANIFEST_PARSED, () => {
							videoElement?.play().catch((e: Error) => {
								if (e.name === 'NotAllowedError') {
									autoplayBlocked = true;
									isPaused = true;
								}
							});
							resetControlsTimeout();
						});

						hls.on(
							Hls.Events.ERROR,
							(event: unknown, data: { type: string; response?: { code: number } }) => {
								if (data.type === Hls.ErrorTypes.NETWORK_ERROR && data.response?.code === 404) {
									console.log('Proxy/Stream 404 detected, redirecting to list');
									showToast($t('theater.live.offline'), 'error');
									goto(basePath);
								}
							}
						);
					} else if (videoElement.canPlayType('application/vnd.apple.mpegurl')) {
						videoElement.src = streamUrl;
						videoElement.addEventListener('loadedmetadata', () => {
							videoElement?.play().catch((e: Error) => {
								if (e.name === 'NotAllowedError') {
									autoplayBlocked = true;
									isPaused = true;
								}
							});
							resetControlsTimeout();
						});
					}
				}
			}
		} catch (e: unknown) {
			console.error('Player init failed:', e);
			if (currentInit !== initCount) return;

			if ((e as { status?: number })?.status === 404) {
				showToast($t('theater.live.offline'), 'error');
				goto(basePath);
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
		const isLaptop = window.innerWidth >= 1024;
		if (isLaptop) {
			isFocusMode = true;
			isImmersive.set(true);
			if (typeof document !== 'undefined') {
				document.body.style.overflow = 'hidden';
			}
		} else {
			isFocusMode = false;
			isImmersive.set(false);
			if (typeof document !== 'undefined') {
				document.body.style.overflow = 'auto';
			}
		}

		refreshInterval = setInterval(() => {
			if (platform && id && !initializing) {
				liveStore.refreshStreamInfo(platform, id).catch((e) => {
					if (e?.status === 404) {
						showToast($t('theater.live.offline'), 'error');
						goto(basePath);
					}
				});
				fetchOtherLive();
			}
		}, 30000);

		return () => {
			if (refreshInterval) clearInterval(refreshInterval);
			if (typeof document !== 'undefined') {
				document.body.style.overflow = '';
			}
		};
	});

	onDestroy(() => {
		if (hls) hls.destroy();
		if (recordingTimer) clearInterval(recordingTimer);
		if (refreshInterval) clearInterval(refreshInterval);
		liveStore.reset();
		isImmersive.set(false);
		if (typeof document !== 'undefined') {
			document.body.style.overflow = '';
		}
	});

	function toggleFocus() {
		isFocusMode = !isFocusMode;
		isImmersive.set(isFocusMode);
		if (typeof document !== 'undefined') {
			if (isFocusMode) {
				document.body.style.overflow = 'hidden';
				if (window.innerWidth < 1024) chatVisible = false;
			} else {
				document.body.style.overflow = 'auto';
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
		peakDuration = 0;
		await initPlayer();
	}

	function updateBufferAndDuration() {
		if (videoElement) {
			const buffered = videoElement.buffered;
			if (buffered.length > 0) {
				const furthestBuffer = buffered.end(buffered.length - 1);
				if (furthestBuffer > peakDuration) peakDuration = furthestBuffer;
			}
			const nativeDuration = videoElement.duration;
			if (nativeDuration !== Infinity && !isNaN(nativeDuration)) {
				if (nativeDuration > peakDuration) peakDuration = nativeDuration;
			}
		}
	}

	function takeScreenshot() {
		if (videoElement) captureVideoScreenshot(videoElement, memberName || 'JKT48_Live');
	}

	async function toggleRecording() {
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
				recordingDuration = 0;
				recordingTimer = setInterval(() => {
					recordingDuration++;
				}, 1000);
			}
		} else if (mediaRecorder) {
			mediaRecorder.stop();
			if (recordingTimer) {
				clearInterval(recordingTimer);
				recordingTimer = null;
			}
		}
	}

	function toggleMute() {
		isMuted = !isMuted;
		if (videoElement) videoElement.muted = isMuted;
	}

	function toggleTheme() {
		setTheme($theme === 'dark' ? 'light' : 'dark');
	}

	function handleVolumeChange(e: Event) {
		const target = e.target as HTMLInputElement;
		volume = parseFloat(target.value);
		if (videoElement) {
			videoElement.volume = volume;
			if (volume > 0) isMuted = false;
		}
	}

	async function togglePiP() {
		try {
			if ((document as Document & { pictureInPictureElement?: Element }).pictureInPictureElement) {
				await (
					document as Document & { exitPictureInPicture: () => Promise<void> }
				).exitPictureInPicture();
			} else if (videoElement) {
				await (
					videoElement as HTMLVideoElement & { requestPictureInPicture: () => Promise<void> }
				).requestPictureInPicture();
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

	function handleSeek(e: Event) {
		if (videoElement) {
			const target = e.target as HTMLInputElement;
			videoElement.currentTime = parseFloat(target.value);
		}
	}

	function togglePlayPause() {
		if (videoElement) {
			if (videoElement.paused) {
				videoElement.play().catch((e) => {
					if (e.name === 'NotAllowedError') {
						autoplayBlocked = true;
						isPaused = true;
					}
				});
			} else {
				videoElement.pause();
			}
		}
	}

	function retryPlayback() {
		autoplayBlocked = false;
		if (videoElement) {
			videoElement.play().catch((e) => {
				if (e.name === 'NotAllowedError') {
					autoplayBlocked = true;
					isPaused = true;
				}
			});
		}
	}

	function formatTime(seconds: number) {
		if (isNaN(seconds) || seconds === Infinity) return '00:00';
		const h = Math.floor(seconds / 3600);
		const m = Math.floor((seconds % 3600) / 60);
		const s = Math.floor(seconds % 60);
		if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
		return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
	}
	let isTheater = $derived(basePath.startsWith('/theater'));
	let { platform, id } = $derived($page.params);

	let streamFromList = $derived(
		$liveList.find(
			(s) =>
				s.platform === platform && (s.room_id === id || s.live_id === id || s.room_url_key === id)
		)
	);
	let streamTitle = $derived(streamFromList?.title || '');
	let originalLiveUrl = $derived(
		platform === 'idn'
			? `https://www.idn.app/${streamFromList?.room_url_key?.replace('@', '') || ''}/live/${streamFromList?.live_id || ''}`
			: platform === 'showroom'
				? `https://www.showroom-live.com/r/${streamFromList?.room_url_key || ''}`
				: '#'
	);
	$effect(() => {
		if (currentTime > peakDuration) peakDuration = currentTime;
	});
	$effect(() => {
		if (duration > 0 && duration !== Infinity && duration > peakDuration) peakDuration = duration;
	});
	let displayDuration = $derived(peakDuration || currentTime);

	let memberName = $derived($currentStream?.member?.name || null);
	let roomIdentifier = $derived($currentStream?.room_identifier || null);

	let startAt = $derived($currentStream?.start_at || null);
	$effect(() => {
		if (platform && id && lastInitializedId !== `${platform}-${id}`) {
			lastInitializedId = `${platform}-${id}`;
			initPlayer();
			fetchOtherLive();
		}
	});
</script>

<svelte:head>
	<title>Live Streaming | MyPage48</title>
</svelte:head>

<div
	class="flex flex-col lg:flex-row gap-4 transition-all duration-500 ease-in-out overflow-x-hidden {isFocusMode
		? 'fixed inset-0 !top-0 !mt-0 z-[7000] bg-white dark:bg-zinc-950 p-2 sm:p-4 h-screen w-screen'
		: 'h-[calc(100vh-72px)] sm:h-[calc(100vh-76px)] mt-2 sm:mt-3 px-0 sm:px-4 pb-2 sm:pb-4'}"
>
	<!-- Main Player Area -->
	<div class="flex-[1.5] lg:flex-1 flex flex-col gap-3 min-h-0 p-0">
		{#if isTheater}
			<PageHeader
				title={memberName || 'JKT48 LIVE'}
				subtitle={streamTitle}
				icon={Tv}
				theme="red"
				showBackButton={true}
				backUrl={basePath}
				hidden={true}
			/>
		{/if}

		<!-- Back Button & Info -->
		<div
			class="{isTheater ? 'hidden sm:flex' : 'flex'} items-center justify-between {isTheater
				? ''
				: 'px-4 sm:px-0'}"
		>
			<div class="flex items-center gap-3">
				<a
					href={basePath}
					class="flex items-center justify-center w-8 h-8 text-slate-500 dark:text-slate-400 hover:text-red-600 transition-colors rounded-full hover:bg-slate-100 dark:hover:bg-zinc-800 cursor-pointer"
					title={$t('theater.live.back')}
				>
					<ArrowLeft size={20} />
				</a>
				<div class="h-4 w-px bg-slate-200 dark:bg-zinc-800 ml-1 hidden sm:block"></div>
				{#if memberName}
					<div class="flex flex-col gap-0.5">
						<div class="flex flex-col sm:flex-row items-baseline gap-1 sm:gap-2">
							<span
								class="text-xs font-black uppercase tracking-[0.15em] text-slate-900 dark:text-white leading-none truncate max-w-[200px] sm:max-w-none"
								>{memberName}</span
							>
							<span
								class="text-[9px] font-bold text-slate-400 tracking-widest leading-none hidden sm:inline"
								>{streamTitle}</span
							>
						</div>
					</div>
				{/if}
			</div>

			{#if !isFullscreen}
				<div class="hidden sm:flex items-center gap-3 flex-shrink-0">
					<LiveStats view_num={$currentStream?.view_num} start_at={startAt} variant="detailed" />
					<a
						href={originalLiveUrl}
						target="_blank"
						rel="noopener noreferrer"
						class="group/platform flex items-center gap-1.5 hover:scale-110 active:scale-95 transition-transform"
						title={$t('theater.live.openOriginal')}
					>
						<PlatformLogo platform={platform || ''} size="md" />
						<div
							class="w-0 overflow-hidden opacity-0 group-hover/platform:w-4 group-hover/platform:opacity-100 transition-all duration-300"
						>
							<ExternalLink size={14} class="text-slate-400" />
						</div>
					</a>
				</div>
			{/if}
		</div>

		<!-- Video Player -->
		<div
			class="relative flex-1 bg-black rounded-xl sm:rounded-3xl overflow-hidden border border-gray-100 dark:border-zinc-800 shadow-sm"
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
						class="w-32 h-44 sm:w-40 sm:h-56 rounded-2xl overflow-hidden border-2 border-white/10 shadow-2xl mb-2 relative group"
					>
						<img
							src={getExternalMediaUrl(
								(platform === 'showroom'
									? streamFromList?.member?.img || streamFromList?.image
									: streamFromList?.image || streamFromList?.member?.img) || ''
							) || fallbackAvatar}
							alt={streamFromList?.member?.name}
							class="w-full h-full object-cover opacity-50 grayscale group-hover:grayscale-0 group-hover:opacity-100 transition-all duration-700"
						/>
						<div class="absolute inset-0 bg-zinc-950/40 flex items-center justify-center">
							<Info size={32} class="text-white/20" />
						</div>
					</div>
					<div>
						<h2 class="text-2xl font-black mb-2 uppercase tracking-tighter">Stream Offline</h2>
						<p class="text-zinc-500 max-w-sm mx-auto text-xs sm:text-sm px-4">
							{streamFromList?.member?.name || 'Member'} is not live at the moment. This session might
							have ended or is currently unavailable.
						</p>
					</div>
					<a
						href={basePath}
						class="px-8 py-3 rounded-2xl bg-white text-zinc-950 font-black uppercase tracking-widest text-xs hover:bg-red-600 hover:text-white transition-all"
					>
						Return Home
					</a>
				</div>
			{/if}

			<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
			<!-- svelte-ignore a11y_click_events_have_key_events -->
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
				onfullscreenchange={handleFullscreenChange}
				onmousemove={() => resetControlsTimeout(false)}
				onmouseleave={() => {
					showControls = false;
					clearTimeout(controlsTimeout);
				}}
				onclick={() => resetControlsTimeout(false)}
				ontouchstart={() => resetControlsTimeout(true)}
			>
				<!-- Top Info Overlay -->
				<div
					class="dark absolute inset-x-0 top-0 p-6 bg-gradient-to-b from-black/90 via-black/40 to-transparent transition-all duration-500 pointer-events-none z-[5500] {showControls
						? 'translate-y-0 opacity-100'
						: isFullscreen || isFocusMode
							? '-translate-y-full opacity-0'
							: 'opacity-0 -translate-y-full group-hover/player:translate-y-0 group-hover/player:opacity-100'}"
				>
					<div class="w-full flex items-start gap-4 pointer-events-auto">
						<div class="flex flex-col gap-2 min-w-0 flex-1">
							{#if isFullscreen && memberName}
								<div class="flex items-center gap-3 min-w-0">
									<div class="flex flex-col sm:flex-row items-baseline gap-1 sm:gap-2 min-w-0">
										<h2
											class="text-white text-lg sm:text-2xl font-black truncate drop-shadow-xl tracking-tight"
										>
											{memberName}
										</h2>
										{#if streamTitle}
											<span
												class="text-white/60 text-[10px] sm:text-xs font-bold tracking-widest truncate drop-shadow-lg hidden sm:inline"
											>
												{streamTitle}
											</span>
										{/if}
									</div>
								</div>
							{/if}

							<!-- Stats (Mobile Only) -->
							<div class="flex sm:hidden items-center gap-3 flex-shrink-0 mt-0.5">
								<LiveStats
									view_num={$currentStream?.view_num}
									start_at={startAt}
									variant="detailed"
								/>
								<a
									href={originalLiveUrl}
									target="_blank"
									rel="noopener noreferrer"
									class="group/platform flex items-center gap-1.5 hover:scale-110 active:scale-95 transition-transform"
								>
									<PlatformLogo platform={platform || ''} size="md" />
									<div
										class="w-0 overflow-hidden opacity-0 group-hover/platform:w-4 group-hover/platform:opacity-100 transition-all duration-300"
									>
										<ExternalLink size={14} class="text-white/60" />
									</div>
								</a>
							</div>
						</div>

						<!-- Stats (Desktop Fullscreen Only) -->
						{#if isFullscreen}
							<div class="hidden sm:flex items-center gap-3 flex-shrink-0 mt-1">
								<LiveStats
									view_num={$currentStream?.view_num}
									start_at={startAt}
									variant="detailed"
								/>
								<a
									href={originalLiveUrl}
									target="_blank"
									rel="noopener noreferrer"
									class="group/platform flex items-center gap-1.5 hover:scale-110 active:scale-95 transition-transform"
								>
									<PlatformLogo platform={platform || ''} size="md" />
									<div
										class="w-0 overflow-hidden opacity-0 group-hover/platform:w-4 group-hover/platform:opacity-100 transition-all duration-300"
									>
										<ExternalLink size={14} class="text-white/60" />
									</div>
								</a>
							</div>
						{/if}
					</div>
				</div>

				<video
					bind:this={videoElement}
					class="relative z-10 w-full h-full object-contain cursor-pointer bg-transparent transition-transform duration-300"
					style="transform: rotate({rotation}deg);"
					crossorigin="anonymous"
					autoplay
					playsinline
					ontimeupdate={() => {
						currentTime = videoElement?.currentTime || 0;
						updateBufferAndDuration();
					}}
					onloadedmetadata={() => {
						duration = videoElement?.duration || 0;
						// videoWidth = videoElement?.videoWidth || 0;
						// videoHeight = videoElement?.videoHeight || 0;
						updateBufferAndDuration();
					}}
					onplay={() => (isPaused = false)}
					onpause={() => {
						isPaused = true;
						isBuffering = false;
					}}
					onclick={() => {
						if (ignoreNextVideoClick) {
							ignoreNextVideoClick = false;
							return;
						}
						togglePlayPause();
					}}
					onwaiting={() => (isBuffering = true)}
					onplaying={() => (isBuffering = false)}
					onstalled={() => (isBuffering = true)}
					oncanplay={() => (isBuffering = false)}
				></video>

				{#if autoplayBlocked}
					<button
						class="absolute inset-0 flex flex-col items-center justify-center bg-zinc-950/80 backdrop-blur-sm z-30 group/autoplay cursor-pointer"
						onclick={(e) => {
							e.stopPropagation();
							retryPlayback();
						}}
					>
						<div
							class="w-20 h-20 rounded-full bg-white/10 flex items-center justify-center border-2 border-white/20 group-hover/autoplay:scale-110 group-hover/autoplay:bg-white/20 transition-all duration-300"
						>
							<Play size={40} class="text-white ml-2" fill="white" />
						</div>
						<div class="mt-6 text-center">
							<h3 class="text-white font-black text-lg uppercase tracking-[0.2em] mb-1">
								{$t('theater.live.tap_to_play')}
							</h3>
							<p class="text-white/40 text-[10px] font-bold uppercase tracking-widest">
								{$t('theater.live.autoplay_description')}
							</p>
						</div>
					</button>
				{:else if isBuffering && !initializing}
					<div
						class="absolute inset-0 flex items-center justify-center bg-black/20 backdrop-blur-[1px] z-25 pointer-events-none"
						transition:fade
					>
						<div class="flex flex-col items-center gap-3">
							<div
								class="w-12 h-12 border-4 border-white/20 border-t-white rounded-full animate-spin"
							></div>
						</div>
					</div>
				{/if}

				{#if roomIdentifier}
					<GiftOverlay {roomIdentifier} />
				{/if}

				<!-- Custom Player Controls Overlay -->
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
								<div
									class="absolute inset-x-0 h-1 bg-white/20 rounded-full pointer-events-none"
								></div>
								<div
									class="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-red-600 rounded-full pointer-events-none transition-all z-10"
									style="width: {Math.min(100, (currentTime / (displayDuration || 1)) * 100)}%"
								></div>
								<input
									type="range"
									min="0"
									max={displayDuration || 0}
									step="0.1"
									value={currentTime}
									oninput={handleSeek}
									class="absolute inset-x-0 w-full h-full bg-transparent appearance-none cursor-pointer z-20 custom-range"
								/>
							</div>
						</div>

						<!-- Controls Bar -->
						<div
							class="flex items-center justify-between gap-2 sm:gap-4 overflow-x-auto scrollbar-hide py-1"
						>
							<!-- Left: Play, Volume, PiP -->
							<div class="flex items-center gap-1 sm:gap-2 flex-shrink-0">
								<button
									class="w-10 h-10 flex items-center justify-center text-white hover:bg-white/10 rounded-full transition-all flex-shrink-0 cursor-pointer group/btn relative"
									onclick={togglePlayPause}
								>
									{#if isPaused}<Play size={22} fill="currentColor" class="ml-1" />{:else}<Pause
											size={22}
											fill="currentColor"
										/>{/if}
									<div
										class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none"
									>
										{isPaused ? $t('theater.live.play') : $t('theater.live.pause')}
									</div>
								</button>

								<div class="flex items-center gap-1 group/volume">
									<button
										class="group/btn relative w-10 h-10 flex items-center justify-center text-white hover:bg-white/10 rounded-full transition-all flex-shrink-0 cursor-pointer"
										onclick={toggleMute}
									>
										{#if isMuted || volume === 0}<VolumeX size={18} />{:else}<Volume2
												size={18}
											/>{/if}
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
										oninput={handleVolumeChange}
										class="w-0 opacity-0 group-hover/volume:w-16 sm:group-hover/volume:w-24 group-hover/volume:opacity-100 transition-all duration-300 h-1 bg-white/30 rounded-full appearance-none cursor-pointer accent-white"
									/>
								</div>

								<button
									class="group/btn relative w-10 h-10 flex items-center justify-center text-white hover:bg-white/10 rounded-full transition-all flex-shrink-0 cursor-pointer"
									onclick={togglePiP}
								>
									<PictureInPicture2 size={18} />
									<div
										class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none"
									>
										{$t('theater.live.pip')}
									</div>
								</button>
							</div>

							<!-- Right: Screenshot, Record, Theme, Focus, Fullscreen, Refresh, Rotate, Sidebar, Chat -->
							<div class="flex items-center gap-1 sm:gap-2 flex-shrink-0">
								<button
									class="group/btn relative w-10 h-10 flex items-center justify-center hover:bg-white/10 text-white rounded-full transition-all flex-shrink-0 cursor-pointer"
									onclick={takeScreenshot}
								>
									<Camera size={18} />
									<div
										class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none"
									>
										{$t('theater.live.screenshot')}
									</div>
								</button>

								<div class="flex items-center gap-1.5 min-w-[40px] transition-all duration-300">
									<button
										class="group/btn relative w-10 h-10 flex items-center justify-center {isRecording
											? 'bg-red-600 animate-pulse'
											: 'bg-white/10 hover:bg-white/20'} text-white rounded-full transition-all flex-shrink-0 active:scale-95 cursor-pointer"
										onclick={toggleRecording}
									>
										{#if isRecording}<Square size={16} fill="white" />{:else}<Circle
												size={16}
												fill="white"
												class="text-white"
											/>{/if}
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
										onclick={toggleTheme}
									>
										{#if $theme === 'dark'}<Moon size={18} />{:else}<Sun size={18} />{/if}
										<div
											class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none uppercase tracking-widest"
										>
											{$t('theater.live.toggleTheme')}
										</div>
									</button>
								{/if}

								<button
									class="group/btn relative w-10 h-10 flex items-center justify-center {isFocusMode
										? 'bg-white text-black'
										: 'hover:bg-white/10 text-white'} rounded-full transition-all flex-shrink-0 cursor-pointer"
									onclick={toggleFocus}
								>
									{#if isFocusMode}<Minimize2 size={18} />{:else}<Maximize2 size={18} />{/if}
									<div
										class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none uppercase tracking-widest"
									>
										{isFocusMode ? $t('theater.live.exitFocus') : $t('theater.live.focusMode')}
									</div>
								</button>

								<button
									class="group/btn relative w-10 h-10 flex items-center justify-center {isFullscreen
										? 'bg-white text-black'
										: 'hover:bg-white/10 text-white'} rounded-full transition-all flex-shrink-0 cursor-pointer"
									onclick={toggleFullscreen}
								>
									{#if isFullscreen}<Minimize size={18} />{:else}<Maximize size={18} />{/if}
									<div
										class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none uppercase tracking-widest"
									>
										{isFullscreen
											? $t('theater.live.exitFullscreen')
											: $t('theater.live.fullscreen')}
									</div>
								</button>

								<button
									class="group/btn relative w-10 h-10 flex items-center justify-center hover:bg-white/10 text-white rounded-full transition-all flex-shrink-0 cursor-pointer"
									onclick={refreshStream}
								>
									<RefreshCw size={18} class={$liveLoading ? 'animate-spin' : ''} />
									<div
										class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none"
									>
										{$t('theater.live.refresh')}
									</div>
								</button>

								<button
									class="group/btn relative w-10 h-10 flex items-center justify-center hover:bg-white/10 text-white rounded-full transition-all flex-shrink-0 cursor-pointer"
									onclick={rotateVideo}
								>
									<RotateCw size={18} class="transition-transform duration-500" />
									<div
										class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none uppercase tracking-widest"
									>
										{$t('theater.live.rotate')}
									</div>
								</button>

								<div class="w-px h-4 bg-white/20 mx-1"></div>

								<button
									class="group/btn relative w-10 h-10 flex items-center justify-center {sidebarMode ===
									'list'
										? 'bg-white text-black'
										: 'hover:bg-white/10 text-white'} rounded-full transition-all flex-shrink-0 cursor-pointer"
									onclick={() => {
										sidebarMode = sidebarMode === 'chat' ? 'list' : 'chat';
										if (sidebarMode === 'list') fetchOtherLive();
										if (!chatVisible) chatVisible = true;
									}}
								>
									{#if sidebarMode === 'chat'}<Users size={18} />{:else}<MessageCircle
											size={18}
										/>{/if}
									<div
										class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none"
									>
										{sidebarMode === 'chat'
											? $t('theater.subNav.members')
											: $t('theater.live.chat')}
									</div>
								</button>

								<button
									class="group/btn relative w-10 h-10 flex items-center justify-center {chatVisible
										? 'hover:bg-white/10 text-white'
										: 'bg-white text-black'} rounded-full transition-all flex-shrink-0 cursor-pointer"
									onclick={() => (chatVisible = !chatVisible)}
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

	<!-- Sidebar (Chat & Other Live) -->
	{#if chatVisible}
		<div
			class="w-full lg:w-[320px] flex flex-col gap-4 min-h-0 p-1 {isFocusMode
				? 'h-[40%] lg:h-full lg:flex-none'
				: 'flex-1 lg:flex-none'}"
			transition:fly={{ x: 20, duration: 300 }}
		>
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
										href="{basePath}/{member.platform}/{getMemberId(member)}"
										class="flex items-center gap-3 p-2.5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-100 dark:border-zinc-800/50 hover:border-red-500/30 hover:shadow-sm hover:shadow-red-500/5 transition-all group overflow-hidden relative"
									>
										<div class="relative flex-none">
											<div
												class="w-12 aspect-[3/4] rounded-lg overflow-hidden border border-slate-100 dark:border-zinc-800 bg-slate-100 dark:bg-zinc-800"
											>
												<img
													src={getExternalMediaUrl(member.member?.img) || fallbackAvatar}
													alt={member.member?.name}
													onerror={(e) => {
														if (e.currentTarget instanceof HTMLImageElement)
															e.currentTarget.src = fallbackAvatar;
													}}
													class="w-full h-full object-cover grayscale group-hover:grayscale-0 transition-all duration-500"
												/>
											</div>
											<div class="absolute -top-1 -right-1">
												<PlatformLogo platform={member.platform || ''} size="xs" />
											</div>
										</div>
										<div class="flex-1 min-w-0">
											<div
												class="text-[10px] font-black text-slate-900 dark:text-white uppercase tracking-wider truncate mb-0.5 group-hover:text-red-600 transition-colors"
											>
												{member.member?.name ||
													(member.platform === 'idn' ? member.room_url_key : member.title)}
											</div>
											<LiveStats view_num={member.view_num} variant="compact" className="mt-0.5" />
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
			</div>
		</div>
	{/if}
</div>

<style>
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
		border: 2px solid #ef4444;
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
