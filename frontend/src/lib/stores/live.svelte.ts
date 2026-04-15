import { live as liveApi } from '$lib/apis/live';
import type { LiveStatus, LiveStreamingResponse } from '$lib/types';
import { isCacheExpired } from '$lib/utils/cache';
import { logger } from '$lib/utils/logger';

/**
 * Live store - migrated to Svelte 5 Shared Rune State.
 * Manages live stream listings, current stream data, and the global clock.
 */

interface LiveState {
	list: LiveStatus[];
	otherLive: LiveStatus[];
	currentStream: LiveStreamingResponse | null;
	error: string | null;
	lastUpdated: number;
	isLoading: boolean;
}

const initialState: LiveState = {
	list: [],
	otherLive: [],
	currentStream: null,
	error: null,
	lastUpdated: 0,
	isLoading: false
};

const state = $state<LiveState>(initialState);

// Centralized ticker for the global 'now' time
let currentTime = $state(Date.now());
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const ticker = setInterval(() => {
	currentTime = Date.now();
}, 1000);

function createLiveStore() {
	return {
		get list() {
			return state.list;
		},
		get otherLive() {
			return state.otherLive;
		},
		get currentStream() {
			return state.currentStream;
		},
		get error() {
			return state.error;
		},
		get lastUpdated() {
			return state.lastUpdated;
		},
		get isLoading() {
			return state.isLoading;
		},

		reset: () => {
			state.currentStream = null;
			state.otherLive = [];
			state.error = null;
			state.isLoading = false;
		},

		loadLiveList: async (forceRefresh = false) => {
			const nowVal = Date.now();
			if (!forceRefresh && state.list.length > 0 && !isCacheExpired(state.lastUpdated)) {
				return;
			}

			state.error = null;
			state.isLoading = true;

			try {
				const res = await liveApi.getLiveStatus();
				state.list = res.data || [];
				state.error = null;
				state.lastUpdated = nowVal;
			} catch (e) {
				logger.error('Failed to load live status', e);
				state.error = 'Failed to load live status';
			} finally {
				state.isLoading = false;
			}
		},

		loadStream: async (platform: string, id: string) => {
			state.error = null;
			state.currentStream = null;
			state.isLoading = true;

			try {
				const res = await liveApi.getStreamingUrl(platform, id);
				state.currentStream = res;
				state.error = null;
			} catch (e) {
				logger.error(`Failed to load stream for ${platform}/${id}`, e);
				state.error = 'Failed to load stream';
				throw e;
			} finally {
				state.isLoading = false;
			}
		},

		refreshStreamInfo: async (platform: string, id: string) => {
			try {
				const res = await liveApi.getStreamingUrl(platform, id);
				state.currentStream = res;
			} catch (e) {
				logger.error(`Failed to refresh stream info for ${platform}/${id}`, e);
				throw e;
			}
		},

		loadOtherLive: async (currentPlatform: string, currentId: string) => {
			try {
				const streams = await liveApi.getLiveList();
				state.otherLive = (streams || []).filter((m) => {
					const mId = m.platform === 'showroom' ? m.room_id : m.live_id;
					return !(m.platform === currentPlatform && mId === currentId);
				});
			} catch (e) {
				logger.error('Failed to load other live members', e);
			}
		},

		/**
		 * Legacy subscribe method for backward compatibility
		 */
		subscribe: (
			fn: (val: {
				list: LiveStatus[];
				otherLive: LiveStatus[];
				currentStream: LiveStreamingResponse | null;
				error: string | null;
				lastUpdated: number;
			}) => void
		) => {
			fn({
				list: state.list,
				otherLive: state.otherLive,
				currentStream: state.currentStream,
				error: state.error,
				lastUpdated: state.lastUpdated
			});
			$effect.root(() => {
				$effect(() => {
					fn({
						list: state.list,
						otherLive: state.otherLive,
						currentStream: state.currentStream,
						error: state.error,
						lastUpdated: state.lastUpdated
					});
				});
			});
			return () => {};
		}
	};
}

export const liveStore = createLiveStore();

// Derived Stores (Migration Aliases)
export const liveList = {
	get value() {
		return state.list;
	},
	subscribe: (cb: (val: LiveStatus[]) => void) => {
		cb(state.list);
		$effect.root(() => {
			$effect(() => cb(state.list));
		});
		return () => {};
	}
};

export const currentStream = {
	get value() {
		return state.currentStream;
	},
	subscribe: (cb: (val: LiveStreamingResponse | null) => void) => {
		cb(state.currentStream);
		$effect.root(() => {
			$effect(() => cb(state.currentStream));
		});
		return () => {};
	}
};

export const otherLive = {
	get value() {
		return state.otherLive;
	},
	subscribe: (cb: (val: LiveStatus[]) => void) => {
		cb(state.otherLive);
		$effect.root(() => {
			$effect(() => cb(state.otherLive));
		});
		return () => {};
	}
};

export const liveLoading = {
	get value() {
		return state.isLoading;
	},
	subscribe: (fn: (val: boolean) => void) => {
		fn(state.isLoading);
		$effect.root(() => {
			$effect(() => fn(state.isLoading));
		});
		return () => {};
	}
};

export const liveError = {
	get value() {
		return state.error;
	},
	subscribe: (cb: (val: string | null) => void) => {
		cb(state.error);
		$effect.root(() => {
			$effect(() => cb(state.error));
		});
		return () => {};
	}
};

/**
 * Centralized reactive 'now' timestamp.
 */
export const now = {
	get value() {
		return currentTime;
	},
	subscribe: (fn: (val: number) => void) => {
		fn(currentTime);
		$effect.root(() => {
			$effect(() => fn(currentTime));
		});
		return () => {};
	}
};
