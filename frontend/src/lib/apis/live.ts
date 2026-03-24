import { client } from './client';

export const live = {
	getLiveStatus: async () => {
		return await client<any>('/jkt48/live');
	},
	getLiveList: async () => {
		const res = await client<any>('/jkt48/live');
		return res.data || [];
	},
	getStreamingUrl: async (platform: string, id: string) => {
		return await client<any>(`/jkt48/live/${platform}/${id}/streaming-url`);
	}
};
