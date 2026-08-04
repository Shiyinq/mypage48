import { replayApi } from '$lib/apis/replay';
import type { ReplayDetailResponse } from '$lib/types/replay';
import { createRequestDedup } from '$lib/utils/requestDedup';

interface LiveHistoryDetailState {
	data: Record<string, ReplayDetailResponse>;
	loading: Record<string, boolean>;
	error: Record<string, string | null>;
}

const state = $state<LiveHistoryDetailState>({
	data: {},
	loading: {},
	error: {}
});

const dedup = createRequestDedup();

function createLiveHistoryDetailStore() {
	return {
		get data() {
			return state.data;
		},
		get loading() {
			return state.loading;
		},
		get error() {
			return state.error;
		},
		loadDetail: async (liveId: string, force = false) => {
			if (!liveId) return null;

			// Return cached data if not forcing and already loaded
			if (!force && state.data[liveId]) {
				// Ensure error state is cleared for cached successful data
				state.error[liveId] = null;
				return state.data[liveId];
			}

			return dedup.execute(`liveDetail:${liveId}`, async () => {
				try {
					state.loading[liveId] = true;
					state.error[liveId] = null;
					const detail = await replayApi.getReplayByLiveId(liveId);
					if (detail) {
						state.data[liveId] = detail;
					}
					return detail;
				} catch (e) {
					state.error[liveId] = (e as Error).message || 'Failed to load replay detail';
					console.error(`Failed to load replay detail for ${liveId}:`, e);
					return null;
				} finally {
					state.loading[liveId] = false;
				}
			});
		}
	};
}

export const liveHistoryDetailStore = createLiveHistoryDetailStore();
