import { writable, get } from 'svelte/store';
import type { DashboardStats } from '$lib/types';
import { dashboard } from '$lib/apis/dashboard';
import { logger } from '$lib/utils/logger';

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

export const isDashboardLoading = writable(false);

// Create smart store for stats
function createDashboardStore() {
	const { subscribe, set, update } = writable<{
		data: DashboardStats | null;
		error: string | null;
	}>({
		data: null,
		error: null
	});
	const lastFetchedFilter = writable<string>('');

	return {
		subscribe,
		set,
		load: async (filter: DashboardFilterState) => {
			const currentFilterKey = JSON.stringify(filter);

			// Cache check: if we already fetched this filter, don't re-fetch
			const lastKey = get(lastFetchedFilter);
			const currentData = get({ subscribe });

			if (currentData.data && lastKey === currentFilterKey) {
				return;
			}

			update((s) => ({ ...s, error: null }));
			isDashboardLoading.set(true);

			try {
				const stats = await dashboard.getStats({
					year: filter.selectedYear,
					startMonth: filter.startMonth,
					endMonth: filter.endMonth,
					isAllData: filter.isAllData
				});
				set({ data: stats, error: null });
				lastFetchedFilter.set(currentFilterKey);
			} catch (e) {
				logger.error('Failed to load dashboard stats', e, { context: 'DashboardStore' });
				update((s) => ({ ...s, error: 'Failed to load dashboard stats' }));
				// Optional: don't throw, let store error state handle UI
			} finally {
				isDashboardLoading.set(false);
			}
		},
		reset: () => {
			set({ data: null, error: null });
			lastFetchedFilter.set('');
			dashboardFilter.set({
				selectedYear: new Date().getFullYear(),
				startMonth: 0,
				endMonth: 11,
				isAllData: false
			});
			isDashboardLoading.set(false);
		},
		invalidate: () => {
			set({ data: null, error: null });
			lastFetchedFilter.set('');
			isDashboardLoading.set(false);
		}
	};
}

export const dashboardStatsData = createDashboardStore();

// Export aliases for compatibility if needed, though simpler to use store methods directly
export const resetDashboard = dashboardStatsData.reset;
export const invalidateDashboard = dashboardStatsData.invalidate;
