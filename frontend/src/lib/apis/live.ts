import { client } from './client';
import type {
	LiveStatus,
	LiveStreamingResponse,
	ShowroomCommentLogResponse,
	ShowroomGiftLogResponse,
	ShowroomGiftListResponse
} from '$lib/types';

export const live = {
	getLiveStatus: async () => {
		return await client<{ data: LiveStatus[] }>(`/jkt48/live?t=${Date.now()}`);
	},
	getLiveList: async () => {
		const res = await live.getLiveStatus();
		return res.data || [];
	},
	getScheduledLiveList: async () => {
		const res = await client<{ data: LiveStatus[] }>(`/jkt48/live/scheduled?t=${Date.now()}`);
		return res.data || [];
	},
	getStreamingUrl: async (platform: string, id: string) => {
		return await client<LiveStreamingResponse>(
			`/jkt48/live/${platform}/${id}/streaming-url?t=${Date.now()}`
		);
	},
	getShowroomComments: async (roomId: string) => {
		return await client<ShowroomCommentLogResponse>(
			`/jkt48/live/showroom/comments?room_id=${roomId}`
		);
	},
	getShowroomGifts: async (roomId: string) => {
		return await client<ShowroomGiftLogResponse>(`/jkt48/live/showroom/gifts?room_id=${roomId}`);
	},
	getShowroomGiftList: async (roomId: string) => {
		return await client<ShowroomGiftListResponse>(
			`/jkt48/live/showroom/gift-list?room_id=${roomId}`
		);
	}
};
