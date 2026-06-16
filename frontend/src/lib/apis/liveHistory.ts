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
	WatchedLiveMemberRankingResponse,
	PCLiveHistoryResponse
} from '$lib/types/liveHistory';

export const liveHistoryApi = {
	getGlobalHistory: async (
		page: number = 1,
		limit: number = 20,
		startDate?: string,
		endDate?: string
	): Promise<GlobalLiveHistoryResponse> => {
		let url = `/history/lives?page=${page}&limit=${limit}`;
		if (startDate) url += `&start_date=${startDate}`;
		if (endDate) url += `&end_date=${endDate}`;
		return client<GlobalLiveHistoryResponse>(url);
	},

	getPCCollection: async (
		collectionType: 'owned' | 'unowned' | 'all' = 'all',
		page: number = 1,
		limit: number = 20,
		startDate?: string,
		endDate?: string,
		sortBy?: string
	): Promise<PCLiveHistoryResponse> => {
		let url = `/history/lives/pc?collection_type=${collectionType}&page=${page}&limit=${limit}`;
		if (startDate) url += `&start_date=${startDate}`;
		if (endDate) url += `&end_date=${endDate}`;
		if (sortBy) url += `&sort_by=${sortBy}`;
		return client<PCLiveHistoryResponse>(url);
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
		memberId?: string,
		startDate?: string,
		endDate?: string
	): Promise<LiveHistoryResponse> => {
		let url = `/history/lives/watched?page=${page}&limit=${limit}`;
		if (memberId) {
			url += `&member_id=${memberId}`;
		}
		if (startDate) url += `&start_date=${startDate}`;
		if (endDate) url += `&end_date=${endDate}`;
		return client<LiveHistoryResponse>(url);
	},

	getWatchedStats: async (startDate?: string, endDate?: string): Promise<LiveHistoryStats> => {
		let url = '/history/lives/watched/stats?';
		if (startDate) url += `&start_date=${startDate}`;
		if (endDate) url += `&end_date=${endDate}`;
		return client<LiveHistoryStats>(url);
	},

	getWatchedMemberStats: async (
		memberId: string,
		startDate?: string,
		endDate?: string
	): Promise<MemberLiveHistoryStats> => {
		let url = `/history/lives/watched/members/${memberId}/stats?`;
		if (startDate) url += `&start_date=${startDate}`;
		if (endDate) url += `&end_date=${endDate}`;
		return client<MemberLiveHistoryStats>(url);
	},

	getWatchedLiveMembersRanking: async (
		page: number = 1,
		limit: number = 20,
		startDate?: string,
		endDate?: string
	): Promise<WatchedLiveMemberRankingResponse> => {
		let url = `/history/lives/watched/members/ranking?page=${page}&limit=${limit}`;
		if (startDate) url += `&start_date=${startDate}`;
		if (endDate) url += `&end_date=${endDate}`;
		return client<WatchedLiveMemberRankingResponse>(url);
	},

	getGlobalStats: async (startDate?: string, endDate?: string): Promise<GlobalLiveHistoryStats> => {
		let url = '/history/lives/stats';
		const params = new URLSearchParams();
		if (startDate) params.append('start_date', startDate);
		if (endDate) params.append('end_date', endDate);
		const qs = params.toString();
		if (qs) url += `?${qs}`;
		return client<GlobalLiveHistoryStats>(url);
	},

	getGlobalMembersRanking: async (
		page: number = 1,
		limit: number = 20,
		startDate?: string,
		endDate?: string
	): Promise<GlobalLiveMemberRankingResponse> => {
		let url = `/history/lives/members/ranking?page=${page}&limit=${limit}`;
		if (startDate) url += `&start_date=${startDate}`;
		if (endDate) url += `&end_date=${endDate}`;
		return client<GlobalLiveMemberRankingResponse>(url);
	},

	getGlobalMemberHistory: async (
		memberId: string,
		page: number = 1,
		limit: number = 20,
		startDate?: string,
		endDate?: string
	): Promise<GlobalLiveHistoryResponse> => {
		let url = `/history/lives/members/${memberId}?page=${page}&limit=${limit}`;
		if (startDate) url += `&start_date=${startDate}`;
		if (endDate) url += `&end_date=${endDate}`;
		return client<GlobalLiveHistoryResponse>(url);
	},

	getGlobalMemberStats: async (
		memberId: string,
		startDate?: string,
		endDate?: string
	): Promise<GlobalSingleMemberLiveHistoryStats> => {
		let url = `/history/lives/members/${memberId}/stats`;
		const params = new URLSearchParams();
		if (startDate) params.append('start_date', startDate);
		if (endDate) params.append('end_date', endDate);
		const qs = params.toString();
		if (qs) url += `?${qs}`;
		return client<GlobalSingleMemberLiveHistoryStats>(url);
	}
};
