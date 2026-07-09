import { replayApi } from '$lib/apis/replay';
import type { ReplayVideo } from '$lib/types/replay';
import { createRequestDedup } from '$lib/utils/requestDedup';

const REPLAY_CACHE_TTL = 5 * 60 * 1000;

export type ReplaySource = 'jeketibots' | 'mypage48';

interface ReplayState {
	videos: Record<ReplaySource, ReplayVideo[]>;
	currentSource: ReplaySource;
	loading: boolean;
	error: string | null;
	lastUpdated: Record<ReplaySource, number>;
}

const state = $state<ReplayState>({
	videos: { jeketibots: [], mypage48: [] },
	currentSource: 'mypage48',
	loading: true,
	error: null,
	lastUpdated: { jeketibots: 0, mypage48: 0 }
});

const dedup = createRequestDedup();

function createReplayStore() {
	return {
		get videos() {
			return state.videos[state.currentSource];
		},
		get currentSource() {
			return state.currentSource;
		},
		get loading() {
			return state.loading;
		},
		get error() {
			return state.error;
		},
		loadVideos: async (source: ReplaySource = 'mypage48', force = false) => {
			state.currentSource = source;
			if (
				!force &&
				state.videos[source].length > 0 &&
				Date.now() - state.lastUpdated[source] < REPLAY_CACHE_TTL
			) {
				return;
			}

			return dedup.execute(`replay-videos-${source}`, async () => {
				try {
					state.loading = true;
					state.error = null;
					let fetchedVideos: ReplayVideo[];
					if (source === 'mypage48') {
						fetchedVideos = await replayApi.getVideos();
					} else {
						fetchedVideos = await replayApi.getJeketiBotsVideos();
					}
					state.videos[source] = fetchedVideos;
					state.lastUpdated[source] = Date.now();
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
