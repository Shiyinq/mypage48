<script lang="ts">
	import { untrack } from 'svelte';
	import { page } from '$app/stores';
	import SEO from '$lib/components/SEO.svelte';
	import { fly, fade } from 'svelte/transition';
	import { spring } from 'svelte/motion';
	import { liveStore, liveList, liveLoading } from '$lib/stores/live.svelte';
	import type { LiveStatus, LiveStreamingResponse } from '$lib/types';
	import type { ReplayVideo } from '$lib/types/replay';
	import { replayStore } from '$lib/stores/replay.svelte';
	import { infiniteScroll } from '$lib/actions/infiniteScroll';
	import { live } from '$lib/apis/live';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import {
		X,
		Plus,
		Volume2,
		VolumeX,
		MessageCircle,
		Search,
		UserPlus,
		RefreshCw,
		Monitor,
		Smartphone,
		Check,
		Camera,
		RotateCw,
		Circle,
		Square,
		Trash2,
		Tv,
		LayoutGrid,
		Ratio,
		Columns3
	} from 'lucide-svelte';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import { OptimizedImage } from '$lib/components/common';
	import ShowroomChat from '$lib/components/live/ShowroomChat.svelte';
	import IDNChat from '$lib/components/live/IDNChat.svelte';
	import ReplayChat from '$lib/components/live/replay/ReplayChat.svelte';
	import MultiPlayer from '$lib/components/live/MultiPlayer.svelte';
	import YoutubeMultiPlayer from '$lib/components/live/YoutubeMultiPlayer.svelte';
	import HlsSettingsDropdown from '$lib/components/live/HlsSettingsDropdown.svelte';
	import { showToast, isImmersive, isAuthenticated } from '$lib/stores';
	import { liveHistoryStore } from '$lib/stores/liveHistory.svelte';
	import PlatformLogo from '$lib/components/live/PlatformLogo.svelte';
	import LiveStats from '$lib/components/live/LiveStats.svelte';
	import AppBackground from '$lib/components/common/AppBackground.svelte';

	const { t } = useTranslation();

	interface Props {
		/** Base path for back-navigation. Use '/jkt48/live' for public, '/live' for theater. */
		basePath?: string;
	}

	let { basePath: _basePath = '/jkt48/live' }: Props = $props();

	// Multi-view State
	export type MultiviewSlot =
		| { type: 'live'; data: LiveStatus; order?: number }
		| { type: 'replay'; data: ReplayVideo; order?: number };
	let slots: MultiviewSlot[] = $state([]);
	let activeTab: 'live' | 'replay' = $state('live');
	let focusedSlotIndex: number = $state(0);
	let focusedStreamDetails: LiveStreamingResponse | null = $state(null);
	let lastLoadedId: string | null = $state(null);
	let showPicker = $state(false);
	let showChat = $state(false);
	let isPortrait = $state(true);
	let searchQuery = $state('');
	let isMobile = $state(false);
	let showLayoutDropdown = $state(false);
	let layoutDropdownRef: HTMLDivElement | undefined = $state();

	// Background Decoration State
	let scrollY = $state(0);
	let mouse = $state(spring({ x: 0, y: 0 }, { stiffness: 0.1, damping: 0.25 }));

	// Update isMobile on mount and resize

	// Update isMobile on mount and resize
	function updateIsMobile() {
		isMobile = window.innerWidth < 768;
	}

	function togglePicker() {
		showPicker = !showPicker;
		if (showPicker && isMobile) showChat = false;
	}

	function toggleChat() {
		showChat = !showChat;
		if (showChat && isMobile) showPicker = false;
	}

	// Drag and Drop State
	let draggedIndex: number | null = $state(null);
	let dragOverIndex: number | null = $state(null);

	// Media State for slots
	let volumes: number[] = $state(Array(8).fill(1));
	let muted: boolean[] = $state(Array(8).fill(false));
	let isRecording: boolean[] = $state(Array(8).fill(false));
	let fillModes: boolean[] = $state(Array(8).fill(false));
	let landscapes: boolean[] = $state(Array(8).fill(false));
	let focusedCurrentTime: number = $state(0);
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	let playerRefs: any[] = $state(Array(8).fill(null));

	let windowWidth = $state(0);
	let windowHeight = $state(0);
	let isEffectiveLandscape = $derived(!isPortrait);

	$effect(() => {
		if (activeTab === 'replay') {
			// Read synchronously so Svelte 5 tracks the dependency
			const currentSearch = searchQuery;
			const timeout = setTimeout(() => {
				replayStore.loadVideos(1, 20, currentSearch);
			}, 300);
			return () => clearTimeout(timeout);
		}
	});

	$effect(() => {
		untrack(() => {
			liveStore.loadLiveList();
			replayStore.loadVideos();
		});
		const interval = setInterval(async () => {
			await liveStore.loadLiveList(true);
			const currentLive = liveList.value;

			let hasGoneOffline = false;
			const indicesToRemove: number[] = [];
			const updatedSlots = slots
				.map((slot, index) => {
					if (slot.type === 'replay') return slot;
					const liveData = slot.data;
					const updated = currentLive.find(
						(l) =>
							(l.platform === liveData.platform && l.room_id === liveData.room_id && l.room_id) ||
							(l.platform === liveData.platform && l.live_id === liveData.live_id && l.live_id)
					);
					if (!updated) {
						hasGoneOffline = true;
						indicesToRemove.push(index);
						showToast(
							t('theater.live.multiview.member_offline', { name: liveData.member?.name }),
							'error'
						);
						return null;
					}
					return { type: 'live', data: { ...liveData, ...updated } } as MultiviewSlot;
				})
				.filter((s): s is MultiviewSlot => s !== null);

			if (hasGoneOffline) {
				const keep = (i: number) => !indicesToRemove.includes(i);
				volumes = volumes.filter((_, i) => keep(i));
				muted = muted.filter((_, i) => keep(i));
				isRecording = isRecording.filter((_, i) => keep(i));
				fillModes = fillModes.filter((_, i) => keep(i));
				landscapes = landscapes.filter((_, i) => keep(i));
				playerRefs = playerRefs.filter((_, i) => keep(i));

				slots = updatedSlots;
				saveSlots();
				if (focusedSlotIndex >= slots.length) {
					setFocusedSlot(Math.max(0, slots.length - 1));
				}
			} else {
				slots = updatedSlots;
			}
		}, 30000);

		// Initial setup
		if (typeof window !== 'undefined') {
			const savedSlots = localStorage.getItem('mypage48_multiview_slots');
			if (savedSlots) {
				try {
					const parsedSlots = JSON.parse(savedSlots);
					const validSlots = parsedSlots.filter(
						(s: Partial<MultiviewSlot>) => s && s.type && s.data
					);
					validSlots.forEach((s: MultiviewSlot, i: number) => {
						if ((s.type === 'live' && s.data.platform === 'idn') || s.type === 'replay')
							fillModes[i] = true;
						else fillModes[i] = false;
						landscapes[i] = false;
						isRecording[i] = false;
						volumes[i] = 1;
						muted[i] = false;
					});
					slots = validSlots;
				} catch (e) {
					console.error('Failed to load saved slots:', e);
				}
			}

			if (window.innerWidth >= 1024) {
				showPicker = true;
				showChat = true;
				const shouldManage = false;
				if (shouldManage) isImmersive.set(true);
				document.body.style.overflow = 'hidden';
			}

			if (window.innerWidth < 768) {
				showPicker = false;
				showChat = false;
				isPortrait = false; // Default to landscape on mobile
			}

			updateIsMobile();

			// Load aspect ratio preference from localStorage
			const savedPortrait = localStorage.getItem('mypage48_multiview_portrait');
			if (savedPortrait !== null && !isMobile) {
				// Only use saved preference if not on mobile, or handle mobile specifically
				isPortrait = savedPortrait === 'true';
			}

			window.addEventListener('resize', updateIsMobile);
		}

		return () => {
			clearInterval(interval);
			if (typeof window !== 'undefined') {
				window.removeEventListener('resize', updateIsMobile);
				// Re-enable body scroll when leaving multiview
				document.body.style.overflow = '';
				const shouldManage = false;
				if (shouldManage) isImmersive.set(false);
			}
		};
	});

	// Heartbeat for live history tracking
	$effect(() => {
		const heartbeatInterval = setInterval(() => {
			if (!isAuthenticated.value) return;

			// Track all active streams in multiview slots
			slots.forEach((slot) => {
				if (slot.type === 'replay') return;
				const liveData = slot.data;
				const platform = liveData.platform || '';
				const liveId = liveData.live_id || liveData.room_url_key || liveData.room_id || '';
				const memberId = liveData.member?.id || liveData.room_url_key || '';
				const memberName = liveData.member?.name || liveData.title || 'Unknown';
				const memberNickname = liveData.member?.nickname || undefined;
				const title = liveData.title;

				if (liveId && platform) {
					liveHistoryStore.updateWatchDuration(
						liveId,
						memberId,
						memberName,
						memberNickname,
						platform,
						30,
						title
					);
				}
			});
		}, 30000);

		return () => {
			clearInterval(heartbeatInterval);
		};
	});

	function saveSlots() {
		localStorage.setItem('mypage48_multiview_slots', JSON.stringify(slots));
	}

	function addSlot(slot: MultiviewSlot) {
		if (slots.length >= 8) return;

		const exists = slots.find((s) => {
			if (s.type === 'live' && slot.type === 'live') {
				return (
					(s.data.platform === slot.data.platform &&
						s.data.room_id === slot.data.room_id &&
						s.data.room_id) ||
					(s.data.platform === slot.data.platform &&
						s.data.live_id === slot.data.live_id &&
						s.data.live_id)
				);
			} else if (s.type === 'replay' && slot.type === 'replay') {
				return s.data?.youtube_id === slot.data?.youtube_id;
			}
			return false;
		});
		if (exists) return;

		const maxOrder = slots.reduce((max, s) => Math.max(max, s.order ?? 0), -1);
		slot.order = maxOrder + 1;

		const newIndex = slots.length;
		if ((slot.type === 'live' && slot.data.platform === 'idn') || slot.type === 'replay') {
			fillModes[newIndex] = true;
		} else {
			fillModes[newIndex] = false;
		}
		landscapes[newIndex] = false;
		isRecording[newIndex] = false;
		muted[newIndex] = false;
		volumes[newIndex] = 1;

		slots = [...slots, slot];
		focusedSlotIndex = slots.length - 1;
		saveSlots();
	}

	function setFocusedSlot(index: number) {
		focusedSlotIndex = index;
	}

	async function loadFocusedDetails(stream: MultiviewSlot) {
		focusedStreamDetails = null; // Clear old info
		if (stream.type === 'replay') return;
		try {
			const platform = stream.data.platform;
			const id =
				platform === 'showroom'
					? stream.data.room_id || stream.data.room_url_key
					: stream.data.live_id || stream.data.room_url_key;
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
		volumes = volumes.filter((_, i) => i !== index);
		muted = muted.filter((_, i) => i !== index);
		isRecording = isRecording.filter((_, i) => i !== index);
		fillModes = fillModes.filter((_, i) => i !== index);
		landscapes = landscapes.filter((_, i) => i !== index);
		playerRefs = playerRefs.filter((_, i) => i !== index);
		saveSlots();
		if (focusedSlotIndex === index) {
			setFocusedSlot(Math.max(0, slots.length - 1));
		} else if (focusedSlotIndex > index) {
			setFocusedSlot(focusedSlotIndex - 1);
		}
	}

	function clearAll() {
		slots = [];
		volumes = [];
		muted = [];
		isRecording = [];
		playerRefs = [];
		fillModes = [];
		landscapes = [];
		saveSlots();
	}

	function handleDragStart(index: number) {
		draggedIndex = index;
	}

	function handleDragOver(e: DragEvent, index: number) {
		e.preventDefault();
		dragOverIndex = index;
	}

	function handleDrop(index: number) {
		if (draggedIndex === null || draggedIndex === index) return;

		// Ensure all slots have an order
		slots.forEach((s, i) => {
			if (s.order === undefined) s.order = i;
		});

		// Sort indices by order to get visual order
		const visualIndices = slots.map((_, i) => i).sort((a, b) => slots[a].order! - slots[b].order!);

		// Find the visual index of dragged and target
		const visualDraggedIdx = visualIndices.indexOf(draggedIndex);
		const visualTargetIdx = visualIndices.indexOf(index);

		// Swap volume, muted, recording, fillMode states
		const tempVol = volumes[draggedIndex];
		volumes[draggedIndex] = volumes[index];
		volumes[index] = tempVol;

		const tempMuted = muted[draggedIndex];
		muted[draggedIndex] = muted[index];
		muted[index] = tempMuted;

		const tempRec = isRecording[draggedIndex];
		isRecording[draggedIndex] = isRecording[index];
		isRecording[index] = tempRec;

		const tempFill = fillModes[draggedIndex];
		fillModes[draggedIndex] = fillModes[index];
		fillModes[index] = tempFill;

		const tempLand = landscapes[draggedIndex];
		landscapes[draggedIndex] = landscapes[index];
		landscapes[index] = tempLand;

		// Perform the insertion in the visual array
		const [movedIdx] = visualIndices.splice(visualDraggedIdx, 1);
		visualIndices.splice(visualTargetIdx, 0, movedIdx);

		// Now reassign order based on the new visual order
		visualIndices.forEach((originalIndex, visualIndex) => {
			slots[originalIndex].order = visualIndex;
		});

		slots = [...slots]; // trigger reactivity
		saveSlots();
	}

	function handleDragEnd() {
		draggedIndex = null;
		dragOverIndex = null;
	}

	let fallbackAvatar = 'https://placehold.co/640x960?text=NO%20IMAGE';

	function handleRoomOffline(index: number, memberName: string) {
		removeMemberFromSlot(index);
		showToast(t('theater.live.multiview.member_offline', { name: memberName }), 'error');
	}
	$effect(() => {
		if (isMobile) {
			// On mobile, if one is toggled on, toggle the other off
			if (showPicker && showChat) {
				// This logic depends on which one was toggled last,
				// but for simplicity, let's just ensure only one is active.
			}
		}
	});
	let activeStreams = $derived(liveList.value);
	let filteredStreams = $derived(
		activeStreams.filter(
			(s) =>
				s.member?.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
				s.title?.toLowerCase().includes(searchQuery.toLowerCase())
		)
	);
	let activeReplays = $derived(replayStore.videos);
	let filteredReplays = $derived(
		activeReplays.filter(
			(v) =>
				v.member.toLowerCase().includes(searchQuery.toLowerCase()) ||
				v.title.toLowerCase().includes(searchQuery.toLowerCase())
		)
	);
	// Auto-initialize first slot if empty and no saved session
	$effect(() => {
		if (
			slots.length === 0 &&
			((liveList.value?.length ?? 0) > 0 || replayStore.videos.length > 0) &&
			typeof localStorage !== 'undefined' &&
			!localStorage.getItem('mypage48_multiview_slots')
		) {
			const firstLive =
				(liveList.value || []).find((l) => l.platform === 'idn') || liveList.value?.[0];
			if (firstLive) {
				slots = [{ type: 'live', data: firstLive }];
				setFocusedSlot(0);
			} else if (replayStore.videos.length > 0) {
				slots = [{ type: 'replay', data: replayStore.videos[0] }];
				setFocusedSlot(0);
			}
		}
	});
	let focusedStream = $derived(slots[focusedSlotIndex]);

	$effect(() => {
		const interval = setInterval(() => {
			if (focusedStream?.type === 'replay' && playerRefs[focusedSlotIndex]) {
				const player = playerRefs[focusedSlotIndex];
				if (typeof player.getCurrentTime === 'function') {
					focusedCurrentTime = player.getCurrentTime();
				}
			}
		}, 500);
		return () => clearInterval(interval);
	});

	$effect(() => {
		if (!liveLoading.value && liveList.value.length === 0 && activeTab === 'live') {
			activeTab = 'replay';
		}
	});
	$effect(() => {
		if (focusedStream) {
			const currentId =
				focusedStream.type === 'live'
					? focusedStream.data?.platform === 'showroom'
						? focusedStream.data?.room_id || focusedStream.data?.room_url_key
						: focusedStream.data?.live_id || focusedStream.data?.room_url_key
					: focusedStream.data?.youtube_id;
			if (currentId !== lastLoadedId) {
				lastLoadedId = currentId;
				loadFocusedDetails(focusedStream);
			}
		} else {
			focusedStreamDetails = null;
			lastLoadedId = null;
		}
	});
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	function isFillEligible(s: any): boolean {
		return (s.type === 'live' && s.data.platform === 'idn') || s.type === 'replay';
	}

	let fillEligibleCount = $derived(slots.filter((s) => isFillEligible(s)).length);
	let idnStreamsCount = $derived(
		slots.filter((s) => s.type === 'live' && s.data.platform === 'idn').length
	);
	let shouldShowGlobalFillToggle = $derived(
		fillEligibleCount > 0 && !(isEffectiveLandscape && idnStreamsCount === 0)
	);
	let isAnyGlobalFillMode = $derived(slots.some((s, i) => isFillEligible(s) && fillModes[i]));

	function toggleGlobalFillMode() {
		let anyOff = false;
		slots.forEach((s, i) => {
			if (isFillEligible(s) && !fillModes[i]) {
				anyOff = true;
			}
		});

		slots.forEach((s, i) => {
			if (isFillEligible(s)) {
				fillModes[i] = anyOff;
			}
		});
	}

	// Responsive grid logic
	let gridClass = $derived(
		isMobile
			? isPortrait
				? 'grid-cols-1'
				: slots.length === 1
					? 'grid-cols-1'
					: 'grid-cols-1 sm:grid-cols-2'
			: isPortrait
				? slots.length === 1
					? 'grid-cols-1 max-w-md mx-auto'
					: slots.length === 2
						? 'grid-cols-2 max-w-4xl mx-auto'
						: slots.length === 3
							? 'grid-cols-3 max-w-6xl mx-auto'
							: 'grid-cols-2 lg:grid-cols-4 max-w-none'
				: slots.length === 1
					? 'grid-cols-1 max-w-7xl mx-auto'
					: slots.length <= 2
						? 'grid-cols-2 max-w-none'
						: slots.length <= 4
							? 'grid-cols-2 max-w-none'
							: 'grid-cols-2 lg:grid-cols-3 max-w-none'
	);
	// Aspect ratio persistence
	import { liveNavbarStore } from '$lib/stores/liveNavbar.svelte';

	$effect(() => {
		if (typeof window !== 'undefined') {
			localStorage.setItem('mypage48_multiview_portrait', String(isPortrait));
		}
	});

	$effect(() => {
		liveNavbarStore.rightSnippet = rightActions;
		return () => {
			if (liveNavbarStore.rightSnippet === rightActions) {
				liveNavbarStore.rightSnippet = undefined;
			}
		};
	});
</script>

{#snippet rightActions()}
	<div class="flex items-center gap-0 md:gap-2 shrink-0 ml-2 md:ml-0">
		<button
			onclick={clearAll}
			class="p-1.5 md:p-2 shrink-0 rounded-lg text-slate-500 hover:bg-red-50 hover:text-red-600 transition-all cursor-pointer"
			title={t('theater.live.multiview.clear_all')}
		>
			<Trash2 size={20} />
		</button>
		{#if isMobile}
			<div class="relative inline-block text-left" bind:this={layoutDropdownRef}>
				<button
					onclick={(e) => {
						e.stopPropagation();
						showLayoutDropdown = !showLayoutDropdown;
					}}
					class="p-1.5 shrink-0 rounded-lg {showLayoutDropdown
						? 'bg-red-50 text-red-600'
						: 'text-slate-500 hover:bg-gray-100 dark:hover:bg-zinc-800'} transition-all cursor-pointer"
					title="Layout Settings"
				>
					<LayoutGrid size={20} />
				</button>

				{#if showLayoutDropdown}
					<div
						in:fly={{ y: -10, duration: 200 }}
						out:fade={{ duration: 150 }}
						class="absolute right-auto left-1/2 -translate-x-1/2 mt-3 bg-white dark:bg-zinc-800 border border-slate-200 dark:border-zinc-700/50 z-50 w-52 rounded-xl overflow-hidden"
					>
						<div class="py-1 flex flex-col">
							<div
								class="px-4 py-2 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-zinc-400 border-b border-slate-100 dark:border-zinc-700/50"
							>
								{t('theater.live.multiview.layout') || 'Layout'}
							</div>

							<button
								onclick={(e) => {
									e.stopPropagation();
									isPortrait = !isPortrait;
									showLayoutDropdown = false;
								}}
								class="w-full cursor-pointer text-left px-4 py-3 text-sm flex items-center gap-3 transition-colors text-slate-700 hover:bg-slate-50 dark:text-zinc-300 dark:hover:bg-zinc-700/50 dark:hover:text-white"
							>
								{#if isPortrait}
									<Monitor size={16} />
									{t('theater.live.multiview.switch_to_landscape')}
								{:else}
									<Smartphone size={16} />
									{t('theater.live.multiview.switch_to_portrait')}
								{/if}
							</button>

							{#if shouldShowGlobalFillToggle}
								<button
									onclick={(e) => {
										e.stopPropagation();
										toggleGlobalFillMode();
										showLayoutDropdown = false;
									}}
									class="w-full cursor-pointer text-left px-4 py-3 text-sm flex items-center gap-3 transition-colors {isAnyGlobalFillMode
										? 'text-red-600 bg-red-50 dark:bg-red-500/10 dark:text-red-500 font-bold'
										: 'text-slate-700 hover:bg-slate-50 dark:text-zinc-300 dark:hover:bg-zinc-700/50 dark:hover:text-white'}"
								>
									{#if isEffectiveLandscape}
										<Columns3 size={16} />
										{t('theater.live.tripleView')}
									{:else}
										<Ratio size={16} />
										{t('theater.live.fillMode')}
									{/if}
								</button>
							{/if}
						</div>
					</div>
				{/if}
			</div>
		{:else}
			<button
				onclick={() => (isPortrait = !isPortrait)}
				class="p-2 shrink-0 rounded-lg text-slate-500 hover:bg-gray-100 dark:hover:bg-zinc-800 transition-all cursor-pointer"
				title={isPortrait
					? t('theater.live.multiview.switch_to_landscape')
					: t('theater.live.multiview.switch_to_portrait')}
			>
				{#if isPortrait}
					<Monitor size={20} />
				{:else}
					<Smartphone size={20} />
				{/if}
			</button>
			{#if shouldShowGlobalFillToggle}
				<button
					onclick={toggleGlobalFillMode}
					class="p-2 shrink-0 rounded-lg {isAnyGlobalFillMode
						? 'bg-red-50 text-red-600'
						: 'text-slate-500 hover:bg-gray-100 dark:hover:bg-zinc-800'} transition-all cursor-pointer"
					title={isEffectiveLandscape
						? 'Toggle Triple Screen for IDN Streams'
						: 'Toggle Fill Mode for IDN Streams'}
				>
					{#if isEffectiveLandscape}
						<Columns3 size={20} />
					{:else}
						<Ratio size={20} />
					{/if}
				</button>
			{/if}
		{/if}
		<button
			onclick={togglePicker}
			class="p-1.5 md:p-2 shrink-0 rounded-lg {showPicker
				? 'bg-red-50 text-red-600'
				: 'text-slate-500 hover:bg-gray-100 dark:hover:bg-zinc-800'} transition-all cursor-pointer"
			title={t('theater.live.multiview.toggle_picker')}
		>
			<UserPlus size={20} />
		</button>
		<button
			onclick={toggleChat}
			class="p-1.5 md:p-2 shrink-0 rounded-lg {showChat
				? 'bg-red-50 text-red-600'
				: 'text-slate-500 hover:bg-gray-100 dark:hover:bg-zinc-800'} transition-all cursor-pointer"
			title={t('theater.live.multiview.toggle_chat')}
		>
			<MessageCircle size={20} />
		</button>
		<div class="w-px h-5 bg-slate-200 dark:bg-zinc-800 mx-1 shrink-0"></div>
		<div class="flex items-center justify-center shrink-0 -ml-1">
			<HlsSettingsDropdown variant="multiview" />
		</div>
	</div>
{/snippet}

<SEO
	title={t('theater.live.multiview.live.seoTitle')}
	path={$page.url.pathname}
	description={t('theater.live.multiview.live.seoDescription')}
	keywords="JKT48 Multi-view, JKT48 Live, JKT48 Showroom, JKT48 IDN Live, Multi Room Live JKT48, Multi View Live JKT48"
/>

<svelte:window
	bind:innerWidth={windowWidth}
	bind:innerHeight={windowHeight}
	onclick={(e) => {
		if (showLayoutDropdown && layoutDropdownRef && !layoutDropdownRef.contains(e.target as Node)) {
			showLayoutDropdown = false;
		}
	}}
/>

<div
	role="presentation"
	class="fixed inset-0 bg-gradient-to-b from-pink-50/50 via-white to-white dark:from-zinc-950 dark:via-zinc-950 dark:to-zinc-900 flex flex-col overflow-hidden z-[9999]"
	onmousemove={(e) => {
		const { clientX, clientY } = e;
		const { innerWidth, innerHeight } = window;
		const x = clientX / innerWidth - 0.5;
		const y = clientY / innerHeight - 0.5;
		mouse.set({ x, y });
	}}
>
	<!-- Background Decor (Stars, Dots, Glows) -->
	<AppBackground hideDecorationsOnMobile={true} interactive={true} bind:mouse bind:scrollY />
	<div class="flex-1 flex overflow-hidden pt-16">
		<!-- Member Picker Sidebar -->
		{#if showPicker}
			<div
				class="fixed md:relative top-14 md:top-0 left-0 w-full md:w-72 h-[calc(100dvh-56px)] md:h-auto border-r border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 flex flex-col z-[5000]"
				transition:fly={{ x: isMobile ? -500 : -288, duration: 300 }}
			>
				<div class="flex items-center gap-4 px-4 pt-4">
					<button
						onclick={() => (activeTab = 'live')}
						class="flex-1 py-2 text-center text-xs font-bold rounded-t-lg transition-colors border-b-2 cursor-pointer uppercase {activeTab ===
						'live'
							? 'border-red-500 text-red-500'
							: 'border-transparent text-gray-400 hover:text-gray-600'}"
					>
						{t('nav.live')} ({activeStreams.length})
					</button>
					<button
						onclick={() => (activeTab = 'replay')}
						class="flex-1 py-2 text-center text-xs font-bold rounded-t-lg transition-colors border-b-2 cursor-pointer uppercase {activeTab ===
						'replay'
							? 'border-red-500 text-red-500'
							: 'border-transparent text-gray-400 hover:text-gray-600'}"
					>
						{t('replay.nav')} ({activeReplays.length})
					</button>
				</div>
				<div class="p-4 border-b border-gray-100 dark:border-zinc-800 flex items-center gap-2">
					<div class="relative flex-1">
						<Search class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
						<input
							type="text"
							bind:value={searchQuery}
							placeholder={t('theater.live.multiview.search_placeholder')}
							class="w-full pl-9 pr-4 py-3 md:py-2 bg-gray-50 dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 rounded-xl text-sm md:text-xs focus:ring-2 focus:ring-red-500 outline-none"
						/>
					</div>
					{#if isMobile}
						<button
							onclick={togglePicker}
							class="p-2 text-slate-500 hover:bg-gray-100 dark:hover:bg-zinc-800 rounded-lg cursor-pointer"
						>
							<X size={20} />
						</button>
					{/if}
				</div>
				<div class="flex-1 overflow-y-auto p-2 space-y-1 relative">
					{#if activeTab === 'live' && liveLoading.value && activeStreams.length === 0}
						{#each Array(6)}
							<div class="h-12 bg-gray-50 dark:bg-zinc-800/50 rounded-xl animate-pulse"></div>
						{/each}
					{:else if activeTab === 'replay' && replayStore.loading && activeReplays.length === 0}
						{#each Array(6)}
							<div class="h-12 bg-gray-50 dark:bg-zinc-800/50 rounded-xl animate-pulse"></div>
						{/each}
					{:else if activeTab === 'live'}
						{#each filteredStreams as stream}
							{@const selectedIndex = slots.findIndex(
								(s) =>
									s.type === 'live' &&
									((s.data.platform === stream.platform &&
										s.data.room_id === stream.room_id &&
										stream.room_id) ||
										(s.data.platform === stream.platform &&
											s.data.live_id === stream.live_id &&
											stream.live_id))
							)}
							{@const isSelected = selectedIndex !== -1}
							<button
								onclick={() =>
									isSelected
										? removeMemberFromSlot(selectedIndex)
										: addSlot({ type: 'live', data: stream })}
								class="w-full flex items-center gap-3 p-2 rounded-xl border transition-all text-left group cursor-pointer {isSelected
									? 'bg-red-50 dark:bg-red-500/10 border-red-200 dark:border-red-500/20 shadow-inner'
									: 'border-transparent hover:border-red-500/20 hover:bg-slate-50 dark:hover:bg-zinc-800/50'}"
							>
								<div class="relative shrink-0">
									<OptimizedImage
										src={getExternalMediaUrl(stream.member?.img) || fallbackAvatar}
										alt={stream.member?.name || 'Member'}
										class="w-10 h-10 rounded-lg object-cover {isSelected
											? 'grayscale-[0.5] opacity-80'
											: ''}"
									/>
									<div class="absolute -bottom-1 -right-1">
										<PlatformLogo platform={stream.platform} size="xs" />
									</div>
								</div>
								<div class="flex-1 min-w-0">
									<div
										class="font-bold text-xs text-slate-900 dark:text-white truncate {isSelected
											? 'opacity-50'
											: ''}"
									>
										{stream.member?.name}
									</div>
									<div
										class="text-[10px] text-zinc-500 dark:text-zinc-400 truncate mb-0.5 {isSelected
											? 'opacity-50'
											: ''}"
									>
										{stream.title || t('theater.live.multiview.live_status')}
									</div>
									<LiveStats
										view_num={stream.view_num}
										start_at={stream.start_at}
										variant="compact"
										showLabel={true}
										className={isSelected ? 'opacity-50' : ''}
									/>
								</div>
								{#if isSelected}<Check size={16} class="text-red-500" />{:else}<Plus
										size={16}
										class="text-gray-300 group-hover:text-red-500 transition-colors"
									/>{/if}
							</button>
						{/each}
					{:else}
						{#each filteredReplays as replay}
							{@const selectedIndex = slots.findIndex(
								(s) => s.type === 'replay' && s.data?.youtube_id === replay.youtube_id
							)}
							{@const isSelected = selectedIndex !== -1}
							<button
								onclick={() =>
									isSelected
										? removeMemberFromSlot(selectedIndex)
										: addSlot({ type: 'replay', data: replay })}
								class="w-full flex items-center gap-3 p-2 rounded-xl border transition-all text-left group cursor-pointer {isSelected
									? 'bg-red-50 dark:bg-red-500/10 border-red-200 dark:border-red-500/20 shadow-inner'
									: 'border-transparent hover:border-red-500/20 hover:bg-slate-50 dark:hover:bg-zinc-800/50'}"
							>
								<div class="relative shrink-0">
									<OptimizedImage
										src={`https://img.youtube.com/vi/${replay.youtube_id}/mqdefault.jpg`}
										alt={replay.member || 'Member'}
										class="w-10 h-10 rounded-lg object-cover {isSelected
											? 'grayscale-[0.5] opacity-80'
											: ''}"
									/>
									<div class="absolute -bottom-1 -right-1">
										<PlatformLogo platform="youtube" size="xs" />
									</div>
								</div>
								<div class="flex-1 min-w-0">
									<div
										class="font-bold text-xs text-slate-900 dark:text-white truncate {isSelected
											? 'opacity-50'
											: ''}"
									>
										{replay.member}
									</div>
									<div
										class="text-[10px] text-zinc-500 dark:text-zinc-400 truncate mb-0.5 {isSelected
											? 'opacity-50'
											: ''}"
									>
										{replay.title}
									</div>
									<div class="text-[10px] font-bold text-gray-400 {isSelected ? 'opacity-50' : ''}">
										{replay.date}
									</div>
								</div>
								{#if isSelected}<Check size={16} class="text-red-500" />{:else}<Plus
										size={16}
										class="text-gray-300 group-hover:text-red-500 transition-colors"
									/>{/if}
							</button>
						{/each}
						{#if activeTab === 'replay' && replayStore.pagination.next_page}
							<div
								use:infiniteScroll
								onintersect={() => replayStore.loadMore(20, searchQuery)}
								class="w-full py-4 flex items-center justify-center shrink-0"
							>
								<div
									class="w-5 h-5 rounded-full border-2 border-red-500 border-t-transparent animate-spin"
								></div>
							</div>
						{/if}
					{/if}
				</div>

				{#if activeTab === 'live' && !liveLoading.value && (activeStreams.length === 0 || filteredStreams.length === 0)}
					<div
						class="absolute inset-0 flex flex-col items-center justify-center text-center p-8 pointer-events-none z-0"
						in:fade
					>
						<Tv size={32} class="text-gray-300 mb-4" />
						<p class="text-[10px] font-black uppercase tracking-widest text-gray-400">
							{activeStreams.length === 0
								? t('theater.live.multiview.no_live_members')
								: t('theater.live.multiview.no_search_results')}
						</p>
					</div>
				{:else if activeTab === 'replay' && !replayStore.loading && (activeReplays.length === 0 || filteredReplays.length === 0)}
					<div
						class="absolute inset-0 flex flex-col items-center justify-center text-center p-8 pointer-events-none z-0"
						in:fade
					>
						<Tv size={32} class="text-gray-300 mb-4" />
						<p class="text-[10px] font-black uppercase tracking-widest text-gray-400">
							No replays found
						</p>
					</div>
				{/if}
			</div>
		{/if}

		<!-- Main Grid Area -->
		<div class="flex-1 bg-transparent p-2 md:p-4 overflow-y-auto">
			<div class="grid {gridClass} gap-2 md:gap-6 h-fit transition-all duration-500 pb-20">
				{#each slots as slot, i (slot.type === 'live' ? slot.data?.platform + '-' + (slot.data?.live_id || slot.data?.room_id || slot.data?.room_url_key) : slot.data?.youtube_id)}
					<div
						class="relative flex items-center justify-center w-full h-full"
						style="order: {slot.order ?? i};"
					>
						<div
							class="relative {isEffectiveLandscape
								? 'aspect-video'
								: 'aspect-[9/16]'} mx-auto bg-white dark:bg-zinc-900 rounded-2xl overflow-hidden border {focusedSlotIndex ===
							i
								? 'border-red-500 ring-2 ring-red-500/50'
								: 'border-gray-200 dark:border-zinc-800'} {dragOverIndex === i
								? 'opacity-50 border-dashed border-red-400 scale-[0.98]'
								: ''} {draggedIndex === i
								? 'opacity-20 translate-y-2'
								: ''} group shadow-sm transition-all hover:shadow-md text-left cursor-pointer transition-[aspect-ratio,transform,opacity] duration-500"
							style="width: min(100%, calc((100dvh - 140px) * {isEffectiveLandscape
								? 16 / 9
								: 9 / 16}));"
							draggable="true"
							ondragstart={() => handleDragStart(i)}
							ondragover={(e) => handleDragOver(e, i)}
							ondrop={() => handleDrop(i)}
							ondragend={handleDragEnd}
							onclick={() => setFocusedSlot(i)}
							onkeydown={(e) => e.key === 'Enter' && setFocusedSlot(i)}
							role="button"
							tabindex="0"
							aria-label={t('theater.live.multiview.focus_member', {
								name: slot.type === 'live' ? slot.data.member?.name : slot.data.member
							})}
						>
							<div class="absolute inset-0 z-0">
								{#if slot.type === 'live'}
									<MultiPlayer
										bind:this={playerRefs[i]}
										bind:isRecording={isRecording[i]}
										platform={slot.data.platform}
										id={slot.data.platform === 'showroom'
											? slot.data.room_id || slot.data.room_url_key
											: slot.data.live_id || slot.data.room_url_key}
										roomIdentifier={slot.data.room_url_key}
										volume={volumes[i] || 1}
										muted={muted[i]}
										isFillMode={fillModes[i]}
										onLandscapeChange={(val) => {
											landscapes[i] = val;
										}}
										onoffline={() => handleRoomOffline(i, slot.data.member?.name || 'Member')}
									/>
								{:else}
									<YoutubeMultiPlayer
										bind:this={playerRefs[i]}
										id={slot.data?.youtube_id}
										volume={volumes[i] || 1}
										muted={muted[i]}
										controls={true}
										isFillMode={fillModes[i] && !isEffectiveLandscape}
									/>
									{#if focusedSlotIndex !== i || draggedIndex !== null}
										<!-- Intercept clicks so user can click anywhere on unfocused video to focus it, and catch drag events over iframes -->
										<div class="absolute inset-0 z-10 cursor-pointer bg-transparent"></div>
									{/if}
								{/if}
							</div>

							<!-- Slot Header (Overlay) -->
							<div
								class="absolute inset-x-0 top-0 p-3 flex items-center justify-between opacity-0 group-hover:opacity-100 group-focus:opacity-100 group-focus-within:opacity-100 transition-opacity z-20 {slot.type ===
								'live'
									? 'bg-gradient-to-b from-black/60 to-transparent'
									: ''} pointer-events-none"
							>
								{#if slot.type === 'live'}
									<div class="flex items-center gap-2 flex-1 min-w-0 pr-2 pointer-events-auto">
										<OptimizedImage
											src={getExternalMediaUrl(slot.data.member?.img) || fallbackAvatar}
											alt={slot.data.member?.name || 'Member'}
											class="w-8 h-8 rounded-lg object-cover border border-white/20 shadow-lg shrink-0"
										/>
										<div class="flex flex-col min-w-0">
											<span
												class="text-[10px] font-black text-white uppercase tracking-wider truncate drop-shadow-md"
												>{slot.data.member?.name}</span
											>
											<LiveStats
												view_num={slot.data.view_num}
												start_at={slot.data.start_at}
												variant="overlay"
												className="mt-0.5"
											/>
										</div>
									</div>
								{:else}
									<div class="flex-1"></div>
								{/if}
								<button
									onclick={(e) => {
										e.stopPropagation();
										removeMemberFromSlot(i);
									}}
									class="w-8 h-8 shrink-0 rounded-xl bg-red-500 hover:bg-red-600 text-white flex items-center justify-center transition-all shadow-lg cursor-pointer pointer-events-auto {slot.type !==
									'live'
										? 'order-first'
										: ''}"
									aria-label={t('theater.live.multiview.remove_stream')}
								>
									<X size={14} />
								</button>
							</div>

							<!-- Slot Controls (Bottom Overlay) -->
							{#if slot.type === 'live' || slot.type === 'replay'}
								<div
									class="absolute inset-x-0 bottom-0 p-2 sm:p-3 flex flex-wrap items-center justify-between gap-y-2 opacity-0 group-hover:opacity-100 group-focus:opacity-100 group-focus-within:opacity-100 transition-opacity z-20 bg-gradient-to-t from-black/60 to-transparent"
								>
									<div class="flex items-center group/volume relative w-8 h-8">
										<button
											class="w-8 h-8 rounded-xl bg-white/10 backdrop-blur-md text-white flex items-center justify-center hover:bg-white/20 transition-all shadow-lg z-10 cursor-pointer relative"
											onclick={(e) => {
												e.stopPropagation();
												muted[i] = !muted[i];
												muted = muted; // Trigger reactivity
											}}
											aria-label={muted[i] || volumes[i] === 0
												? t('theater.live.multiview.unmute')
												: t('theater.live.multiview.mute')}
										>
											{#if muted[i] || volumes[i] === 0}<VolumeX size={16} />{:else}<Volume2
													size={16}
												/>{/if}
										</button>
										<div
											class="absolute bottom-4 left-0 hidden md:flex h-0 group-hover/volume:h-28 w-8 overflow-hidden transition-all duration-500 bg-white/10 backdrop-blur-md rounded-t-xl z-0 items-end justify-center"
										>
											<div class="w-8 h-28 flex items-center justify-center pb-4">
												<input
													type="range"
													min="0"
													max="1"
													step="0.01"
													value={volumes[i]}
													oninput={(e) => {
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
													onclick={(e) => e.stopPropagation()}
													class="w-20 h-1 accent-white cursor-pointer origin-center -rotate-90"
												/>
											</div>
										</div>
									</div>

									<div class="flex flex-wrap items-center justify-end gap-1 sm:gap-2">
										<!-- Rotate Button -->
										<button
											class="w-8 h-8 rounded-xl bg-white/10 backdrop-blur-md text-white flex items-center justify-center hover:bg-zinc-600 hover:scale-105 transition-all shadow-lg grayscale hover:grayscale-0 group/rot cursor-pointer"
											onclick={(e) => {
												e.stopPropagation();
												playerRefs[i]?.rotateVideo();
											}}
											title={t('theater.live.rotate') || 'Rotate Video'}
										>
											<RotateCw
												size={16}
												class="group-hover/rot:rotate-90 transition-transform duration-300"
											/>
										</button>

										{#if slot.type === 'live' || !isEffectiveLandscape}
											<button
												class="w-8 h-8 rounded-xl {fillModes[i]
													? 'bg-white text-black'
													: 'bg-white/10 backdrop-blur-md grayscale hover:grayscale-0 hover:bg-white hover:text-black text-white'} flex items-center justify-center hover:scale-105 transition-all shadow-lg group/fill cursor-pointer"
												onclick={(e) => {
													e.stopPropagation();
													fillModes[i] = !fillModes[i];
												}}
												title={fillModes[i]
													? landscapes[i]
														? t('theater.live.exitTripleView')
														: t('theater.live.exitFillMode')
													: landscapes[i]
														? t('theater.live.tripleView')
														: t('theater.live.fillMode')}
											>
												{#if landscapes[i]}
													<Columns3 size={16} />
												{:else}
													<Ratio size={16} />
												{/if}
											</button>
										{/if}
										{#if slot.type === 'live'}
											<button
												class="w-8 h-8 rounded-xl bg-white/10 backdrop-blur-md text-white flex items-center justify-center hover:bg-blue-600 hover:scale-105 transition-all shadow-lg grayscale hover:grayscale-0 group/cam cursor-pointer"
												onclick={(e) => {
													e.stopPropagation();
													playerRefs[i]?.takeScreenshot(slot.data.member?.name);
												}}
												title={t('theater.live.multiview.take_screenshot')}
											>
												<Camera
													size={16}
													class="group-hover/cam:rotate-12 transition-transform duration-300"
												/>
											</button>
											<button
												class="w-8 h-8 rounded-xl {isRecording[i]
													? 'bg-red-600 animate-pulse'
													: 'bg-white/10 backdrop-blur-md grayscale hover:grayscale-0 hover:bg-red-600'} text-white flex items-center justify-center hover:scale-105 transition-all shadow-lg group/rec cursor-pointer"
												onclick={(e) => {
													e.stopPropagation();
													playerRefs[i]?.toggleRecording(slot.data.member?.name);
												}}
												title={isRecording[i]
													? t('theater.live.multiview.stop_recording')
													: t('theater.live.multiview.start_recording')}
											>
												{#if isRecording[i]}<Square size={14} fill="currentColor" />{:else}<Circle
														size={14}
														fill="currentColor"
														class="text-red-500 group-hover/rec:scale-110 transition-transform"
													/>{/if}
											</button>
										{/if}
									</div>
								</div>
							{/if}
						</div>
					</div>
				{/each}

				{#if slots.length === 0}
					<div class="col-span-full py-20 flex flex-col items-center justify-center text-center">
						<div
							class="w-20 h-20 rounded-3xl bg-white dark:bg-zinc-900 border border-dashed border-gray-200 dark:border-zinc-800 flex items-center justify-center mb-6 shadow-sm"
						>
							<LayoutGrid size={32} class="text-gray-300" />
						</div>
						<h3
							class="text-xl font-black uppercase tracking-widest text-slate-900 dark:text-white mb-2"
						>
							{t('theater.live.multiview.empty_title')}
						</h3>
						<p class="text-sm text-slate-500 dark:text-zinc-500 max-w-xs mx-auto italic mb-6">
							{t('theater.live.multiview.empty_description')}
						</p>
						{#if isMobile}
							<button
								onclick={togglePicker}
								class="px-6 py-3 bg-red-500 hover:bg-red-600 text-white text-sm font-bold rounded-xl shadow-sm active:scale-95 transition-all flex items-center gap-2 cursor-pointer uppercase tracking-wider"
							>
								<UserPlus size={18} />
								{t('theater.live.multiview.select_member') || 'Select Member'}
							</button>
						{/if}
					</div>
				{/if}
			</div>
		</div>

		<!-- Switchable Chat Sidebar -->
		{#if showChat}
			<div
				class="fixed md:relative top-14 md:top-0 right-0 w-full md:w-80 h-[calc(100dvh-56px)] md:h-auto border-l border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 flex flex-col z-[5000]"
				transition:fly={{ x: isMobile ? 500 : 320, duration: 300 }}
			>
				{#if focusedStream}
					{#if focusedStream.type === 'live'}
						<div
							class="p-3 border-b border-gray-100 dark:border-zinc-800 flex items-center justify-between bg-slate-50/50 dark:bg-zinc-800/30"
						>
							<div class="flex items-center gap-2 min-w-0">
								<div class="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></div>
								<span
									class="text-[10px] font-black uppercase tracking-widest text-slate-900 dark:text-white truncate"
								>
									{t('theater.live.multiview.chat_with', { name: focusedStream.data.member?.name })}
								</span>
							</div>
							{#if isMobile}
								<button
									onclick={toggleChat}
									class="p-1 text-slate-500 hover:bg-gray-100 dark:hover:bg-zinc-800 rounded-lg cursor-pointer"
								>
									<X size={20} />
								</button>
							{/if}
						</div>
					{/if}
					<div class="flex-1 overflow-hidden relative flex flex-col">
						{#if focusedStream.type === 'live'}
							{#key focusedStream.data.room_url_key || focusedStream.data.live_id || focusedStream.data.room_id}
								{#if focusedStream.data.platform === 'showroom' && focusedStream.data.room_id}
									<ShowroomChat roomId={focusedStream.data.room_id} />
								{:else if focusedStreamDetails}
									<IDNChat roomIdentifier={focusedStreamDetails?.room_identifier || ''} />
								{:else}
									<div class="flex flex-col items-center justify-center h-full text-center p-8">
										<RefreshCw size={24} class="text-gray-300 animate-spin mb-4" />
										<p class="text-[10px] font-black uppercase tracking-widest text-gray-400">
											{t('theater.live.multiview.loading_chat')}
										</p>
									</div>
								{/if}
							{/key}
						{:else if focusedStream.data.srt_file || focusedStream.data.live_id}
							<div class="flex-1 overflow-hidden relative flex flex-col">
								<ReplayChat
									srtFile={focusedStream.data.srt_file || focusedStream.data.live_id || ''}
									currentTime={focusedCurrentTime}
									memberName={focusedStream.data.member}
								/>
							</div>
						{:else}
							<div class="flex flex-col items-center justify-center h-full text-center p-8">
								<MessageCircle size={32} class="text-gray-300 mb-4" />
								<p class="text-[10px] font-black uppercase tracking-widest text-gray-400">
									{t('replay.chat.notAvailable')}
								</p>
							</div>
						{/if}
					</div>
				{:else}
					<div class="flex flex-col items-center justify-center h-full text-center p-8">
						<MessageCircle size={32} class="text-gray-300 mb-4" />
						<p class="text-[10px] font-black uppercase tracking-widest text-gray-400">
							{t('theater.live.multiview.select_stream_to_chat')}
						</p>
					</div>
				{/if}
			</div>
		{/if}
	</div>
</div>
