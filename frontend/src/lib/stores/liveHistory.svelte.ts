import { liveHistoryApi } from '$lib/apis/liveHistory';
import type {
	LiveHistory,
	LiveHistoryStats,
	MemberLiveHistoryStats,
	GlobalLiveHistory
} from '$lib/types/liveHistory';
import { logger } from '$lib/utils/logger';

class LiveHistoryStore {
	// State
	list = $state<LiveHistory[]>([]);
	globalList = $state<GlobalLiveHistory[]>([]);
	overallStats = $state<LiveHistoryStats | null>(null);
	memberStats = $state<Record<string, MemberLiveHistoryStats>>({});
	isLoading = $state(false);
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

			const response = await liveHistoryApi.getHistory(page, 10, memberId);

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
			this.overallStats = await liveHistoryApi.getOverallStats();
		} catch (err) {
			logger.error('Failed to load overall live stats:', err);
		}
	}

	async loadMemberStats(memberId: string) {
		try {
			const stats = await liveHistoryApi.getMemberStats(memberId);
			this.memberStats[memberId] = stats;
		} catch (err) {
			logger.error(`Failed to load stats for member ${memberId}:`, err);
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
		this.error = null;
		this.lastUpdated = 0;
		this.pagination = {
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
