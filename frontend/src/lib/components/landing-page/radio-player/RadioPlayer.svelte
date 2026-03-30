<script lang="ts">
	import { fade, fly } from 'svelte/transition';
	import { Play, Pause, SkipForward, Volume2, VolumeX, Music2, Disc, Radio } from 'lucide-svelte';
	import { radioStore, RADIO_CHANNELS } from '$lib/stores/radio';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	$: currentChannel = RADIO_CHANNELS.find((c) => c.id === $radioStore.currentChannelId) || RADIO_CHANNELS[0];

	function handleVolumeChange(e: Event) {
		const vol = parseInt((e.target as HTMLInputElement).value);
		radioStore.setVolume(vol);
	}

	function toggleMute() {
		radioStore.setMuted(!$radioStore.isMuted);
	}

	function nextTrack() {
		radioStore.skip();
	}

	function changeChannel(channelId: string) {
		radioStore.setChannel(channelId);
	}
</script>

<div
	class="w-80 bg-white/90 dark:bg-zinc-900/90 backdrop-blur-2xl border border-gray-100 dark:border-zinc-800 rounded-3xl shadow-2xl p-5 overflow-hidden ring-1 ring-black/5"
	transition:fly={{ y: 20, duration: 300, opacity: 0 }}
>
	<!-- Header: Pulse Indicator -->
	<div class="flex items-center justify-between mb-6">
		<div class="flex items-center gap-2">
			<div class="relative flex h-2 w-2">
				{#if $radioStore.isPlaying}
					<span
						class="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"
					></span>
				{/if}
				<span class="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
			</div>
			<span class="text-[10px] font-black uppercase tracking-[0.2em] text-red-600 dark:text-red-400"
				>JKT48 Radio</span
			>
		</div>
		<div class="px-2 py-0.5 rounded-full bg-gray-100 dark:bg-zinc-800 text-[9px] font-bold text-gray-500 dark:text-zinc-400 border border-gray-200 dark:border-zinc-700">
			{$radioStore.isPlaying ? $t('landing.radio.nowPlaying') : $t('landing.radio.paused')}
		</div>
	</div>

	<!-- Album Art / Vinyl -->
	<div class="relative group mb-6">
		<div class="aspect-square w-full relative perspective-1000">
			<!-- Shadow -->
			<div class="absolute inset-4 bg-black/40 blur-2xl rounded-full translate-y-4 scale-95 opacity-50 dark:opacity-80"></div>
			
			<!-- Disc Background -->
			<div 
				class="absolute inset-0 bg-zinc-900 rounded-full shadow-2xl ring-4 ring-black/5 dark:ring-white/5 flex items-center justify-center overflow-hidden transition-transform duration-700"
				class:animate-spin-slow={$radioStore.isPlaying}
			>
				{#if $radioStore.currentThumbnail}
					<img 
						src={$radioStore.currentThumbnail} 
						alt="Track Art" 
						class="w-[110%] h-[110%] object-cover opacity-60 blur-[2px]"
					/>
				{:else}
					<div class="w-full h-full bg-gradient-to-tr from-zinc-800 to-zinc-900 flex items-center justify-center">
						<Disc size={64} class="text-zinc-700 opacity-20" />
					</div>
				{/if}
				
				<!-- Inner Hole -->
				<div class="absolute inset-0 flex items-center justify-center">
					<div class="w-24 h-24 rounded-full bg-white dark:bg-zinc-900 shadow-inner border-8 border-black/10 dark:border-white/10 overflow-hidden relative">
						{#if $radioStore.currentThumbnail}
							<img src={$radioStore.currentThumbnail} alt="Art" class="w-full h-full object-cover scale-150" />
						{:else}
							<div class="w-full h-full idol-gradient flex items-center justify-center">
								<Music2 class="text-white w-8 h-8" />
							</div>
						{/if}
						<div class="absolute inset-0 bg-gradient-to-tr from-transparent via-white/10 to-transparent"></div>
						<!-- Center hole -->
						<div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-4 h-4 rounded-full bg-zinc-900 border border-white/20 shadow-lg"></div>
					</div>
				</div>
				
				<!-- Vinyl Grooves -->
				<div class="absolute inset-0 rounded-full border border-white/5 pointer-events-none opacity-20"></div>
				<div class="absolute inset-4 rounded-full border border-white/5 pointer-events-none opacity-10"></div>
				<div class="absolute inset-8 rounded-full border border-white/5 pointer-events-none opacity-5"></div>
			</div>
		</div>
	</div>

	<!-- Track Info -->
	<div class="text-center mb-6 min-h-[48px]">
		<h3 class="text-sm font-black text-gray-900 dark:text-gray-100 line-clamp-1 mb-1 tracking-tight">
			{$radioStore.currentTrackTitle || $t('landing.radio.connecting')}
		</h3>
		<p class="text-[10px] font-bold text-gray-400 dark:text-zinc-500 uppercase tracking-widest">
			{$t(`landing.radio.${currentChannel.id}`)}
		</p>
	</div>

	<!-- Controls -->
	<div class="flex items-center justify-between gap-4 mb-8">
		<div class="flex-1 flex justify-center items-center gap-6">
			<button 
				class="p-2 text-gray-400 hover:text-red-500 dark:text-zinc-500 dark:hover:text-red-400 transition-colors active:scale-90 cursor-pointer"
				on:click={() => radioStore.toggle()}
				title={$radioStore.isPlaying ? $t('landing.radio.pause') : $t('landing.radio.play')}
			>
				{#if $radioStore.isPlaying}
					<Pause size={24} fill="currentColor" />
				{:else}
					<Play size={24} fill="currentColor" />
				{/if}
			</button>
			
			<button 
				class="p-2 text-gray-400 hover:text-red-500 dark:text-zinc-500 dark:hover:text-red-400 transition-colors active:scale-90 cursor-pointer"
				on:click={nextTrack}
				title={$t('landing.radio.nextTrack')}
			>
				<SkipForward size={24} fill="currentColor" />
			</button>
		</div>

		<div class="flex items-center gap-2 px-3 py-1 bg-gray-50 dark:bg-zinc-800/50 rounded-full border border-gray-100 dark:border-zinc-800 group/vol">
			<button class="text-gray-400 hover:text-gray-900 dark:text-zinc-500 dark:hover:text-white cursor-pointer" on:click={toggleMute}>
				{#if $radioStore.isMuted || $radioStore.volume === 0}
					<VolumeX size={14} />
				{:else}
					<Volume2 size={14} />
				{/if}
			</button>
			<input 
				type="range" 
				min="0" 
				max="100" 
				value={$radioStore.volume} 
				on:input={handleVolumeChange}
				class="w-16 h-1 bg-gray-200 dark:bg-zinc-700 rounded-full appearance-none accent-red-500 cursor-pointer"
			/>
		</div>
	</div>

	<div class="grid grid-cols-3 gap-2">
		{#each RADIO_CHANNELS as channel}
			<button
				class="flex flex-col items-center gap-1.5 p-2 rounded-2xl border transition-all duration-300 cursor-pointer {channel.id === $radioStore.currentChannelId ? 'bg-red-50 dark:bg-red-500/10 border-red-200 dark:border-red-500/30 ring-1 ring-red-100 dark:ring-red-500/10' : 'bg-transparent border-transparent hover:bg-gray-50 dark:hover:bg-zinc-800'}"
				on:click={() => changeChannel(channel.id)}
			>

				<div class="w-8 h-8 rounded-full flex items-center justify-center {channel.id === $radioStore.currentChannelId ? 'bg-red-500 text-white shadow-lg shadow-red-500/30' : 'bg-gray-100 dark:bg-zinc-800 text-gray-500 dark:text-zinc-400'}">
					<Radio size={14} />
				</div>
				<span class="text-[9px] font-black uppercase tracking-tight {channel.id === $radioStore.currentChannelId ? 'text-red-600 dark:text-red-400' : 'text-gray-400 dark:text-zinc-500'}">
					{$t('landing.radio.' + channel.id)}
				</span>
			</button>
		{/each}
	</div>
</div>

<style>
	.perspective-1000 {
		perspective: 1000px;
	}

	@keyframes spin-slow {
		from {
			transform: rotate(0deg);
		}
		to {
			transform: rotate(360deg);
		}
	}

	.animate-spin-slow {
		animation: spin-slow 8s linear infinite;
	}

	input[type='range']::-webkit-slider-thumb {
		-webkit-appearance: none;
		width: 10px;
		height: 10px;
		background-color: theme('colors.red.600');
		border-radius: 9999px;
		border: none;
		box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
		transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
	}

	input[type='range']:hover::-webkit-slider-thumb {
		transform: scale(1.25);
	}
</style>
