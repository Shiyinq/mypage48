import { client } from './client';
import type {
	LiveHistoryResponse,
	LiveHistoryStats,
	MemberLiveHistoryStats,
	LiveHistoryUpdateRequest
} from '$lib/types/liveHistory';

export const liveHistoryApi = {
	updateWatchDuration: async (data: LiveHistoryUpdateRequest): Promise<void> => {
		await client('/history/lives/update', {
			method: 'POST',
			// eslint-disable-next-line @typescript-eslint/no-explicit-any
			body: data as any
		});
	},

	getHistory: async (
		page: number = 1,
		limit: number = 20,
		memberId?: string
	): Promise<LiveHistoryResponse> => {
		let url = `/history/lives/watched?page=${page}&limit=${limit}`;
		if (memberId) {
			url += `&member_id=${memberId}`;
		}
		return client<LiveHistoryResponse>(url);
	},

	getOverallStats: async (): Promise<LiveHistoryStats> => {
		return client<LiveHistoryStats>('/history/lives/watched/stats');
	},

	getMemberStats: async (memberId: string): Promise<MemberLiveHistoryStats> => {
		return client<MemberLiveHistoryStats>(`/history/lives/watched/members/${memberId}/stats`);
	}
};
