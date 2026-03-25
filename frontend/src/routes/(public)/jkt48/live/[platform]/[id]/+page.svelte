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
		Camera,
		Circle,
		Square
	} from 'lucide-svelte';
	import { fade, fly } from 'svelte/transition';
	import { getExternalMediaUrl } from '$lib/utils/media';

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
	let mediaRecorder: any = null;
	let recordedChunks: any[] = [];
	let sidebarMode: 'chat' | 'list' = 'chat';

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
						});
					} else if (videoElement.canPlayType('application/vnd.apple.mpegurl')) {
						videoElement.src = streamUrl;
						videoElement.addEventListener('loadedmetadata', () => {
							videoElement.play().catch((e) => console.log('Autoplay blocked', e));
						});
					}
				}
			}
		} catch (e: any) {
			console.error('Player init failed:', e);
			if (currentInit !== initCount) return;

			// Handle 404 error from server
			if (e?.detail === 'No streaming URL found for this room.') {
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
		await initPlayer();
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
			} catch (err) {
				console.error('Recording failed to start:', err);
				// Standard alert only if it's a persistent error
				alert('Record failed. Please ensure the video is playing and try again in a few seconds.');
			}
		} else {
			if (mediaRecorder) {
				mediaRecorder.stop();
				isRecording = false;
			}
		}
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
	<div class="flex-[1.5] lg:flex-1 flex flex-col gap-4 overflow-hidden min-h-0">
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

			<div
				class="flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-600 text-white text-[10px] font-black uppercase tracking-widest animate-pulse"
			>
				{$t('theater.live.liveBadge')}
			</div>
		</div>

		<!-- Video Player -->
		<div
			class="relative flex-1 bg-black rounded-3xl overflow-hidden shadow-2xl border border-gray-100 dark:border-zinc-800"
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

			<div class="w-full h-full flex items-center justify-center">
				<!-- svelte-ignore a11y-media-has-caption -->
				<video
					bind:this={videoElement}
					class="w-full h-full object-contain"
					crossorigin="anonymous"
					controls
					autoplay
					playsinline
				></video>
			</div>
		</div>

		<!-- Player Controls -->
		<div class="flex items-center justify-end gap-3 pr-2">
			<!-- Screenshot Button -->
			<div class="group relative">
				<button
					class="w-10 h-10 bg-blue-600 hover:bg-blue-700 active:scale-95 text-white rounded-full flex items-center justify-center shadow-lg shadow-blue-500/20 transition-all cursor-pointer"
					on:click={takeScreenshot}
				>
					<Camera size={18} />
				</button>
				<div
					class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-zinc-900 border border-zinc-800 text-white text-[9px] font-black uppercase tracking-[0.15em] rounded-lg opacity-0 group-hover:opacity-100 transition-all pointer-events-none whitespace-nowrap shadow-2xl z-[100]"
				>
					{$t('theater.live.screenshot')}
				</div>
			</div>

			<!-- Recording Button -->
			<div class="group relative">
				<button
					class="w-10 h-10 {isRecording
						? 'bg-red-600 animate-pulse'
						: 'bg-zinc-900 dark:bg-zinc-800'} hover:bg-red-700 active:scale-95 text-white rounded-full flex items-center justify-center shadow-lg transition-all cursor-pointer"
					on:click={toggleRecording}
				>
					{#if isRecording}
						<Square size={18} fill="currentColor" />
					{:else}
						<Circle size={18} fill="currentColor" class="text-red-600" />
					{/if}
				</button>
				<div
					class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-zinc-900 border border-zinc-800 text-white text-[9px] font-black uppercase tracking-[0.15em] rounded-lg opacity-0 group-hover:opacity-100 transition-all pointer-events-none whitespace-nowrap shadow-2xl z-[100]"
				>
					{isRecording ? $t('theater.live.stopRecord') : $t('theater.live.record')}
				</div>
			</div>

			<!-- Focus Mode Button -->
			<div class="group relative">
				<button
					class="w-10 h-10 {isFocusMode
						? 'bg-zinc-100 dark:bg-zinc-800 text-slate-900 dark:text-white'
						: 'bg-zinc-900 dark:bg-zinc-800 text-white'} hover:opacity-80 active:scale-95 rounded-full flex items-center justify-center shadow-lg transition-all cursor-pointer"
					on:click={toggleFocus}
				>
					{#if isFocusMode}
						<Minimize2 size={18} />
					{:else}
						<Maximize2 size={18} />
					{/if}
				</button>
				<div
					class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-zinc-900 border border-zinc-800 text-white text-[9px] font-black uppercase tracking-[0.15em] rounded-lg opacity-0 group-hover:opacity-100 transition-all pointer-events-none whitespace-nowrap shadow-2xl z-[100]"
				>
					{isFocusMode ? $t('theater.live.exitFocus') : $t('theater.live.focusMode')}
				</div>
			</div>

			<!-- Refresh Button -->
			<div class="group relative">
				<button
					class="w-10 h-10 bg-red-600 hover:bg-red-700 active:scale-95 text-white rounded-full flex items-center justify-center shadow-lg shadow-red-500/20 transition-all cursor-pointer"
					on:click={refreshStream}
				>
					<RefreshCw size={18} class={$liveLoading ? 'animate-spin' : ''} />
				</button>
				<div
					class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-zinc-900 border border-zinc-800 text-white text-[9px] font-black uppercase tracking-[0.15em] rounded-lg opacity-0 group-hover:opacity-100 transition-all pointer-events-none whitespace-nowrap shadow-2xl z-[100]"
				>
					{$t('theater.live.refresh')}
				</div>
			</div>

			<!-- Toggle Mode Button -->
			<div class="group relative">
				<button
					class="w-10 h-10 {sidebarMode === 'list'
						? 'bg-red-600'
						: 'bg-zinc-900 dark:bg-zinc-800'} hover:bg-red-600 active:scale-95 text-white rounded-full flex items-center justify-center shadow-lg transition-all cursor-pointer"
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
				</button>
				<div
					class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-zinc-900 border border-zinc-800 text-white text-[9px] font-black uppercase tracking-[0.15em] rounded-lg opacity-0 group-hover:opacity-100 transition-all pointer-events-none whitespace-nowrap shadow-2xl z-[100]"
				>
					{sidebarMode === 'chat' ? $t('theater.subNav.live') : $t('theater.live.chat')}
				</div>
			</div>

			<!-- Chat Toggle Button -->
			<div class="group relative">
				<button
					class="w-10 h-10 bg-zinc-900 dark:bg-zinc-800 hover:bg-black dark:hover:bg-zinc-700 active:scale-95 text-white rounded-full flex items-center justify-center shadow-lg transition-all cursor-pointer"
					on:click={toggleChat}
				>
					{#if chatVisible}
						<ChevronRight size={18} />
					{:else}
						<ChevronLeft size={18} />
					{/if}
				</button>
				<div
					class="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-zinc-900 border border-zinc-800 text-white text-[9px] font-black uppercase tracking-[0.15em] rounded-lg opacity-0 group-hover:opacity-100 transition-all pointer-events-none whitespace-nowrap shadow-2xl z-[100]"
				>
					{chatVisible ? $t('theater.live.hideChat') : $t('theater.live.showChat')}
				</div>
			</div>
		</div>
	</div>

	<!-- Sidebar (Chat & Member Info) -->
	{#if chatVisible}
		<div
			class="w-full lg:w-[320px] flex flex-col gap-4 overflow-hidden min-h-0 {isFocusMode
				? 'h-full lg:flex-none'
				: 'flex-1 lg:flex-none'}"
			transition:fly={{ x: 20, duration: 300 }}
		>
			<!-- Chat Window placeholder -->
			<div
				class="bg-white dark:bg-zinc-950 rounded-3xl border border-gray-100 dark:border-zinc-800 overflow-hidden flex flex-col shadow-2xl {isFocusMode
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
										class="flex items-center gap-3 p-2.5 rounded-2xl bg-white dark:bg-zinc-900 border border-slate-100 dark:border-zinc-800/50 hover:border-red-500/30 hover:shadow-xl hover:shadow-red-500/5 transition-all group overflow-hidden relative"
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
													class="px-1.5 py-0.5 bg-red-600 rounded-md text-[7px] font-black text-white uppercase tracking-tighter shadow-xl"
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
</style>
