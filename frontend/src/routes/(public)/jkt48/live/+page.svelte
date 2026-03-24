<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { fade, fly } from 'svelte/transition';
	import { live } from '$lib/apis/live';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { Star, Users, ExternalLink, Play, Tv } from 'lucide-svelte';
	import { getExternalMediaUrl } from '$lib/utils/media';

	const { t } = useTranslation();

	let lives: any[] = [];
	let loading = true;
	let error = false;
	let interval: any;

	async function fetchLives() {
		try {
			const res = await live.getLiveStatus();
			lives = res.data || [];
			error = false;
		} catch (e) {
			console.error('Failed to fetch lives:', e);
			error = true;
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		fetchLives();
		interval = setInterval(fetchLives, 60000); // Refresh every 60 seconds
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
	<header class="mb-12 text-center" in:fly={{ y: -20, duration: 600 }}>
		<div class="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-red-100 dark:bg-red-500/10 text-red-600 dark:text-red-400 text-xs font-black uppercase tracking-widest mb-4">
			<span class="w-2 h-2 rounded-full bg-red-600 animate-pulse"></span>
			{$t('theater.live.onLive')}
		</div>
		<h1 class="text-4xl sm:text-5xl font-black tracking-tighter text-slate-900 dark:text-white mb-4">
			JKT48 <span class="text-red-600 italic">LIVE</span>
		</h1>
		<p class="text-slate-500 dark:text-slate-400 max-w-2xl mx-auto px-6 font-medium">
			{$t('theater.live.subtitle')}
		</p>
	</header>

	{#if loading && lives.length === 0}
		<div class="flex flex-col items-center justify-center py-24" transition:fade>
			<div class="w-16 h-16 border-4 border-red-600 border-t-transparent rounded-full animate-spin mb-4"></div>
			<p class="text-slate-400 font-bold uppercase tracking-widest text-xs">{$t('common.loading')}</p>
		</div>
	{:else if lives.length === 0}
		<div class="flex flex-col items-center justify-center py-24 text-center px-6" in:fade>
			<div class="w-24 h-24 rounded-full bg-slate-100 dark:bg-zinc-900 flex items-center justify-center mb-6 text-slate-300 dark:text-zinc-800">
				<Tv size={48} />
			</div>
			<h2 class="text-2xl font-black text-slate-900 dark:text-white mb-2 italic">POOF!</h2>
			<p class="text-slate-500 dark:text-slate-400 font-medium max-w-md">
				{$t('theater.live.empty')}
			</p>
		</div>
	{:else}
		<div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4 px-4">
			{#each lives as live, i (live.platform + (live.room_id || live.live_id))}
				<a 
					href="/jkt48/live/{live.platform}/{live.room_id || live.live_id}"
					class="group relative aspect-[3/4] flex flex-col bg-white dark:bg-zinc-900 rounded-xl overflow-hidden shadow-xl shadow-slate-200/50 dark:shadow-none hover:shadow-2xl transition-all duration-500 hover:-translate-y-2 cursor-pointer"
					in:fly={{ y: 20, delay: i * 100, duration: 500 }}
				>
					<!-- Member Photo Container -->
					<div class="relative w-full h-full overflow-hidden bg-gray-100 dark:bg-zinc-800">
						<img 
							src={getExternalMediaUrl(live.member?.img) || fallbackAvatar} 
							alt={live.member?.name}
							on:error={(e) => { if (e.currentTarget instanceof HTMLImageElement) e.currentTarget.src = fallbackAvatar; }}
							class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
						/>
						
						<!-- Frame Image Overlay -->
						<img
							src={live.member?.member_type?.toLowerCase() === 'trainee' ? 'https://jkt48.com/images/member/bg-member-trainee-frame-transparent.png' : 'https://jkt48.com/images/member/bg-member-item-frame-transparent.png'}
							alt="frame"
							class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10"
						/>

						<!-- Gradient Overlay -->
						<div class="absolute inset-0 bg-gradient-to-t from-black/95 via-black/20 to-transparent z-20"></div>

						<!-- Platform & Viewers Badges -->
						<div class="absolute top-4 left-4 right-4 flex items-center justify-end gap-2 z-30">
							{#if live.view_num > 0}
								<div class="px-3 py-1 rounded-full bg-black/60 backdrop-blur-md text-white text-[10px] font-black uppercase tracking-widest border border-white/20 flex items-center gap-1.5 shadow-lg">
									<Users size={12} class="text-sky-400" />
									{live.view_num.toLocaleString()}
								</div>
							{/if}

							<div class="px-3 py-1 rounded-full bg-black/60 backdrop-blur-md text-white text-[10px] font-black uppercase tracking-widest border border-white/20 flex items-center gap-1.5 shadow-lg">
								<span class="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse"></span>
								{live.platform}
							</div>
						</div>

						<!-- Content Area (Overlay) -->
						<div class="absolute bottom-0 left-0 right-0 p-4 flex flex-col justify-end z-30">
							<div class="flex items-center justify-between gap-2 mb-0.5">
								<h3 class="font-black text-white text-base leading-tight drop-shadow-md group-hover:text-red-500 transition-colors line-clamp-1">
									{live.member?.name}
								</h3>
								<div class="shrink-0 w-6 h-6 rounded-full bg-gradient-to-br {getPlatformColor(live.platform)} flex items-center justify-center text-white text-[8px] font-bold shadow-lg shadow-black/30 border border-white/20">
									{getPlatformIcon(live.platform)}
								</div>
							</div>
							<p class="text-[10px] text-gray-300 font-medium drop-shadow-sm line-clamp-1">
								{live.title || 'Streaming JKT48! ✨'}
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
	/* Custom styles if needed */
</style>
