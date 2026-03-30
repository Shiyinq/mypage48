import { writable } from 'svelte/store';

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

function createRadioStore() {
    const { subscribe, set, update } = writable<RadioState>(initialState);

    return {
        subscribe,
        play: () => update(s => ({ ...s, isPlaying: true })),
        pause: () => update(s => ({ ...s, isPlaying: false })),
        toggle: () => update(s => ({ ...s, isPlaying: !s.isPlaying })),
        setChannel: (channelId: string) => update(s => ({ ...s, currentChannelId: channelId, isPlaying: true })),
        setTrack: (title: string, thumbnail: string) => update(s => ({ ...s, currentTrackTitle: title, currentThumbnail: thumbnail })),
        setVolume: (volume: number) => update(s => ({ ...s, volume })),
        setMuted: (isMuted: boolean) => update(s => ({ ...s, isMuted })),
        skip: () => update(s => ({ ...s, nextTrackTrigger: s.nextTrackTrigger + 1 })),
        reset: () => set(initialState)
    };
}

export const radioStore = createRadioStore();
