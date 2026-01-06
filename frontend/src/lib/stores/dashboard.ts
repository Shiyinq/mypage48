import { writable, get } from 'svelte/store';
import type { DashboardStats } from '$lib/types';
import { dashboard } from '$lib/apis/dashboard';

const currentYear = new Date().getFullYear();

// Define filter type
export interface DashboardFilterState {
	selectedYear: number;
	startMonth: number;
	endMonth: number;
	isAllData: boolean;
}

export const dashboardFilter = writable<DashboardFilterState>({
	selectedYear: currentYear,
	startMonth: 0,
	endMonth: 11,
	isAllData: false
});

// Create smart store for stats
function createDashboardStore() {
	const { subscribe, set } = writable<DashboardStats | null>(null);
	const lastFetchedFilter = writable<string>('');

	return {
		subscribe,
		set,
		load: async (filter: DashboardFilterState) => {
			const currentFilterKey = JSON.stringify(filter);

			// Cache check: if we already fetched this filter, don't re-fetch
			const lastKey = get(lastFetchedFilter);
			const currentData = get({ subscribe });

			if (currentData && lastKey === currentFilterKey) {
				return;
			}

			const stats = await dashboard.getStats({
				year: filter.selectedYear,
				startMonth: filter.startMonth,
				endMonth: filter.endMonth,
				isAllData: filter.isAllData
			});
			set(stats);
			lastFetchedFilter.set(currentFilterKey);
		},
		reset: () => {
			set(null);
			lastFetchedFilter.set('');
			dashboardFilter.set({
				selectedYear: new Date().getFullYear(),
				startMonth: 0,
				endMonth: 11,
				isAllData: false
			});
		},
		invalidate: () => {
			set(null);
			lastFetchedFilter.set('');
		}
	};
}

export const dashboardStatsData = createDashboardStore();

// Export aliases for compatibility if needed, though simpler to use store methods directly
export const resetDashboard = dashboardStatsData.reset;
export const invalidateDashboard = dashboardStatsData.invalidate;
