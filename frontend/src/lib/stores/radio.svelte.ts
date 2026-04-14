/**
 * Radio store - migrated to Svelte 5 Shared Rune State.
 * Manages the audio streaming state, channels, and playback control.
 */

export interface RadioChannel {
	id: string;
	name: string;
	playlistId: string;
	description: string;
}

export const RADIO_CHANNELS: RadioChannel[] = [
	{
		id: 'Playlist1',
		name: 'Playlist 1',
		playlistId: 'PLqQ7E8cz91tAIC6gMT04mWW3gWoE8iPK_',
		description: 'JKT48 New Era Special Performance Video'
	},
	{
		id: 'Playlist2',
		name: 'Playlist 2',
		playlistId: 'PLqQ7E8cz91tAW6p6_8a2I20U70_bs12Fm',
		description: 'JKT48 Lyric Video'
	},
	{
		id: 'Playlist3',
		name: 'Playlist 3',
		playlistId: 'PLqQ7E8cz91tAFx55KVX2FvQyxSGderPOO',
		description: '[JKT48 Official Lyric Video] Pertaruhan Cinta'
	}
];

export interface RadioState {
	isPlaying: boolean;
	currentChannelId: string;
	currentTrackTitle: string;
	currentThumbnail: string;
	volume: number;
	isMuted: boolean;
	nextTrackTrigger: number;
}

const initialState: RadioState = {
	isPlaying: false,
	currentChannelId: RADIO_CHANNELS[0].id,
	currentTrackTitle: '',
	currentThumbnail: '',
	volume: 50,
	isMuted: false,
	nextTrackTrigger: 0
};

const state = $state<RadioState>(initialState);

function createRadioStore() {
	return {
		get isPlaying() {
			return state.isPlaying;
		},
		get currentChannelId() {
			return state.currentChannelId;
		},
		get currentTrackTitle() {
			return state.currentTrackTitle;
		},
		get currentThumbnail() {
			return state.currentThumbnail;
		},
		get volume() {
			return state.volume;
		},
		get isMuted() {
			return state.isMuted;
		},
		get nextTrackTrigger() {
			return state.nextTrackTrigger;
		},

		play: () => {
			state.isPlaying = true;
		},
		pause: () => {
			state.isPlaying = false;
		},
		toggle: () => {
			state.isPlaying = !state.isPlaying;
		},
		setChannel: (channelId: string) => {
			state.currentChannelId = channelId;
			state.isPlaying = true;
		},
		setTrack: (title: string, thumbnail: string) => {
			state.currentTrackTitle = title;
			state.currentThumbnail = thumbnail;
		},
		setVolume: (volume: number) => {
			state.volume = volume;
		},
		setMuted: (isMuted: boolean) => {
			state.isMuted = isMuted;
		},
		skip: () => {
			state.nextTrackTrigger += 1;
		},
		reset: () => {
			Object.assign(state, initialState);
		},

		/**
		 * Legacy subscribe method for backward compatibility
		 */
		subscribe: (fn: (val: RadioState) => void) => {
			$effect.root(() => {
				$effect(() => {
					fn(state);
				});
			});
			return () => {};
		}
	};
}

export const radioStore = createRadioStore();
