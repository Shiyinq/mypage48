<script lang="ts">
	import { page } from '$app/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { replayStore } from '$lib/stores/replay.svelte';
	import { isImmersive, theme, setTheme } from '$lib/stores';
	import ReplayChat from './ReplayChat.svelte';
	import SEO from '$lib/components/SEO.svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import PlatformLogo from '$lib/components/live/PlatformLogo.svelte';
	import type { ReplayVideo } from '$lib/types/replay';
	import {
		ArrowLeft,
		Tv,
		Play,
		Pause,
		Volume2,
		VolumeX,
		Maximize2,
		Minimize2,
		Maximize,
		Minimize,
		PictureInPicture2,
		Camera,
		MessageCircle,
		Sun,
		Moon,
		Calendar,
		ExternalLink
	} from 'lucide-svelte';
	import { fade } from 'svelte/transition';

	const { t } = useTranslation();

	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	let YT: any;
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	let youTubePlayer: any;
	const PlayerState = { PLAYING: 1, BUFFERING: 3 } as const;

	interface Props {
		basePath?: string;
	}

	let { basePath = '/jkt48/live/replay' }: Props = $props();

	let playerContainer: HTMLDivElement | undefined = $state();
	let youTubeReady = $state(false);
	let currentTime = $state(0);
	let duration = $state(0);
	let isPlaying = $state(false);
	let isPaused = $state(true);
	let showControls = $state(true);
	let isFullscreen = $state(false);
	let isFocusMode = $state(true);
	let volume = $state(1);
	let isMuted = $state(false);
	let isSettingsOpen = $state(false);
	let controlsTimeout: ReturnType<typeof setTimeout> | undefined;
	let chatVisible = $state(true);
	let videoContainer: HTMLDivElement | undefined = $state();
	let initAttempted = $state(false);
	let { id } = $derived($page.params);

	let video: ReplayVideo | undefined = $derived(
		replayStore.videos.find((v) => v.youtube_id === id)
	);

	let isTheater = $derived(basePath.startsWith('/theater'));

	$effect(() => {
		isImmersive.set(true);
		document.body.style.overflow = 'hidden';
		return () => {
			isImmersive.set(false);
			document.body.style.overflow = '';
		};
	});

	function loadYTApi() {
		if (typeof window === 'undefined') return;
		YT = (window as unknown as Record<string, unknown>).YT;
		if (YT?.Player) {
			createPlayer();
			return;
		}
		const tag = document.createElement('script');
		tag.src = 'https://www.youtube.com/iframe_api';
		const firstScript = document.getElementsByTagName('script')[0];
		firstScript.parentNode!.insertBefore(tag, firstScript);
		(window as unknown as Record<string, unknown>).onYouTubeIframeAPIReady = () => {
			YT = (window as unknown as Record<string, unknown>).YT;
			createPlayer();
		};
	}

	function createPlayer() {
		if (!playerContainer || !id) return;
		try {
			youTubePlayer = new YT.Player(playerContainer, {
				videoId: id,
				playerVars: {
					autoplay: 1,
					rel: 0,
					modestbranding: 1,
					controls: 0,
					disablekb: 1,
					fs: 0,
					playsinline: 1,
					iv_load_policy: 3
				},
				events: {
					onReady: (event: { target: { getDuration: () => number; playVideo: () => void } }) => {
						youTubePlayer = event.target;
						youTubeReady = true;
						initAttempted = true;
						duration = event.target.getDuration() || 0;
						event.target.playVideo();
					},
					onStateChange: (event: { data: number }) => {
						const state = event.data;
						isPlaying = state === PlayerState.PLAYING;
						isPaused = state !== PlayerState.PLAYING && state !== PlayerState.BUFFERING;
						if (state === PlayerState.PLAYING) {
							duration = youTubePlayer?.getDuration() || duration;
						}
					},
					onError: () => {
						console.error('YouTube player error');
					}
				}
			});
		} catch (e) {
			console.error('Failed to create YouTube player:', e);
		}
	}

	$effect(() => {
		if (id && !initAttempted) {
			if (replayStore.videos.length === 0) {
				replayStore.loadVideos().then(() => loadYTApi());
			} else {
				loadYTApi();
			}
		}
	});

	$effect(() => {
		if (!youTubeReady) return;
		const interval = setInterval(() => {
			try {
				const time = youTubePlayer?.getCurrentTime();
				if (typeof time === 'number') {
					currentTime = time;
				}
			} catch {
				// ignore
			}
		}, 500);
		return () => clearInterval(interval);
	});

	function resetControlsTimeout(_isTouch = false) {
		showControls = true;
		clearTimeout(controlsTimeout);
		controlsTimeout = setTimeout(() => {
			if (!isSettingsOpen) showControls = false;
		}, 5000);
	}

	function togglePlayPause() {
		if (!youTubePlayer) return;
		if (isPlaying) {
			youTubePlayer.pauseVideo();
		} else {
			youTubePlayer.playVideo();
		}
	}

	function handleSeek(e: Event) {
		if (!youTubePlayer) return;
		const target = e.target as HTMLInputElement;
		youTubePlayer.seekTo(parseFloat(target.value), true);
	}

	function toggleMute() {
		if (!youTubePlayer) return;
		isMuted = !isMuted;
		if (isMuted) {
			youTubePlayer.mute();
		} else {
			youTubePlayer.unMute();
		}
	}

	function handleVolumeChange(e: Event) {
		if (!youTubePlayer) return;
		const target = e.target as HTMLInputElement;
		volume = parseFloat(target.value);
		youTubePlayer.setVolume(volume * 100);
		if (volume > 0) isMuted = false;
	}

	function toggleFocus() {
		isFocusMode = !isFocusMode;
		if (typeof document !== 'undefined') {
			if (isFocusMode) {
				document.body.style.overflow = 'hidden';
			} else {
				document.body.style.overflow = 'auto';
			}
		}
	}

	async function toggleFullscreen() {
		if (!videoContainer) return;
		try {
			if (!document.fullscreenElement) {
				await videoContainer.requestFullscreen();
			} else {
				await document.exitFullscreen();
			}
		} catch (err) {
			console.error('Fullscreen toggle failed:', err);
		}
	}

	function handleFullscreenChange() {
		isFullscreen = document.fullscreenElement !== null;
	}

	function toggleTheme() {
		setTheme(theme.value === 'dark' ? 'light' : 'dark');
	}

	function takeScreenshot() {
		const vid = document.querySelector('#replay-youtube-player iframe') as HTMLIFrameElement;
		if (!vid) return;
		const canvas = document.createElement('canvas');
		const ctx = canvas.getContext('2d');
		if (!ctx) return;
		try {
			const img = new Image();
			img.crossOrigin = 'anonymous';
			img.src = `https://img.youtube.com/vi/${id}/maxresdefault.jpg`;
			img.onload = () => {
				canvas.width = img.width;
				canvas.height = img.height;
				ctx.drawImage(img, 0, 0);
				const link = document.createElement('a');
				link.download = `JKT48_Replay_${id}.jpg`;
				link.href = canvas.toDataURL('image/jpeg');
				link.click();
			};
		} catch {
			// fallback: use current video frame - limited by same-origin
		}
	}

	async function togglePiP() {
		const vid = document.querySelector('#replay-youtube-player iframe') as HTMLIFrameElement;
		if (!vid) return;
		try {
			if ((document as Document & { pictureInPictureElement?: Element }).pictureInPictureElement) {
				await (
					document as Document & { exitPictureInPicture: () => Promise<void> }
				).exitPictureInPicture();
			} else {
				// YouTube doesn't support direct PiP from iframe, use a fallback
				const videoEl = document.querySelector('#replay-youtube-player video') as HTMLVideoElement;
				if (videoEl?.requestPictureInPicture) {
					await videoEl.requestPictureInPicture();
				}
			}
		} catch (error) {
			console.error('PiP failed', error);
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

	let displayDuration = $derived(duration || 0);

	const youtubeUrl = $derived(`https://www.youtube.com/watch?v=${id}`);
</script>

<SEO
	title={video ? t('replay.room.seoTitle', { member: video.member }) : t('replay.room.seoTitleFallback')}
	path={$page.url.pathname}
	description={video ? t('replay.room.seoDesc', { member: video.member, title: video.title }) : t('replay.room.seoTitleFallback')}
/>

<div
	class="flex flex-col lg:flex-row gap-4 transition-all duration-500 ease-in-out overflow-x-hidden {isFocusMode
		? 'fixed inset-0 !top-0 !mt-0 z-[7000] bg-white dark:bg-zinc-950 p-2 sm:p-4 h-[100dvh] w-screen'
		: 'isolate overflow-y-auto h-full px-0 sm:px-4 py-0'}"
>
	<div class="flex-[1.5] lg:flex-1 flex flex-col gap-3 min-h-0 p-0">
		{#if isTheater}
			<PageHeader
				title={video?.member || t('replay.room.fallbackTitle')}
				subtitle={video?.title}
				icon={Tv}
				theme="red"
				showBackButton={true}
				backUrl={basePath}
				hidden={true}
			/>
		{/if}

		<div class="flex items-center justify-between {isTheater ? '' : 'px-4 sm:px-0'}">
			<a
				href={basePath}
				class="flex items-center gap-3 hover:opacity-80 transition-opacity cursor-pointer"
				title={t('theater.live.back')}
			>
				<div
					class="flex items-center justify-center w-8 h-8 text-slate-500 dark:text-slate-400 hover:text-red-600 transition-colors rounded-full hover:bg-slate-100 dark:hover:bg-zinc-800"
				>
					<ArrowLeft size={20} />
				</div>
				<div class="h-4 w-px bg-slate-200 dark:bg-zinc-800 ml-1 hidden sm:block"></div>
				{#if video}
					<div class="flex flex-col gap-0.5">
						<div class="flex flex-col sm:flex-row items-baseline gap-1 sm:gap-2">
							<span
								class="text-xs font-black uppercase tracking-[0.15em] text-slate-900 dark:text-white leading-none truncate max-w-[200px] sm:max-w-none hover:text-red-600 transition-colors"
								>{video.member}</span
							>
							<span
								class="text-[9px] font-bold text-slate-400 tracking-widest leading-none hidden sm:inline"
								>{video.title}</span
							>
						</div>
					</div>
				{/if}
			</a>

			{#if !isFullscreen}
				<div class="hidden sm:flex items-center gap-3 flex-shrink-0">
					{#if video}
						<div class="flex items-center gap-2 text-slate-400 text-xs font-bold">
							<Calendar size={12} />
							<span>{video.date}</span>
							<span class="text-slate-600">|</span>
							<PlatformLogo
								platform={video.platform === 'SHOWROOM' ? 'showroom' : 'idn'}
								size="md"
							/>
						</div>
					{/if}
					<a
						href={youtubeUrl}
						target="_blank"
						rel="noopener noreferrer"
						class="group/platform flex items-center gap-1.5 hover:scale-110 active:scale-95 transition-transform"
						title={t('replay.room.openInYoutube')}
					>
						<ExternalLink size={14} class="text-slate-400" />
					</a>
				</div>
			{/if}
		</div>

		<div
			bind:this={videoContainer}
			class="relative flex-1 bg-black rounded-xl sm:rounded-3xl overflow-hidden border border-gray-100 dark:border-zinc-800 shadow-sm"
		>
			{#if !initAttempted}
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
								{t('replay.room.loadingTitle')}
							</div>
							<div class="text-white/40 text-xs font-medium uppercase tracking-widest">
								{t('replay.room.loadingSubtext')}
							</div>
						</div>
					</div>
				</div>
			{:else if !video}
				<div
					class="absolute inset-0 flex flex-col items-center justify-center bg-zinc-950 text-white gap-6 px-6 text-center"
				>
					<div
						class="w-32 h-44 sm:w-40 sm:h-56 rounded-2xl overflow-hidden border-2 border-white/10 shadow-2xl mb-2 relative group"
					>
						<div class="w-full h-full bg-zinc-800 animate-pulse rounded-2xl"></div>
					</div>
					<div>
						<h2 class="text-2xl font-black mb-2 uppercase tracking-tighter">
							{t('replay.room.videoNotFound')}
						</h2>
						<p class="text-zinc-500 max-w-sm mx-auto text-xs sm:text-sm px-4">
							{t('replay.room.videoNotFoundDesc')}
						</p>
					</div>
					<a
						href={basePath}
						class="px-8 py-3 rounded-2xl bg-white text-zinc-950 font-black uppercase tracking-widest text-xs hover:bg-red-600 hover:text-white transition-all"
					>
						{t('replay.room.back')}
					</a>
				</div>
			{/if}

			<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
			<div
				bind:this={playerContainer}
				id="replay-youtube-player"
				class="relative w-full h-full flex items-center justify-center bg-black"
				class:cursor-none={isFocusMode && !showControls}
				role="region"
				aria-label={t('replay.room.playerLabel')}
				onfullscreenchange={handleFullscreenChange}
				onmousemove={() => resetControlsTimeout(false)}
				onmouseleave={() => {
					if (!isSettingsOpen) {
						showControls = false;
						clearTimeout(controlsTimeout);
					}
				}}
				onclick={() => resetControlsTimeout(false)}
				onkeydown={() => resetControlsTimeout(false)}
			>
				{#if youTubeReady && video}
					<div
						class="dark absolute inset-x-0 top-0 p-6 bg-gradient-to-b from-black/90 via-black/40 to-transparent transition-all duration-500 pointer-events-none z-[5500] {showControls
							? 'translate-y-0 opacity-100'
							: isFullscreen || isFocusMode
								? '-translate-y-full opacity-0'
								: 'opacity-0 -translate-y-full group-hover/player:translate-y-0 group-hover/player:opacity-100'}"
					>
						<div class="w-full flex items-start gap-4 pointer-events-auto">
							<div class="flex flex-col gap-2 min-w-0 flex-1">
								{#if video}
									<div class="flex items-center gap-3 min-w-0">
										<div class="flex flex-col sm:flex-row items-baseline gap-1 sm:gap-2 min-w-0">
											<h2
												class="text-white text-lg sm:text-2xl font-black truncate drop-shadow-xl tracking-tight"
											>
												{video.member}
											</h2>
											<span
												class="text-white/60 text-[10px] sm:text-xs font-bold tracking-widest truncate drop-shadow-lg hidden sm:inline"
											>
												{video.title}
											</span>
										</div>
									</div>
								{/if}
								<div class="flex sm:hidden items-center gap-3 flex-shrink-0 mt-0.5">
									{#if video}
										<div class="flex items-center gap-2 text-white/60 text-[10px] font-bold">
											<Calendar size={12} />
											<span>{video.date}</span>
										</div>
									{/if}
									<a
										href={youtubeUrl}
										target="_blank"
										rel="noopener noreferrer"
										class="group/platform flex items-center gap-1.5 hover:scale-110 active:scale-95 transition-transform"
									>
										<ExternalLink size={14} class="text-white/60" />
									</a>
								</div>
							</div>

							{#if isFullscreen}
								<div class="hidden sm:flex items-center gap-3 flex-shrink-0 mt-1">
									{#if video}
										<div class="flex items-center gap-2 text-white/60 text-xs font-bold">
											<Calendar size={14} />
											<span>{video.date}</span>
											<span class="text-white/30">|</span>
											<PlatformLogo
												platform={video.platform === 'SHOWROOM' ? 'showroom' : 'idn'}
												size="md"
											/>
										</div>
									{/if}
								</div>
							{/if}
						</div>
					</div>
				{/if}

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

						<div
							class="flex items-center justify-between gap-2 sm:gap-4 overflow-x-auto scrollbar-hide py-1"
						>
							<div class="flex items-center gap-1 sm:gap-2 flex-shrink-0">
								<button
									class="w-10 h-10 flex items-center justify-center text-white hover:bg-white/10 rounded-full transition-all flex-shrink-0 cursor-pointer group/btn relative"
									onclick={togglePlayPause}
								>
									{#if isPaused}
										<Play size={22} fill="currentColor" class="ml-1" />
									{:else}
										<Pause size={22} fill="currentColor" />
									{/if}
									<div
										class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none"
									>
										{isPaused ? t('replay.room.play') : t('replay.room.pause')}
									</div>
								</button>

								<div class="flex items-center gap-1 group/volume">
									<button
										class="group/btn relative w-10 h-10 flex items-center justify-center text-white hover:bg-white/10 rounded-full transition-all flex-shrink-0 cursor-pointer"
										onclick={toggleMute}
									>
										{#if isMuted || volume === 0}
											<VolumeX size={18} />
										{:else}
											<Volume2 size={18} />
										{/if}
										<div
											class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none uppercase tracking-widest"
										>
											{isMuted ? t('replay.room.unmute') : t('replay.room.mute')}
										</div>
									</button>
									<input
										type="range"
										min="0"
										max="1"
										step="0.01"
										bind:value={volume}
										oninput={handleVolumeChange}
										class="hidden md:block w-0 opacity-0 group-hover/volume:w-16 sm:group-hover/volume:w-24 group-hover/volume:opacity-100 transition-all duration-300 h-1 bg-white/30 rounded-full appearance-none cursor-pointer accent-white"
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
										{t('replay.room.pip')}
									</div>
								</button>
							</div>

							<div class="flex items-center gap-1 sm:gap-2 flex-shrink-0">
								<button
									class="group/btn relative w-10 h-10 flex items-center justify-center hover:bg-white/10 text-white rounded-full transition-all flex-shrink-0 cursor-pointer"
									onclick={takeScreenshot}
								>
									<Camera size={18} />
									<div
										class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none"
									>
										{t('replay.room.screenshot')}
									</div>
								</button>

								<div class="w-px h-4 bg-white/20 mx-1"></div>

								{#if isFocusMode}
									<button
										class="group/btn relative w-10 h-10 flex items-center justify-center hover:bg-white/10 text-white rounded-full transition-all flex-shrink-0 cursor-pointer"
										onclick={toggleTheme}
									>
										{#if theme.value === 'dark'}
											<Moon size={18} />
										{:else}
											<Sun size={18} />
										{/if}
										<div
											class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none uppercase tracking-widest"
										>
											{t('replay.room.theme')}
										</div>
									</button>
								{/if}

								<button
									class="group/btn relative w-10 h-10 flex items-center justify-center {isFocusMode
										? 'bg-white text-black'
										: 'hover:bg-white/10 text-white'} rounded-full transition-all flex-shrink-0 cursor-pointer"
									onclick={toggleFocus}
								>
									{#if isFocusMode}
										<Minimize2 size={18} />
									{:else}
										<Maximize2 size={18} />
									{/if}
									<div
										class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none uppercase tracking-widest"
									>
										{isFocusMode ? t('replay.room.exitFocus') : t('replay.room.focusMode')}
									</div>
								</button>

								<button
									class="group/btn relative w-10 h-10 flex items-center justify-center {isFullscreen
										? 'bg-white text-black'
										: 'hover:bg-white/10 text-white'} rounded-full transition-all flex-shrink-0 cursor-pointer"
									onclick={toggleFullscreen}
								>
									{#if isFullscreen}
										<Minimize size={18} />
									{:else}
										<Maximize size={18} />
									{/if}
									<div
										class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none uppercase tracking-widest"
									>
										{isFullscreen ? t('replay.room.exit') : t('replay.room.fullscreen')}
									</div>
								</button>

								<div class="w-px h-4 bg-white/20 mx-1"></div>

								<div class="flex items-center gap-1">
									<button
										class="group/btn relative w-10 h-10 flex items-center justify-center {chatVisible
											? 'hover:bg-white/10 text-white'
											: 'bg-white text-black'} rounded-full transition-all flex-shrink-0 cursor-pointer"
										onclick={() => (chatVisible = !chatVisible)}
									>
										<MessageCircle size={18} />
										<div
											class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-zinc-900 text-white text-[10px] font-bold rounded shadow-xl opacity-0 invisible group-hover/btn:opacity-100 group-hover/btn:visible transition-all duration-200 whitespace-nowrap z-[6000] pointer-events-none"
										>
											{chatVisible ? t('replay.room.hideChat') : t('replay.room.showChat')}
										</div>
									</button>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>

	{#if chatVisible}
		<div
			class="w-full lg:w-[320px] flex flex-col gap-4 min-h-0 p-1 {isFocusMode
				? 'h-[40%] lg:h-full lg:flex-none'
				: 'flex-1 lg:flex-none'}"
			transition:fade={{ duration: 300 }}
		>
			<div
				class="bg-white dark:bg-zinc-950 rounded-3xl border border-gray-100 dark:border-zinc-800 overflow-hidden flex flex-col shadow-sm {isFocusMode
					? 'flex-1'
					: 'flex-1 lg:h-full'}"
			>
				{#if video && video.srt_file}
					<ReplayChat srtFile={video.srt_file} {currentTime} />
				{:else}
					<div class="flex-1 flex items-center justify-center text-zinc-500">
						<div class="text-center px-4">
							<MessageCircle size={32} class="mx-auto mb-3 text-zinc-700" />
							<p class="text-xs font-bold">{t('replay.room.chatNotAvailable')}</p>
						</div>
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	:global(.custom-range::-webkit-slider-thumb) {
		appearance: none;
		width: 14px;
		height: 14px;
		background: white;
		border-radius: 50%;
		cursor: pointer;
		box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
		border: 2px solid #ef4444;
	}
	:global(.custom-range::-moz-range-thumb) {
		width: 14px;
		height: 14px;
		background: white;
		border-radius: 50%;
		cursor: pointer;
		box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
		border: 2px solid #ef4444;
	}
</style>
