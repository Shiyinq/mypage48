<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import { liveStore, liveList, liveLoading, liveError } from '$lib/stores/live';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { Star, Users, ExternalLink, Play, Tv } from 'lucide-svelte';
	import { getExternalMediaUrl } from '$lib/utils/media';

	const { t } = useTranslation();

	let interval: any;

	let initialLoading = true;
	async function fetchLives() {
		await liveStore.loadLiveList();
		initialLoading = false;
	}

	onMount(() => {
		fetchLives();
		interval = setInterval(() => liveStore.loadLiveList(true), 60000); // Refresh every 60 seconds
	});

	onDestroy(() => {
		if (interval) clearInterval(interval);
	});

	function getPlatformIcon(platform: string) {
		if (platform === 'showroom') return 'SR';
		if (platform === 'idn') return 'IDN';
		return '';
	}

	function getPlatformColor(platform: string) {
		if (platform === 'showroom') return 'from-blue-500 to-indigo-600';
		if (platform === 'idn') return 'from-red-500 to-rose-600';
		return 'from-gray-500 to-gray-600';
	}

	const fallbackAvatar = 'https://placehold.co/640x960?text=NO%20IMAGE';
</script>

<svelte:head>
	<title>{$t('theater.live.title')} | MyPage48</title>
</svelte:head>

<div class="py-12 min-h-screen">
	<!-- Header Section -->
	<header class="mb-12" in:fly={{ y: -20, duration: 600 }}>
		<div class="max-w-7xl mx-auto px-6 flex flex-col items-center">
			<div class="flex flex-col md:flex-row items-center justify-between w-full gap-6">
				<div class="flex-1 text-center md:text-left">
					<div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-100 dark:bg-red-500/10 text-red-600 dark:text-red-400 text-[10px] font-black uppercase tracking-widest mb-4">
						<span class="w-1.5 h-1.5 rounded-full bg-red-600 animate-pulse"></span>
						{$t('theater.live.onLive')}
					</div>
					<h1 class="text-4xl sm:text-6xl font-black tracking-tighter text-slate-900 dark:text-white leading-[0.9]">
						JKT48 <span class="text-red-600 italic">LIVE</span>
					</h1>
					<p class="text-slate-500 dark:text-slate-400 mt-4 font-medium max-w-lg">
						{$t('theater.live.subtitle')}
					</p>
				</div>

				{#if $liveList.length > 0}
					<div class="shrink-0 flex items-center">
						<a 
							href="/jkt48/live/multiview"
							class="group relative flex items-center gap-2 px-5 py-2.5 rounded-2xl bg-white dark:bg-zinc-900 border border-gray-100 dark:border-zinc-800 shadow-xl shadow-slate-200/50 dark:shadow-none hover:shadow-2xl hover:-translate-y-0.5 transition-all duration-300 overflow-hidden"
						>
							<div class="absolute inset-0 bg-gradient-to-r from-red-500/0 via-red-500/5 to-red-500/0 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
							
							<div class="w-8 h-8 rounded-xl bg-red-50 dark:bg-red-500/10 flex items-center justify-center text-red-600 group-hover:bg-red-600 group-hover:text-white transition-all duration-300">
								<Users size={18} />
							</div>
							
							<div class="flex flex-col items-start leading-none gap-0.5">
								<span class="text-[10px] font-black uppercase tracking-widest text-slate-400 group-hover:text-red-600 transition-colors">{$t('theater.live.multiview.title')}</span>
								<span class="text-sm font-black tracking-tight text-slate-900 dark:text-white">{$t('theater.live.switchMultiview')}</span>
							</div>

							<div class="ml-2 w-5 h-5 rounded-lg bg-slate-100 dark:bg-zinc-800 flex items-center justify-center text-[10px] font-black text-slate-500">
								{$liveList.length}
							</div>
						</a>
					</div>
				{/if}
			</div>
		</div>
	</header>

	{#if (initialLoading || $liveLoading) && $liveList.length === 0}
		<div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4 px-4">
			{#each Array(10) as _}
				<div class="aspect-[3/4] bg-slate-100 dark:bg-zinc-900 rounded-xl overflow-hidden relative shadow-sm border border-slate-100 dark:border-zinc-800">
					<div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 dark:via-white/5 to-transparent -translate-x-full animate-shimmer"></div>
					<div class="absolute bottom-0 left-0 right-0 p-4 space-y-2">
						<div class="h-4 w-2/3 bg-slate-200 dark:bg-zinc-800 rounded"></div>
						<div class="h-3 w-1/2 bg-slate-200 dark:bg-zinc-800 rounded"></div>
					</div>
				</div>
			{/each}
		</div>
	{:else if $liveList.length === 0}
		<div class="flex flex-col items-center justify-center py-24 text-center px-6" in:fade>
			<div class="w-24 h-24 rounded-full bg-slate-100 dark:bg-zinc-900 flex items-center justify-center mb-6 text-slate-300 dark:text-zinc-800">
				<Tv size={48} />
			</div>
			<h2 class="text-2xl font-black text-slate-900 dark:text-white mb-2 italic">
				{$t('theater.live.emptyTitle')}
			</h2>
			<p class="text-slate-500 dark:text-slate-400 font-medium max-w-md">
				{$t('theater.live.empty')}
			</p>
		</div>
	{:else}
		<div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4 px-4">
			{#each $liveList as stream, i (stream.platform + (stream.room_id || stream.live_id))}
				<a 
					href="/jkt48/live/{stream.platform}/{stream.room_id || stream.live_id}"
					class="group relative aspect-[3/4] flex flex-col bg-white dark:bg-zinc-900 rounded-xl overflow-hidden shadow-xl shadow-slate-200/50 dark:shadow-none hover:shadow-2xl transition-all duration-500 hover:-translate-y-2 cursor-pointer"
					in:fade={{ duration: 400, delay: i * 50 }}
				>
					<!-- Member Photo Container -->
					<div class="relative w-full h-full overflow-hidden bg-gray-100 dark:bg-zinc-800">
						<img 
							src={getExternalMediaUrl(stream.member?.img) || fallbackAvatar} 
							alt={stream.member?.name}
							on:error={(e) => { if (e.currentTarget instanceof HTMLImageElement) e.currentTarget.src = fallbackAvatar; }}
							class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
						/>
						
						<!-- Frame Image Overlay -->
						<img
							src={stream.member?.member_type?.toLowerCase() === 'trainee' ? 'https://jkt48.com/images/member/bg-member-trainee-frame-transparent.png' : 'https://jkt48.com/images/member/bg-member-item-frame-transparent.png'}
							alt="frame"
							class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10"
						/>

						<!-- Gradient Overlay -->
						<div class="absolute inset-0 bg-gradient-to-t from-black/95 via-black/20 to-transparent z-20"></div>

						<!-- Platform & Viewers Badges -->
						<div class="absolute top-4 left-4 right-4 flex items-center justify-end gap-2 z-30">
							{#if stream.view_num > 0}
								<div class="px-3 py-1 rounded-full bg-black/60 backdrop-blur-md text-white text-[10px] font-black uppercase tracking-widest border border-white/20 flex items-center gap-1.5 shadow-lg">
									<Users size={12} class="text-sky-400" />
									{stream.view_num.toLocaleString()}
								</div>
							{/if}

							<div class="px-3 py-1 rounded-full bg-black/60 backdrop-blur-md text-white text-[10px] font-black uppercase tracking-widest border border-white/20 flex items-center gap-1.5 shadow-lg">
								<span class="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></span>
								{stream.platform}
							</div>
						</div>

						<!-- Content Area (Overlay) -->
						<div class="absolute bottom-0 left-0 right-0 p-4 flex flex-col justify-end z-30">
							<div class="flex items-center justify-between gap-2 mb-0.5">
								<h3 class="font-black text-white text-base leading-tight drop-shadow-md group-hover:text-red-500 transition-colors line-clamp-1">
									{stream.member?.name}
								</h3>
								<div class="shrink-0 w-6 h-6 rounded-full bg-gradient-to-br {getPlatformColor(stream.platform)} flex items-center justify-center text-white text-[8px] font-bold shadow-lg shadow-black/30 border border-white/20">
									{getPlatformIcon(stream.platform)}
								</div>
							</div>
							<p class="text-[10px] text-gray-300 font-medium drop-shadow-sm line-clamp-1">
								{stream.title || $t('theater.live.multiview.live_status')}
							</p>
						</div>

						<!-- Hover Play Button Indicator -->
						<div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-all duration-500 bg-black/20 backdrop-blur-[2px] z-40">
							<div class="w-16 h-16 rounded-full bg-red-600 text-white flex items-center justify-center shadow-2xl scale-50 group-hover:scale-100 transition-transform duration-500">
								<Play fill="currentColor" size={28} class="ml-1" />
							</div>
						</div>
					</div>
				</a>			{/each}
		</div>
	{/if}
</div>

<style>
	@keyframes shimmer {
		100% { transform: translateX(100%); }
	}
	.animate-shimmer {
		animation: shimmer 2s infinite;
	}
</style>
