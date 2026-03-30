<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { radioStore, RADIO_CHANNELS, type RadioChannel } from '$lib/stores/radio';

	let player: any;
	let playerElement: HTMLElement;
	let isInitialized = false;

	$: currentChannel = RADIO_CHANNELS.find((c) => c.id === $radioStore.currentChannelId) || RADIO_CHANNELS[0];

	// Sync Store -> YouTube Player: React strictly to play/pause toggle
	let prevIsPlaying = false;
	$: if (player && isInitialized && prevIsPlaying !== $radioStore.isPlaying) {
		prevIsPlaying = $radioStore.isPlaying;
		if ($radioStore.isPlaying) {
			player.playVideo();
		} else {
			player.pauseVideo();
		}
	}

	// Watch for Playlist Changes
	let previousPlaylistId = '';
	$: if (player && isInitialized && currentChannel && previousPlaylistId !== currentChannel.playlistId) {
		previousPlaylistId = currentChannel.playlistId;
		
		// Segera kosongkan track info agar UI menampilkan "Connecting to Station..."
		radioStore.setTrack('', '');
		
		player.loadPlaylist({
			listType: 'playlist',
			list: currentChannel.playlistId,
			index: 0,
			startSeconds: 0
		});

		// Paksa agar statusnya selalu 'play' saat pindah playlist
		if (!$radioStore.isPlaying) {
			radioStore.play();
		}
	}

	$: if (player && isInitialized) {
		player.setVolume($radioStore.isMuted ? 0 : $radioStore.volume);
	}

	// Trigger Next Track (only run once per trigger increment)
	let lastTrigger = 0;
	$: if (player && isInitialized && $radioStore.nextTrackTrigger > lastTrigger) {
		lastTrigger = $radioStore.nextTrackTrigger;
		player.nextVideo();
	}

	function initPlayer() {
		if (typeof window === 'undefined' || !(window as any).YT) return;

		player = new (window as any).YT.Player(playerElement, {
			height: '1',
			width: '1',
			playerVars: {
				listType: 'playlist',
				list: currentChannel.playlistId,
				autoplay: 0,
				controls: 0,
				showinfo: 0,
				rel: 0,
				loop: 1
			},
			events: {
				onReady: (event: any) => {
					isInitialized = true;
					if ($radioStore.isPlaying) {
						event.target.playVideo();
					}
					event.target.setVolume($radioStore.isMuted ? 0 : $radioStore.volume);
				},
				onStateChange: (event: any) => {
					// YT.PlayerState: 
					// -1 = unstarted, 0 = ended, 1 = playing, 2 = paused, 3 = buffering, 5 = video cued
					
					// Update metadata info when we know video is available
					if (event.data === 1 || event.data === 2 || event.data === 3 || event.data === 5) {
						try {
							const videoData = player.getVideoData();
							if (videoData && videoData.video_id) {
								const videoId = videoData.video_id;
								radioStore.setTrack(
									videoData.title || '',
									`https://img.youtube.com/vi/${videoId}/mqdefault.jpg`
								);
							}
						} catch (e) {
							// Ignore API error
						}
					}

					if (event.data === 1) {
						// Memastikan store selaras
						if (!$radioStore.isPlaying) radioStore.play();
					} else if (event.data === 2) {
						// Jika di-pause manual atau auto-paused oleh browser
						if ($radioStore.isPlaying) radioStore.pause();
					} else if (event.data === 5) {
						// Cued (Siap putar). Jika store meminta putar, paksa main.
						if ($radioStore.isPlaying) event.target.playVideo();
					} else if (event.data === 0) {
						// Lagu habis, harusnya auto-next krn kita set loop: 1
						if ($radioStore.isPlaying) event.target.nextVideo();
					}
				}
			}
		});
	}

	let playerElementOuter: HTMLElement;

	onMount(() => {
		previousPlaylistId = currentChannel.playlistId; // Set initial
		
		if (typeof window !== 'undefined') {
			if ((window as any).YT && (window as any).YT.Player) {
				initPlayer();
			} else {
				if (!document.getElementById('youtube-iframe-api')) {
					const tag = document.createElement('script');
					tag.id = 'youtube-iframe-api';
					tag.src = 'https://www.youtube.com/iframe_api';
					const firstScriptTag = document.getElementsByTagName('script')[0];
					if (firstScriptTag && firstScriptTag.parentNode) {
						firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
					} else {
						document.head.appendChild(tag);
					}
				}

				(window as any).onYouTubeIframeAPIReady = () => {
					initPlayer();
				};
			}
		}
	});

	onDestroy(() => {
		if (player) {
			player.destroy();
		}
	});
</script>

<!-- Hidden YouTube Container connected to the Engine -->
<div class="fixed -top-[1000px] left-0 pointer-events-none opacity-0 overflow-hidden" bind:this={playerElementOuter}>
	<div bind:this={playerElement}></div>
</div>
