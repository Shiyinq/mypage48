import { client } from './client';
import type {
	LiveHistoryResponse,
	LiveHistoryStats,
	MemberLiveHistoryStats,
	LiveHistoryUpdateRequest,
	GlobalLiveHistoryResponse,
	GlobalLiveHistoryStats,
	GlobalLiveMemberRankingResponse,
	GlobalSingleMemberLiveHistoryStats,
	WatchedLiveMemberRankingResponse
} from '$lib/types/liveHistory';

export const liveHistoryApi = {
	getGlobalHistory: async (
		page: number = 1,
		limit: number = 20
	): Promise<GlobalLiveHistoryResponse> => {
		return client<GlobalLiveHistoryResponse>(`/history/lives?page=${page}&limit=${limit}`);
	},

	updateWatchDuration: async (data: LiveHistoryUpdateRequest): Promise<void> => {
		await client('/history/lives/update', {
			method: 'POST',
			// eslint-disable-next-line @typescript-eslint/no-explicit-any
			body: data as any
		});
	},

	getWatchedHistory: async (
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

	getWatchedStats: async (): Promise<LiveHistoryStats> => {
		return client<LiveHistoryStats>('/history/lives/watched/stats');
	},

	getWatchedMemberStats: async (memberId: string): Promise<MemberLiveHistoryStats> => {
		return client<MemberLiveHistoryStats>(`/history/lives/watched/members/${memberId}/stats`);
	},

	getWatchedLiveMembersRanking: async (
		page: number = 1,
		limit: number = 20
	): Promise<WatchedLiveMemberRankingResponse> => {
		return client<WatchedLiveMemberRankingResponse>(
			`/history/lives/watched/members/ranking?page=${page}&limit=${limit}`
		);
	},

	getGlobalStats: async (): Promise<GlobalLiveHistoryStats> => {
		return client<GlobalLiveHistoryStats>('/history/lives/stats');
	},

	getGlobalMembersRanking: async (
		page: number = 1,
		limit: number = 20
	): Promise<GlobalLiveMemberRankingResponse> => {
		return client<GlobalLiveMemberRankingResponse>(
			`/history/lives/members/ranking?page=${page}&limit=${limit}`
		);
	},

	getGlobalMemberHistory: async (
		memberId: string,
		page: number = 1,
		limit: number = 20
	): Promise<GlobalLiveHistoryResponse> => {
		return client<GlobalLiveHistoryResponse>(
			`/history/lives/members/${memberId}?page=${page}&limit=${limit}`
		);
	},

	getGlobalMemberStats: async (memberId: string): Promise<GlobalSingleMemberLiveHistoryStats> => {
		return client<GlobalSingleMemberLiveHistoryStats>(`/history/lives/members/${memberId}/stats`);
	}
};
