import { client } from './client';
import type { LiveStatus, LiveStreamingResponse } from '$lib/types';

export const live = {
	getLiveStatus: async () => {
		return await client<{ data: LiveStatus[] }>(`/jkt48/live?t=${Date.now()}`);
	},
	getLiveList: async () => {
		const res = await live.getLiveStatus();
		return res.data || [];
	},
	getStreamingUrl: async (platform: string, id: string) => {
		return await client<LiveStreamingResponse>(
			`/jkt48/live/${platform}/${id}/streaming-url?t=${Date.now()}`
		);
	}
};
