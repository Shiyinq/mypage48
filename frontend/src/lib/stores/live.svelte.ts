import { live as liveApi } from '$lib/apis/live';
import type { LiveStatus, LiveStreamingResponse } from '$lib/types';
import { logger } from '$lib/utils/logger';
import { createRequestDedup } from '$lib/utils/requestDedup';

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
	scheduledList: LiveStatus[];
	scheduledLastUpdated: number;
	isScheduledLoading: boolean;
}

const initialState: LiveState = {
	list: [],
	otherLive: [],
	currentStream: null,
	error: null,
	lastUpdated: 0,
	isLoading: false,
	scheduledList: [],
	scheduledLastUpdated: 0,
	isScheduledLoading: false
};

const state = $state<LiveState>(initialState);
const dedup = createRequestDedup();

// Centralized ticker for the global 'now' time
let currentTime = $state(Date.now());
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const ticker = setInterval(() => {
	currentTime = Date.now();
}, 1000);

const LIVE_CACHE_TTL = 30 * 1000; // 30 seconds TTL for live status & scheduled list

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
		get scheduledList() {
			return state.scheduledList;
		},
		get isScheduledLoading() {
			return state.isScheduledLoading;
		},
		get scheduledLastUpdated() {
			return state.scheduledLastUpdated;
		},

		reset: () => {
			state.currentStream = null;
			state.otherLive = [];
			state.error = null;
			state.isLoading = false;
			dedup.clear();
		},

		loadLiveList: async (forceRefresh = false) => {
			const nowVal = Date.now();
			if (!forceRefresh && state.lastUpdated > 0 && nowVal - state.lastUpdated < LIVE_CACHE_TTL) {
				return;
			}

			// Deduplicate concurrent requests
			const key = `live:${forceRefresh}`;
			return dedup.execute(key, async () => {
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
			});
		},

		loadScheduledList: async (forceRefresh = false) => {
			const nowVal = Date.now();
			if (
				!forceRefresh &&
				state.scheduledLastUpdated > 0 &&
				nowVal - state.scheduledLastUpdated < LIVE_CACHE_TTL
			) {
				return;
			}

			const key = `scheduledLive:${forceRefresh}`;
			return dedup.execute(key, async () => {
				state.isScheduledLoading = true;
				try {
					const data = await liveApi.getScheduledLiveList();
					state.scheduledList = data || [];
					state.scheduledLastUpdated = nowVal;
				} catch (e) {
					logger.error('Failed to load scheduled lives', e);
				} finally {
					state.isScheduledLoading = false;
				}
			});
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

export const scheduledLiveList = {
	get value() {
		return state.scheduledList;
	},
	subscribe: (cb: (val: LiveStatus[]) => void) => {
		cb(state.scheduledList);
		$effect.root(() => {
			$effect(() => cb(state.scheduledList));
		});
		return () => {};
	}
};

export const scheduledLiveLoading = {
	get value() {
		return state.isScheduledLoading;
	},
	subscribe: (fn: (val: boolean) => void) => {
		fn(state.isScheduledLoading);
		$effect.root(() => {
			$effect(() => fn(state.isScheduledLoading));
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
