import { writable, get, readable } from 'svelte/store';
import { live as liveApi } from '$lib/apis/live';
import type { LiveStatus, LiveStreamingResponse } from '$lib/types';
import { isCacheExpired } from '$lib/utils/cache';
import { logger } from '$lib/utils/logger';

interface LiveState {
	list: LiveStatus[];
	otherLive: LiveStatus[];
	currentStream: LiveStreamingResponse | null;
	error: string | null;
	lastUpdated: number;
}

export const isLiveLoading = writable(false);

function createLiveStore() {
	const initialState: LiveState = {
		list: [],
		otherLive: [],
		currentStream: null,
		error: null,
		lastUpdated: 0
	};

	const { subscribe, set, update } = writable<LiveState>(initialState);

	return {
		subscribe,
		reset: () => {
			update((s) => ({ ...s, currentStream: null, otherLive: [], error: null }));
			isLiveLoading.set(false);
		},

		loadLiveList: async (forceRefresh = false) => {
			const state = get({ subscribe });
			const now = Date.now();

			if (!forceRefresh && state.list.length > 0 && !isCacheExpired(state.lastUpdated)) {
				return;
			}

			update((s) => ({ ...s, error: null }));
			isLiveLoading.set(true);

			try {
				const res = await liveApi.getLiveStatus();
				update((s) => ({
					...s,
					list: res.data || [],
					error: null,
					lastUpdated: now
				}));
			} catch (e) {
				logger.error('Failed to load live status', e);
				update((s) => ({ ...s, error: 'Failed to load live status' }));
			} finally {
				isLiveLoading.set(false);
			}
		},

		loadStream: async (platform: string, id: string) => {
			update((s) => ({ ...s, error: null, currentStream: null }));
			isLiveLoading.set(true);

			try {
				const res = await liveApi.getStreamingUrl(platform, id);
				update((s) => ({
					...s,
					currentStream: res,
					error: null
				}));
			} catch (e) {
				logger.error(`Failed to load stream for ${platform}/${id}`, e);
				update((s) => ({ ...s, error: 'Failed to load stream' }));
				throw e;
			} finally {
				isLiveLoading.set(false);
			}
		},

		refreshStreamInfo: async (platform: string, id: string) => {
			try {
				const res = await liveApi.getStreamingUrl(platform, id);
				update((s) => ({
					...s,
					currentStream: res
				}));
			} catch (e) {
				logger.error(`Failed to refresh stream info for ${platform}/${id}`, e);
				throw e;
			}
		},

		loadOtherLive: async (currentPlatform: string, currentId: string) => {
			try {
				const streams = await liveApi.getLiveList();
				const otherLive = (streams || []).filter((m) => {
					const mId = m.platform === 'showroom' ? m.room_id : m.live_id;
					return !(m.platform === currentPlatform && mId === currentId);
				});
				update((s) => ({ ...s, otherLive }));
			} catch (e) {
				logger.error('Failed to load other live members', e);
			}
		}
	};
}

export const liveStore = createLiveStore();

// Derived Stores
export const liveList = {
	subscribe: (cb: (val: LiveStatus[]) => void) => liveStore.subscribe((val) => cb(val.list))
};

export const currentStream = {
	subscribe: (cb: (val: LiveStreamingResponse | null) => void) =>
		liveStore.subscribe((val) => cb(val.currentStream))
};

export const otherLive = {
	subscribe: (cb: (val: LiveStatus[]) => void) => liveStore.subscribe((val) => cb(val.otherLive))
};

export const liveLoading = isLiveLoading;

export const liveError = {
	subscribe: (cb: (val: string | null) => void) => liveStore.subscribe((val) => cb(val.error))
};

/**
 * A Svelte readable store that updates with the current timestamp every 1000ms.
 * This centralizes the 1-second ticker used across live pages.
 */
export const now = readable(Date.now(), (set) => {
	const interval = setInterval(() => {
		set(Date.now());
	}, 1000);

	return () => {
		clearInterval(interval);
	};
});
