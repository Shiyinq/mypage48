import { client } from './client';
import type { ReplayDetailResponse, ReplayPaginationResponse } from '$lib/types/replay';

export const replayApi = {
	getReplayByLiveId: async (liveId: string): Promise<ReplayDetailResponse> => {
		return await client<ReplayDetailResponse>(`/replays/${liveId}`);
	},
	getVideos: async (
		page = 1,
		limit = 20,
		search?: string,
		platform?: string,
		member?: string,
		youtubeId?: string
	): Promise<ReplayPaginationResponse> => {
		const query = new URLSearchParams({
			page: page.toString(),
			limit: limit.toString()
		});
		if (search) query.append('search', search);
		if (platform && platform !== 'all') query.append('platform', platform);
		if (member) query.append('member', member);
		if (youtubeId) query.append('youtube_id', youtubeId);

		return await client<ReplayPaginationResponse>(`/replays?${query.toString()}`);
	},
	getSrt: async (liveId: string): Promise<string> => {
		return await client<string>(`/replays/${liveId}/srt`, { responseType: 'text' });
	}
};
