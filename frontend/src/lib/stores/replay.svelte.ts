import { replayApi } from '$lib/apis/replay';
import type { ReplayVideo } from '$lib/types/replay';

interface ReplayState {
	videos: ReplayVideo[];
	loading: boolean;
	error: string | null;
}

const state = $state<ReplayState>({
	videos: [],
	loading: false,
	error: null
});

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
		loadVideos: async () => {
			try {
				state.loading = true;
				state.error = null;
				state.videos = await replayApi.getVideos();
			} catch (e) {
				state.error = (e as Error).message;
				console.error('Failed to load replay videos:', e);
			} finally {
				state.loading = false;
			}
		}
	};
}

export const replayStore = createReplayStore();
