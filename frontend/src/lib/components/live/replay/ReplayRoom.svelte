<script lang="ts">
	import { page } from '$app/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { replayStore } from '$lib/stores/replay.svelte';
	import { isImmersive } from '$lib/stores';
	import ReplayChat from './ReplayChat.svelte';
	import SEO from '$lib/components/SEO.svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import PlatformLogo from '$lib/components/live/PlatformLogo.svelte';
	import type { ReplayVideo } from '$lib/types/replay';
	import {
		ArrowLeft,
		Tv,
		PanelRightClose,
		PanelRightOpen,
		PanelBottomClose,
		PanelBottomOpen,
		MessageCircle,
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
	let chatVisible = $state(true);
	let videoContainer: HTMLDivElement | undefined = $state();
	let initAttempted = $state(false);
	let { id } = $derived($page.params);

	let video: ReplayVideo | undefined = $derived(
		replayStore.videos.find((v) => v.youtube_id === id)
	);

	let isTheater = $derived(basePath.startsWith('/theater'));

	const shouldManage = false;

	$effect(() => {
		if (shouldManage) isImmersive.set(true);
		document.body.style.overflow = 'hidden';
		return () => {
			if (shouldManage) isImmersive.set(false);
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

	function disableCaptions() {
		try {
			if (youTubePlayer?.unloadModule) youTubePlayer.unloadModule('captions');
		} catch {
			/* ignore */
		}
	}

	function createPlayer() {
		if (!playerContainer || !id) return;
		try {
			youTubePlayer = new YT.Player(playerContainer, {
				videoId: id,
				playerVars: {
					autoplay: 1,
					mute: 1,
					rel: 0,
					controls: 1,
					playsinline: 1,
					fs: 1,
					iv_load_policy: 3,
					cc_load_policy: 0,
					origin: window.location.origin
				},
				events: {
					onReady: (event: {
						target: {
							getDuration: () => number;
							playVideo: () => void;
							unMute: () => void;
							unloadModule?: (module: string) => void;
						};
					}) => {
						youTubePlayer = event.target;
						youTubeReady = true;
						initAttempted = true;
						duration = event.target.getDuration() || 0;
						event.target.unMute();
						event.target.playVideo();
						disableCaptions();
					},
					onApiChange: () => {
						disableCaptions();
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

	const youtubeUrl = $derived(`https://www.youtube.com/watch?v=${id}`);
</script>

<SEO
	title={video
		? t('replay.room.seoTitle', { member: video.member })
		: t('replay.room.seoTitleFallback')}
	path={$page.url.pathname}
	description={video
		? t('replay.room.seoDesc', { member: video.member, title: video.title })
		: t('replay.room.seoTitleFallback')}
/>

<div
	class="fixed inset-0 !top-0 !mt-0 z-[7000] bg-white dark:bg-zinc-950 p-2 sm:p-4 h-[100dvh] w-screen flex flex-col lg:flex-row gap-4 transition-all duration-500 ease-in-out overflow-hidden"
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

			<div class="flex items-center gap-2 flex-shrink-0">
				<div class="hidden sm:flex items-center gap-3">
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
					<div class="w-px h-4 bg-slate-200 dark:bg-zinc-800"></div>
					<button
						class="w-8 h-8 flex items-center justify-center text-slate-500 dark:text-slate-400 hover:text-red-600 transition-colors rounded-full hover:bg-slate-100 dark:hover:bg-zinc-800 cursor-pointer"
						onclick={() => (chatVisible = !chatVisible)}
						title={chatVisible ? t('replay.room.hideChat') : t('replay.room.showChat')}
					>
						{#if chatVisible}
							<PanelRightClose size={18} />
						{:else}
							<PanelRightOpen size={18} />
						{/if}
					</button>
				</div>
				<button
					class="sm:hidden w-8 h-8 flex items-center justify-center text-slate-500 dark:text-slate-400 hover:text-red-600 transition-colors rounded-full hover:bg-slate-100 dark:hover:bg-zinc-800 cursor-pointer"
					onclick={() => (chatVisible = !chatVisible)}
					title={chatVisible ? t('replay.room.hideChat') : t('replay.room.showChat')}
				>
					{#if chatVisible}
						<PanelBottomClose size={18} />
					{:else}
						<PanelBottomOpen size={18} />
					{/if}
				</button>
			</div>
		</div>

		<!--
			`overflow-clip` + `rounded-*` on mobile breaks YouTube touch/click events on the iframe,
			preventing the native player controls from appearing on tap.
			Rounded corners & overflow-clip are intentionally desktop-only.
		-->
		<div
			bind:this={videoContainer}
			class="relative z-10 flex-1 bg-black sm:rounded-3xl sm:overflow-clip border border-gray-100 dark:border-zinc-800 shadow-sm"
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

			<div
				bind:this={playerContainer}
				id="replay-youtube-player"
				class="relative w-full h-full bg-black"
			></div>
		</div>
	</div>

	{#if chatVisible}
		<div
			class="w-full lg:w-[320px] flex flex-col gap-4 min-h-0 p-1 h-[40%] lg:h-full lg:flex-none overflow-hidden"
		>
			<div
				class="bg-white dark:bg-zinc-950 rounded-3xl border border-gray-100 dark:border-zinc-800 overflow-hidden flex flex-col shadow-sm flex-1 min-h-0"
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

<style></style>
