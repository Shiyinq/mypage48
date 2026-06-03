import { liveHistoryApi } from '$lib/apis/liveHistory';
import type {
	LiveHistory,
	LiveHistoryStats,
	MemberLiveHistoryStats,
	GlobalLiveHistory,
	WatchedLiveMemberRankingItem,
	GlobalLiveHistoryStats,
	GlobalLiveMemberRankingItem,
	GlobalSingleMemberLiveHistoryStats
} from '$lib/types/liveHistory';
import { logger } from '$lib/utils/logger';

class LiveHistoryStore {
	// State
	list = $state<LiveHistory[]>([]);
	globalList = $state<GlobalLiveHistory[]>([]);
	overallStats = $state<LiveHistoryStats | null>(null);
	memberStats = $state<Record<string, MemberLiveHistoryStats>>({});
	membersRanking = $state<WatchedLiveMemberRankingItem[]>([]);
	globalStats = $state<GlobalLiveHistoryStats | null>(null);
	globalMembersRanking = $state<GlobalLiveMemberRankingItem[]>([]);
	globalMemberHistory = $state<GlobalLiveHistory[]>([]);
	globalMemberStats = $state<Record<string, GlobalSingleMemberLiveHistoryStats>>({});
	isLoading = $state(false);
	isLoadingGlobalStats = $state(false);
	error = $state<string | null>(null);
	lastUpdated = $state<number>(0);

	globalPagination = $state({
		page: 1,
		limit: 20,
		total: 0,
		total_pages: 1
	});

	pagination = $state({
		current_page: 1,
		per_page: 20,
		total_data: 0,
		last_page: 1,
		next_page: null as number | null
	});

	rankingPagination = $state({
		current_page: 1,
		per_page: 20,
		total_data: 0,
		last_page: 1,
		next_page: null as number | null
	});

	globalRankingPagination = $state({
		current_page: 1,
		per_page: 20,
		total_data: 0,
		last_page: 1,
		next_page: null as number | null
	});

	globalMemberHistoryPagination = $state({
		page: 1,
		limit: 20,
		total: 0,
		total_pages: 1
	});

	currentMemberFilter = $state<string | undefined>(undefined);

	async load(page: number = 1, memberId?: string, force: boolean = false) {
		if (this.isLoading) return;

		// Reset if filter changed or force refresh
		if (this.currentMemberFilter !== memberId || force) {
			this.list = [];
			this.pagination = {
				current_page: 1,
				per_page: 20,
				total_data: 0,
				last_page: 1,
				next_page: null
			};
		}

		try {
			this.isLoading = true;
			this.error = null;
			this.currentMemberFilter = memberId;

			const response = await liveHistoryApi.getWatchedHistory(page, 20, memberId);

			if (page === 1) {
				this.list = response.data;
			} else {
				// Filter out duplicates in case of race conditions
				const newItems = response.data.filter(
					(newItem) => !this.list.some((existingItem) => existingItem._id === newItem._id)
				);
				this.list = [...this.list, ...newItems];
			}

			this.pagination = response.meta;
			this.lastUpdated = Date.now();
		} catch (err: unknown) {
			this.error = (err as Error).message || 'Failed to load live history';
			logger.error('LiveHistoryStore load error:', err);
			throw err;
		} finally {
			this.isLoading = false;
		}
	}

	async loadGlobal(page: number = 1, force: boolean = false) {
		if (this.isLoading) return;

		if (force) {
			this.globalList = [];
			this.globalPagination = {
				page: 1,
				limit: 20,
				total: 0,
				total_pages: 1
			};
		}

		try {
			this.isLoading = true;
			this.error = null;

			const response = await liveHistoryApi.getGlobalHistory(page, 20);

			if (page === 1) {
				this.globalList = response.data;
			} else {
				const newItems = response.data.filter(
					(newItem) => !this.globalList.some((existingItem) => existingItem._id === newItem._id)
				);
				this.globalList = [...this.globalList, ...newItems];
			}

			this.globalPagination = {
				page: response.page,
				limit: response.limit,
				total: response.total,
				total_pages: response.total_pages
			};
			this.lastUpdated = Date.now();
		} catch (e: unknown) {
			logger.error('Failed to load global live history', e);
			this.error = (e as Error).message || 'Failed to load global live history';
		} finally {
			this.isLoading = false;
		}
	}

	async loadOverallStats() {
		try {
			this.overallStats = await liveHistoryApi.getWatchedStats();
		} catch (err) {
			logger.error('Failed to load overall live stats:', err);
		}
	}

	async loadMemberStats(memberId: string) {
		try {
			const stats = await liveHistoryApi.getWatchedMemberStats(memberId);
			this.memberStats[memberId] = stats;
		} catch (err) {
			logger.error(`Failed to load stats for member ${memberId}:`, err);
		}
	}

	async loadMembersRanking(page: number = 1, force: boolean = false) {
		if (this.isLoading) return;

		if (force) {
			this.membersRanking = [];
			this.rankingPagination = {
				current_page: 1,
				per_page: 20,
				total_data: 0,
				last_page: 1,
				next_page: null
			};
		}

		try {
			this.isLoading = true;
			const response = await liveHistoryApi.getWatchedLiveMembersRanking(page, 20);

			if (page === 1) {
				this.membersRanking = response.data;
			} else {
				const newItems = response.data.filter(
					(newItem) =>
						!this.membersRanking.some(
							(existingItem) => existingItem.member_id === newItem.member_id
						)
				);
				this.membersRanking = [...this.membersRanking, ...newItems];
			}
			this.rankingPagination = response.meta;
		} catch (err) {
			logger.error('Failed to load members ranking:', err);
		} finally {
			this.isLoading = false;
		}
	}

	async loadGlobalStats() {
		try {
			this.isLoadingGlobalStats = true;
			this.globalStats = await liveHistoryApi.getGlobalStats();
		} catch (err) {
			logger.error('Failed to load global live stats:', err);
		} finally {
			this.isLoadingGlobalStats = false;
		}
	}

	async loadGlobalMembersRanking(page: number = 1, force: boolean = false) {
		if (this.isLoading) return;

		if (force) {
			this.globalMembersRanking = [];
			this.globalRankingPagination = {
				current_page: 1,
				per_page: 20,
				total_data: 0,
				last_page: 1,
				next_page: null
			};
		}

		try {
			this.isLoading = true;
			const response = await liveHistoryApi.getGlobalMembersRanking(page, 20);

			if (page === 1) {
				this.globalMembersRanking = response.data;
			} else {
				const newItems = response.data.filter(
					(newItem) =>
						!this.globalMembersRanking.some(
							(existingItem) => existingItem.member_id === newItem.member_id
						)
				);
				this.globalMembersRanking = [...this.globalMembersRanking, ...newItems];
			}
			this.globalRankingPagination = response.meta;
		} catch (err) {
			logger.error('Failed to load global members ranking:', err);
		} finally {
			this.isLoading = false;
		}
	}

	async loadGlobalMemberStats(memberId: string) {
		try {
			const stats = await liveHistoryApi.getGlobalMemberStats(memberId);
			this.globalMemberStats[memberId] = stats;
		} catch (err) {
			logger.error(`Failed to load global stats for member ${memberId}:`, err);
		}
	}

	async loadGlobalMemberHistory(memberId: string, page: number = 1, force: boolean = false) {
		if (this.isLoading) return;

		if (force) {
			this.globalMemberHistory = [];
			this.globalMemberHistoryPagination = {
				page: 1,
				limit: 20,
				total: 0,
				total_pages: 1
			};
		}

		try {
			this.isLoading = true;
			const response = await liveHistoryApi.getGlobalMemberHistory(memberId, page, 20);

			if (page === 1) {
				this.globalMemberHistory = response.data;
			} else {
				const newItems = response.data.filter(
					(newItem) =>
						!this.globalMemberHistory.some((existingItem) => existingItem._id === newItem._id)
				);
				this.globalMemberHistory = [...this.globalMemberHistory, ...newItems];
			}

			this.globalMemberHistoryPagination = {
				page: response.page,
				limit: response.limit,
				total: response.total,
				total_pages: response.total_pages
			};
		} catch (err) {
			logger.error('Failed to load global member history:', err);
		} finally {
			this.isLoading = false;
		}
	}

	async updateWatchDuration(
		live_id: string,
		member_id: string,
		member_name: string,
		member_nickname: string | undefined,
		platform: string,
		ping_duration: number,
		live_title?: string
	) {
		try {
			await liveHistoryApi.updateWatchDuration({
				live_id,
				member_id,
				member_name,
				member_nickname,
				platform,
				ping_duration,
				live_title
			});
			// Don't auto-refresh list here to avoid disrupting the UI while playing
			// We'll let the user manually refresh or refresh on page load
		} catch (err) {
			logger.error('Failed to update watch duration:', err);
		}
	}

	reset() {
		this.list = [];
		this.overallStats = null;
		this.memberStats = {};
		this.membersRanking = [];
		this.error = null;
		this.lastUpdated = 0;
		this.pagination = {
			current_page: 1,
			per_page: 20,
			total_data: 0,
			last_page: 1,
			next_page: null
		};
		this.rankingPagination = {
			current_page: 1,
			per_page: 20,
			total_data: 0,
			last_page: 1,
			next_page: null
		};
		this.currentMemberFilter = undefined;
	}
}

export const liveHistoryStore = new LiveHistoryStore();
