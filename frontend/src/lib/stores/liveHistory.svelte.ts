import { liveHistoryApi } from '$lib/apis/liveHistory';
import { liveHistoryFilterStore } from '$lib/stores/liveHistoryFilter.svelte';
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
import { createRequestDedup } from '$lib/utils/requestDedup';
import { logger } from '$lib/utils/logger';

class LiveHistoryStore {
	dedup = createRequestDedup();

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
	currentGlobalFilterKey = $state<string>('');
	currentWatchedFilterKey = $state<string>('');
	currentRankingFilterKey = $state<string>('');
	currentGlobalRankingFilterKey = $state<string>('');
	currentGlobalMemberHistoryFilterKey = $state<string>('');

	lastUpdatedWatched = $state<number>(0);
	lastUpdatedGlobal = $state<number>(0);
	lastUpdatedOverallStats = $state<number>(0);
	lastUpdatedGlobalStats = $state<number>(0);
	lastUpdatedMembersRanking = $state<number>(0);
	lastUpdatedGlobalMembersRanking = $state<number>(0);
	lastUpdatedGlobalMemberHistory = $state<number>(0);

	async load(page: number = 1, memberId?: string, force: boolean = false) {
		const range = liveHistoryFilterStore.dateRange;
		const filterKey = JSON.stringify({ memberId, range });

		if (this.currentWatchedFilterKey !== filterKey || force) {
			this.list = [];
			this.pagination = {
				current_page: 1,
				per_page: 20,
				total_data: 0,
				last_page: 1,
				next_page: null
			};
			this.currentWatchedFilterKey = filterKey;
			this.currentMemberFilter = memberId;
		} else if (
			!force &&
			this.lastUpdatedWatched > 0 &&
			page === 1 &&
			Date.now() - this.lastUpdatedWatched < 300000
		) {
			return;
		}

		const cacheKey = `watched-${page}-${filterKey}`;

		return this.dedup.execute(cacheKey, async () => {
			try {
				this.isLoading = true;
				this.error = null;

				const response = await liveHistoryApi.getWatchedHistory(
					page,
					20,
					memberId,
					range?.start,
					range?.end
				);

				if (page === 1) {
					this.list = response.data;
				} else {
					const newItems = response.data.filter(
						(newItem) => !this.list.some((existingItem) => existingItem._id === newItem._id)
					);
					this.list = [...this.list, ...newItems];
				}

				this.pagination = response.meta;
				this.lastUpdatedWatched = Date.now();
			} catch (err: unknown) {
				this.error = (err as Error).message || 'Failed to load live history';
				logger.error('LiveHistoryStore load error:', err);
				throw err;
			} finally {
				this.isLoading = false;
			}
		});
	}

	async loadGlobal(page: number = 1, force: boolean = false) {
		const range = liveHistoryFilterStore.dateRange;
		const filterKey = JSON.stringify({ range });

		if (this.currentGlobalFilterKey !== filterKey || force) {
			this.globalList = [];
			this.globalPagination = {
				page: 1,
				limit: 20,
				total: 0,
				total_pages: 1
			};
			this.currentGlobalFilterKey = filterKey;
		} else if (
			!force &&
			this.lastUpdatedGlobal > 0 &&
			page === 1 &&
			Date.now() - this.lastUpdatedGlobal < 300000
		) {
			return;
		}

		const cacheKey = `globalHistory-${page}-${filterKey}`;

		return this.dedup.execute(cacheKey, async () => {
			try {
				this.isLoading = true;
				this.error = null;

				const response = await liveHistoryApi.getGlobalHistory(page, 20, range?.start, range?.end);

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
				this.lastUpdatedGlobal = Date.now();
			} catch (e: unknown) {
				logger.error('Failed to load global live history', e);
				this.error = (e as Error).message || 'Failed to load global live history';
			} finally {
				this.isLoading = false;
			}
		});
	}

	currentOverallStatsFilterKey = $state<string>('');
	currentGlobalStatsFilterKey = $state<string>('');

	async loadOverallStats(force: boolean = false) {
		const range = liveHistoryFilterStore.dateRange;
		const filterKey = JSON.stringify({ range });

		if (this.currentOverallStatsFilterKey !== filterKey || force) {
			this.currentOverallStatsFilterKey = filterKey;
		} else if (
			!force &&
			this.overallStats !== null &&
			Date.now() - this.lastUpdatedOverallStats < 300000
		) {
			return;
		}

		const key = JSON.stringify({ method: 'loadOverallStats', range });

		return this.dedup.execute(key, async () => {
			try {
				this.overallStats = await liveHistoryApi.getWatchedStats(range?.start, range?.end);
				this.lastUpdatedOverallStats = Date.now();
			} catch (err) {
				logger.error('Failed to load overall live stats:', err);
			}
		});
	}

	async loadMemberStats(memberId: string) {
		const range = liveHistoryFilterStore.dateRange;
		const key = JSON.stringify({ method: 'loadMemberStats', memberId, range });

		return this.dedup.execute(key, async () => {
			try {
				const stats = await liveHistoryApi.getWatchedMemberStats(
					memberId,
					range?.start,
					range?.end
				);
				this.memberStats[memberId] = stats;
			} catch (err) {
				logger.error(`Failed to load stats for member ${memberId}:`, err);
			}
		});
	}

	async loadMembersRanking(page: number = 1, force: boolean = false) {
		const range = liveHistoryFilterStore.dateRange;
		const filterKey = JSON.stringify({ range });

		if (this.currentRankingFilterKey !== filterKey || force) {
			this.membersRanking = [];
			this.rankingPagination = {
				current_page: 1,
				per_page: 20,
				total_data: 0,
				last_page: 1,
				next_page: null
			};
			this.currentRankingFilterKey = filterKey;
		} else if (
			!force &&
			this.lastUpdatedMembersRanking > 0 &&
			page === 1 &&
			Date.now() - this.lastUpdatedMembersRanking < 300000
		) {
			return;
		}

		const cacheKey = `membersRanking-${page}-${filterKey}`;

		return this.dedup.execute(cacheKey, async () => {
			try {
				this.isLoading = true;
				const response = await liveHistoryApi.getWatchedLiveMembersRanking(
					page,
					20,
					range?.start,
					range?.end
				);

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
				this.lastUpdatedMembersRanking = Date.now();
			} catch (err) {
				logger.error('Failed to load members ranking:', err);
			} finally {
				this.isLoading = false;
			}
		});
	}

	async loadGlobalStats(force: boolean = false) {
		const range = liveHistoryFilterStore.dateRange;
		const filterKey = JSON.stringify({ range });

		if (this.currentGlobalStatsFilterKey !== filterKey || force) {
			this.currentGlobalStatsFilterKey = filterKey;
		} else if (
			!force &&
			this.globalStats !== null &&
			Date.now() - this.lastUpdatedGlobalStats < 300000
		) {
			return;
		}

		const key = JSON.stringify({ method: 'loadGlobalStats', range });

		return this.dedup.execute(key, async () => {
			try {
				this.isLoadingGlobalStats = true;
				this.globalStats = await liveHistoryApi.getGlobalStats(range?.start, range?.end);
				this.lastUpdatedGlobalStats = Date.now();
			} catch (err) {
				logger.error('Failed to load global live stats:', err);
			} finally {
				this.isLoadingGlobalStats = false;
			}
		});
	}

	async loadGlobalMembersRanking(page: number = 1, force: boolean = false) {
		const range = liveHistoryFilterStore.dateRange;
		const filterKey = JSON.stringify({ range });

		if (this.currentGlobalRankingFilterKey !== filterKey || force) {
			this.globalMembersRanking = [];
			this.globalRankingPagination = {
				current_page: 1,
				per_page: 20,
				total_data: 0,
				last_page: 1,
				next_page: null
			};
			this.currentGlobalRankingFilterKey = filterKey;
		} else if (
			!force &&
			this.lastUpdatedGlobalMembersRanking > 0 &&
			page === 1 &&
			Date.now() - this.lastUpdatedGlobalMembersRanking < 300000
		) {
			return;
		}

		const cacheKey = `globalMembersRanking-${page}-${filterKey}`;

		return this.dedup.execute(cacheKey, async () => {
			try {
				this.isLoading = true;
				const response = await liveHistoryApi.getGlobalMembersRanking(
					page,
					20,
					range?.start,
					range?.end
				);

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
				this.lastUpdatedGlobalMembersRanking = Date.now();
			} catch (err) {
				logger.error('Failed to load global members ranking:', err);
			} finally {
				this.isLoading = false;
			}
		});
	}

	async loadGlobalMemberStats(memberId: string) {
		const range = liveHistoryFilterStore.dateRange;
		const key = JSON.stringify({ method: 'loadGlobalMemberStats', memberId, range });

		return this.dedup.execute(key, async () => {
			try {
				const stats = await liveHistoryApi.getGlobalMemberStats(memberId, range?.start, range?.end);
				this.globalMemberStats[memberId] = stats;
			} catch (err) {
				logger.error(`Failed to load global stats for member ${memberId}:`, err);
			}
		});
	}

	async loadGlobalMemberHistory(memberId: string, page: number = 1, force: boolean = false) {
		const range = liveHistoryFilterStore.dateRange;
		const filterKey = JSON.stringify({ memberId, range });

		if (this.currentGlobalMemberHistoryFilterKey !== filterKey || force) {
			this.globalMemberHistory = [];
			this.globalMemberHistoryPagination = {
				page: 1,
				limit: 20,
				total: 0,
				total_pages: 1
			};
			this.currentGlobalMemberHistoryFilterKey = filterKey;
		} else if (
			!force &&
			this.lastUpdatedGlobalMemberHistory > 0 &&
			page === 1 &&
			Date.now() - this.lastUpdatedGlobalMemberHistory < 300000
		) {
			return;
		}

		const cacheKey = `globalMemberHistory-${page}-${filterKey}`;

		return this.dedup.execute(cacheKey, async () => {
			try {
				this.isLoading = true;
				const response = await liveHistoryApi.getGlobalMemberHistory(
					memberId,
					page,
					20,
					range?.start,
					range?.end
				);

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
				this.lastUpdatedGlobalMemberHistory = Date.now();
			} catch (err) {
				logger.error('Failed to load global member history:', err);
			} finally {
				this.isLoading = false;
			}
		});
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
		this.lastUpdatedWatched = 0;
		this.lastUpdatedGlobal = 0;
		this.lastUpdatedOverallStats = 0;
		this.lastUpdatedGlobalStats = 0;
		this.lastUpdatedMembersRanking = 0;
		this.lastUpdatedGlobalMembersRanking = 0;
		this.lastUpdatedGlobalMemberHistory = 0;
		this.currentWatchedFilterKey = '';
		this.currentGlobalFilterKey = '';
		this.currentOverallStatsFilterKey = '';
		this.currentGlobalStatsFilterKey = '';
		this.currentRankingFilterKey = '';
		this.currentGlobalRankingFilterKey = '';
		this.currentGlobalMemberHistoryFilterKey = '';
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
		this.dedup.clear();
	}
}

export const liveHistoryStore = new LiveHistoryStore();
