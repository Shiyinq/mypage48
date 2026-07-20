import { replayApi } from '$lib/apis/replay';
import type { ReplayVideo } from '$lib/types/replay';
import { createRequestDedup } from '$lib/utils/requestDedup';

const REPLAY_CACHE_TTL = 5 * 60 * 1000;

interface ReplayState {
	videos: ReplayVideo[];
	loading: boolean;
	error: string | null;
	lastUpdated: number;
}

const state = $state<ReplayState>({
	videos: [],
	loading: true,
	error: null,
	lastUpdated: 0
});

const dedup = createRequestDedup();

function createReplayStore() {
	return {
		get videos() {
			return state.videos;
		},
		get loading() {
			return state.loading;
		},
		get error() {
			return state.error;
		},
		loadVideos: async (force = false) => {
			if (!force && state.videos.length > 0 && Date.now() - state.lastUpdated < REPLAY_CACHE_TTL) {
				return;
			}

			return dedup.execute(`replay-videos-mypage48`, async () => {
				try {
					state.loading = true;
					state.error = null;
					state.videos = await replayApi.getVideos();
					state.lastUpdated = Date.now();
				} catch (e) {
					state.error = (e as Error).message;
					console.error('Failed to load replay videos:', e);
				} finally {
					state.loading = false;
				}
			});
		}
	};
}

export const replayStore = createReplayStore();
