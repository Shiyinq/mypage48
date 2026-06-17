import { liveHistoryApi } from '$lib/apis/liveHistory';
import { liveHistoryFilterStore } from '$lib/stores/liveHistoryFilter.svelte';
import type { PCLiveHistory } from '$lib/types/liveHistory';
import { logger } from '$lib/utils/logger';

class PCCollectionStore {
	list = $state<PCLiveHistory[]>([]);
	isLoading = $state(false);
	error = $state<string | null>(null);
	pagination = $state({ page: 1, limit: 10, total: 0, total_pages: 1 });
	currentType = $state<'all' | 'owned' | 'unowned'>('all');
	currentSort = $state<string>('date_desc');

	async load(type: 'all' | 'owned' | 'unowned' = 'all', page: number = 1, force: boolean = false) {
		if (this.isLoading) return;

		if (force || this.currentType !== type) {
			this.list = [];
			this.pagination = { page: 1, limit: 10, total: 0, total_pages: 1 };
			this.currentType = type;
		}

		try {
			this.isLoading = true;
			this.error = null;
			const range = liveHistoryFilterStore.dateRange;
			const response = await liveHistoryApi.getPCCollection(
				type,
				page,
				this.pagination.limit,
				range?.start,
				range?.end,
				this.currentSort
			);

			if (page === 1) {
				this.list = response.data;
			} else {
				const newItems = response.data.filter(
					(newItem) => !this.list.some((item) => item._id === newItem._id)
				);
				this.list = [...this.list, ...newItems];
			}
			this.pagination = {
				page: response.page,
				limit: response.limit,
				total: response.total,
				total_pages: response.total_pages
			};
		} catch (e: unknown) {
			logger.error(`Failed to load ${type} pc collection`, e);
			this.error = (e as Error).message || `Failed to load ${type} pc collection`;
		} finally {
			this.isLoading = false;
		}
	}

	reset() {
		this.list = [];
		this.error = null;
		this.pagination = { page: 1, limit: 10, total: 0, total_pages: 1 };
		this.currentType = 'all';
		this.currentSort = 'date_desc';
	}

	setSort(sort: string) {
		if (this.currentSort !== sort) {
			this.currentSort = sort;
			this.load(this.currentType, 1, true);
		}
	}
}

export const pcCollectionStore = new PCCollectionStore();
