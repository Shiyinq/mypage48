<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { fade, fly, slide } from 'svelte/transition';
	import { liveStore, liveList, liveLoading } from '$lib/stores/live';
	import { live } from '$lib/apis/live';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { 
		Users, 
		Plus, 
		X, 
		Maximize2, 
		Minimize2, 
		Volume2, 
		VolumeX, 
		MessageCircle, 
		Settings2,
		LayoutGrid,
		ChevronRight,
		ChevronLeft,
		Search,
		UserPlus,
		RefreshCw
	} from 'lucide-svelte';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import ShowroomChat from '$lib/components/live/ShowroomChat.svelte';
	import IDNChat from '$lib/components/live/IDNChat.svelte';
	import MultiPlayer from '$lib/components/live/MultiPlayer.svelte';

	const { t } = useTranslation();

	// Multi-view State
	let slots: any[] = [];
	let focusedSlotIndex: number = 0;
	let focusedStreamDetails: any = null;
	let showPicker = true;
	let showChat = true;
	let searchQuery = '';

	// Media State for slots
	let volumes: number[] = Array(8).fill(1);
	let muted: boolean[] = Array(8).fill(false);

	$: activeStreams = $liveList;
	$: filteredStreams = activeStreams.filter(s => 
		s.member?.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
		s.title?.toLowerCase().includes(searchQuery.toLowerCase())
	);

	$: focusedStream = slots[focusedSlotIndex];

	onMount(() => {
		liveStore.loadLiveList();
		const interval = setInterval(() => liveStore.loadLiveList(true), 60000);
		
		// Load from localStorage if available
		const saved = localStorage.getItem('mypage48_multiview_slots');
		if (saved) {
			try {
				const parsed = JSON.parse(saved);
				if (Array.isArray(parsed)) {
					slots = parsed.filter(s => s !== null).slice(0, 8);
				}
			} catch (e) {}
		}

		return () => clearInterval(interval);
	});

	function saveSlots() {
		localStorage.setItem('mypage48_multiview_slots', JSON.stringify(slots));
	}

	function addMemberToSlot(stream: any) {
		if (slots.length >= 8) return;
		
		// Check if already in slots
		const exists = slots.find(s => 
			(s.platform === stream.platform && s.room_id === stream.room_id && s.room_id) || 
			(s.platform === stream.platform && s.live_id === stream.live_id && s.live_id)
		);
		if (exists) return;

		slots = [...slots, stream];
		focusedSlotIndex = slots.length - 1;
		saveSlots();
	}

	function setFocusedSlot(index: number) {
		focusedSlotIndex = index;
		const stream = slots[index];
		if (stream) {
			loadFocusedDetails(stream);
		} else {
			focusedStreamDetails = null;
		}
	}

	async function loadFocusedDetails(stream: any) {
		focusedStreamDetails = null; // Clear old info
		try {
			const platform = stream.platform;
			const id = platform === 'showroom' ? (stream.room_id || stream.room_url_key) : (stream.live_id || stream.room_url_key);
			const details = await live.getStreamingUrl(platform, id);
			if (details) {
				focusedStreamDetails = details;
			}
		} catch (err) {
			console.error('Failed to load focused details:', err);
		}
	}

	function removeMemberFromSlot(index: number) {
		slots = slots.filter((_, i) => i !== index);
		saveSlots();
		if (focusedSlotIndex >= slots.length) {
			setFocusedSlot(Math.max(0, slots.length - 1));
		}
	}

	function clearAll() {
		slots = [];
		saveSlots();
	}

	// Computed grid class
	$: expansive = !showPicker && !showChat;
	$: gridClass = slots.length === 1 
		? (expansive ? 'grid-cols-1 max-w-7xl mx-auto' : 'grid-cols-1 max-w-5xl mx-auto') 
		: slots.length === 2 
		? (expansive ? 'grid-cols-2 max-w-none' : 'grid-cols-1 md:grid-cols-2 max-w-6xl mx-auto') 
		: slots.length <= 4 
		? (expansive ? 'grid-cols-2 max-w-none' : 'grid-cols-2 max-w-6xl mx-auto') 
		: slots.length <= 6 
		? (expansive ? 'grid-cols-3 max-w-none' : 'grid-cols-2 lg:grid-cols-3') 
		: (expansive ? 'grid-cols-4 max-w-none' : 'grid-cols-2 lg:grid-cols-4');

	// Auto-initialize first slot if empty and no saved session
	$: if (slots.length === 0 && $liveList.length > 0 && typeof localStorage !== 'undefined' && !localStorage.getItem('mypage48_multiview_slots')) {
		const firstLive = $liveList.find(l => l.platform === 'idn') || $liveList[0];
		if (firstLive) {
			slots = [firstLive];
			setFocusedSlot(0);
		}
	}

	let fallbackAvatar = 'https://placehold.co/640x960?text=NO%20IMAGE';
</script>

<svelte:head>
	<title>Multi-view | MyPage48</title>
</svelte:head>

<div class="fixed inset-0 bg-slate-50 dark:bg-zinc-950 flex flex-col overflow-hidden z-[9999]">
	<!-- Top Bar -->
	<div class="h-14 border-b border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 flex items-center justify-between px-4 z-[10000]">
		<div class="flex items-center gap-4">
			<a href="/jkt48/live" class="flex items-center gap-2 text-slate-900 dark:text-white hover:text-red-600 transition-colors">
				<ChevronLeft size={20} />
				<span class="font-black tracking-tighter text-lg">JKT48 <span class="text-red-600 italic">LIVE</span></span>
			</a>
			<div class="h-4 w-px bg-gray-200 dark:border-zinc-800"></div>
			<div class="flex items-center gap-2 px-3 py-1 bg-red-50 dark:bg-red-500/10 rounded-full">
				<LayoutGrid size={14} class="text-red-600" />
				<span class="text-[10px] font-black uppercase tracking-widest text-red-600 dark:text-red-400">Multi-view</span>
			</div>
		</div>

		<div class="flex items-center gap-2">
			<button 
				on:click={clearAll}
				class="px-3 py-1.5 rounded-lg text-xs font-black uppercase tracking-widest text-slate-500 hover:bg-red-50 hover:text-red-600 transition-all"
			>
				Clear All
			</button>
			<button 
				on:click={() => showPicker = !showPicker}
				class="p-2 rounded-lg {showPicker ? 'bg-red-50 text-red-600' : 'text-slate-500 hover:bg-gray-100 dark:hover:bg-zinc-800'} transition-all"
				title="Toggle Member Picker"
			>
				<UserPlus size={20} />
			</button>
			<button 
				on:click={() => showChat = !showChat}
				class="p-2 rounded-lg {showChat ? 'bg-red-50 text-red-600' : 'text-slate-500 hover:bg-gray-100 dark:hover:bg-zinc-800'} transition-all"
				title="Toggle Chat"
			>
				<MessageCircle size={20} />
			</button>
		</div>
	</div>

	<div class="flex-1 flex overflow-hidden">
		<!-- Member Picker Sidebar -->
		{#if showPicker}
			<div 
				class="w-72 border-r border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 flex flex-col"
				transition:fly={{ x: -288, duration: 300 }}
			>
				<div class="p-4 border-b border-gray-100 dark:border-zinc-800">
					<div class="relative">
						<Search class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
						<input 
							type="text" 
							bind:value={searchQuery}
							placeholder="Search members..."
							class="w-full pl-9 pr-4 py-2 bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 rounded-xl text-xs focus:ring-2 focus:ring-red-500 outline-none"
						/>
					</div>
				</div>
				<div class="flex-1 overflow-y-auto p-2 space-y-1">
					{#if $liveLoading && activeStreams.length === 0}
						{#each Array(6) as _}
							<div class="h-12 bg-gray-50 dark:bg-zinc-800/50 rounded-xl animate-pulse"></div>
						{/each}
					{:else}
						{#each filteredStreams as stream}
							<button 
								on:click={() => addMemberToSlot(stream)}
								class="w-full flex items-center gap-3 p-2 rounded-xl border border-transparent hover:border-red-500/20 hover:bg-red-50/50 dark:hover:bg-red-500/5 transition-all text-left group"
							>
								<div class="relative shrink-0">
									<img 
										src={getExternalMediaUrl(stream.member?.img) || fallbackAvatar} 
										on:error={(e) => { if (e.currentTarget instanceof HTMLImageElement) e.currentTarget.src = fallbackAvatar; }}
										alt={stream.member?.name || 'Member'}
										class="w-10 h-10 rounded-lg object-cover" 
									/>
									<div class="absolute -bottom-1 -right-1 w-4 h-4 rounded-full bg-red-600 flex items-center justify-center text-[8px] font-bold text-white border-2 border-white dark:border-zinc-900">
										{stream.platform === 'showroom' ? 'SR' : 'IDN'}
									</div>
								</div>
								<div class="flex-1 min-w-0">
									<div class="font-bold text-xs text-slate-900 dark:text-white truncate">{stream.member?.name}</div>
									<div class="text-[10px] text-gray-400 truncate">{stream.title || 'Live...'}</div>
								</div>
								<Plus size={16} class="text-gray-300 group-hover:text-red-500 transition-colors" />
							</button>
						{/each}
					{/if}
				</div>
			</div>
		{/if}

		<!-- Main Grid Area -->
		<div class="flex-1 bg-slate-100 dark:bg-black p-2 sm:p-4 overflow-y-auto">
			<div class="grid {gridClass} gap-3 sm:gap-6 h-fit transition-all duration-500 pb-20">
				{#each slots as stream, i (stream.platform + '-' + (stream.live_id || stream.room_id || stream.room_url_key))}
					<!-- svelte-ignore a11y-no-noninteractive-element-to-interactive-role -->
						<div 
							class="relative aspect-video bg-white dark:bg-zinc-900 rounded-2xl overflow-hidden border {focusedSlotIndex === i ? 'border-red-500 ring-2 ring-red-500/50' : 'border-gray-200 dark:border-zinc-800'} group shadow-sm transition-all hover:shadow-md text-left cursor-pointer"
							on:click={() => setFocusedSlot(i)}
							on:keydown={(e) => e.key === 'Enter' && setFocusedSlot(i)}
							role="button"
							tabindex="0"
							aria-label="Focus {stream.member?.name} stream"
						>
						<div class="absolute inset-0 z-0">
							<MultiPlayer 
								platform={stream.platform}
								id={stream.platform === 'showroom' ? (stream.room_id || stream.room_url_key) : (stream.live_id || stream.room_url_key)}
								roomIdentifier={stream.room_url_key}
								volume={volumes[i] || 1}
								muted={muted[i]}
							/>
						</div>
						
						<!-- Slot Header (Overlay) -->
						<div class="absolute inset-x-0 top-0 p-3 flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity z-20 bg-gradient-to-b from-black/60 to-transparent">
							<div class="flex items-center gap-2">
								<img 
									src={getExternalMediaUrl(stream.member?.img) || fallbackAvatar} 
									on:error={(e) => { if (e.currentTarget instanceof HTMLImageElement) e.currentTarget.src = fallbackAvatar; }}
									alt={stream.member?.name || 'Member'}
									class="w-6 h-6 rounded-md object-cover border border-white/20" 
								/>
								<span class="text-[10px] font-black text-white uppercase tracking-wider truncate max-w-[100px]">{stream.member?.name}</span>
							</div>
							<button 
								on:click|stopPropagation={() => removeMemberFromSlot(i)}
								class="w-8 h-8 rounded-xl bg-red-500 hover:bg-red-600 text-white flex items-center justify-center transition-all shadow-lg"
								aria-label="Remove stream"
							>
								<X size={14} />
							</button>
						</div>

						<!-- Slot Controls (Bottom Overlay) -->
						<div class="absolute inset-x-0 bottom-0 p-3 flex items-center justify-between opacity-0 group-hover:opacity-100 transition-opacity z-20 bg-gradient-to-t from-black/60 to-transparent">
							<div class="flex items-center gap-0 group/volume relative h-8">
								<button 
									class="w-8 h-8 rounded-xl bg-white/10 backdrop-blur-md text-white flex items-center justify-center hover:bg-white/20 transition-all shadow-lg z-10"
									on:click|stopPropagation={() => muted[i] = !muted[i]}
									aria-label={muted[i] || volumes[i] === 0 ? 'Unmute' : 'Mute'}
								>
									{#if muted[i] || volumes[i] === 0}<VolumeX size={16}/>{:else}<Volume2 size={16}/>{/if}
								</button>
								<div class="w-0 group-hover/volume:w-24 h-8 overflow-hidden transition-all duration-500 bg-white/10 backdrop-blur-md rounded-r-xl -ml-2 pl-4 flex items-center">
									<input 
										type="range" 
										min="0" max="1" step="0.01" 
										value={volumes[i]}
										on:input={(e) => {
											let val = parseFloat(e.currentTarget.value);
											if (val < 0.05) {
												val = 0;
												muted[i] = true;
											} else if (muted[i] && val > 0) {
												muted[i] = false;
											}
											volumes[i] = val;
											volumes = volumes; // Trigger reactivity
											muted = muted;
										}}
										on:click|stopPropagation
										class="w-16 h-1 accent-white cursor-pointer" 
									/>
								</div>
							</div>
						</div>
					</div>
				{/each}

				{#if slots.length === 0}
					<div class="col-span-full py-20 flex flex-col items-center justify-center text-center">
						<div class="w-20 h-20 rounded-3xl bg-white dark:bg-zinc-900 border border-dashed border-gray-200 dark:border-zinc-800 flex items-center justify-center mb-6 shadow-sm">
							<Plus size={32} class="text-gray-300" />
						</div>
						<h3 class="text-xl font-black uppercase tracking-widest text-slate-900 dark:text-white mb-2">Multi-view Empty</h3>
						<p class="text-sm text-slate-500 dark:text-zinc-500 max-w-xs mx-auto italic">Select up to 8 members from the sidebar to start your command center.</p>
					</div>
				{/if}
			</div>
		</div>

		<!-- Switchable Chat Sidebar -->
		{#if showChat}
			<div 
				class="w-80 border-l border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 flex flex-col"
				transition:fly={{ x: 320, duration: 300 }}
			>
				{#if focusedStream}
					<div class="p-3 border-b border-gray-100 dark:border-zinc-800 flex items-center justify-between bg-slate-50/50 dark:bg-zinc-800/30">
						<div class="flex items-center gap-2 min-w-0">
							<div class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></div>
							<span class="text-[10px] font-black uppercase tracking-widest text-slate-900 dark:text-white truncate">
								Chat: {focusedStream.member?.name}
							</span>
						</div>
					</div>
					<div class="flex-1 overflow-hidden relative flex flex-col">
						{#key focusedStream.room_url_key || focusedStream.live_id || focusedStream.room_id}
							{#if focusedStream.platform === 'showroom'}
								<ShowroomChat roomId={focusedStream.room_id} />
							{:else}
								{#if focusedStreamDetails}
									<IDNChat roomIdentifier={focusedStreamDetails.room_identifier} />
								{:else}
									<div class="flex flex-col items-center justify-center h-full text-center p-8">
										<RefreshCw size={24} class="text-gray-300 animate-spin mb-4" />
										<p class="text-[10px] font-black uppercase tracking-widest text-gray-400">Loading chat...</p>
									</div>
								{/if}
							{/if}
						{/key}
					</div>
				{:else}
					<div class="flex flex-col items-center justify-center h-full text-center p-8">
						<MessageCircle size={32} class="text-gray-300 mb-4" />
						<p class="text-[10px] font-black uppercase tracking-widest text-gray-400">Select a stream to see chat</p>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>

<style>
	:global(body) {
		overflow: hidden;
	}
</style>
