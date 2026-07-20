import { client } from './client';
import type { ReplayVideo, ReplayDetailResponse } from '$lib/types/replay';

export const replayApi = {
	getReplayByLiveId: async (liveId: string): Promise<ReplayDetailResponse> => {
		return await client<ReplayDetailResponse>(`/replays/${liveId}`);
	},
	getVideos: async (): Promise<ReplayVideo[]> => {
		return await client<ReplayVideo[]>('/replays');
	},
	getSrt: async (liveId: string): Promise<string> => {
		return await client<string>(`/replays/${liveId}/srt`, { responseType: 'text' });
	}
};
