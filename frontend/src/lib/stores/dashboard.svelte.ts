import type { DashboardStats } from '$lib/types';
import { dashboard } from '$lib/apis/dashboard';
import { logger } from '$lib/utils/logger';

/**
 * Dashboard store - migrated to Svelte 5 Shared Rune State.
 * Manages statistics, filters, and loading states for the user dashboard.
 */

const currentYear = new Date().getFullYear();

// Define filter type
export interface DashboardFilterState {
	selectedYear: number;
	startMonth: number;
	endMonth: number;
	isAllData: boolean;
}

// Global reactive state for filtering
export const dashboardFilter = $state<DashboardFilterState>({
	selectedYear: currentYear,
	startMonth: 0,
	endMonth: 11,
	isAllData: false
});

// Global reactive state for loading
let isLoading = $state(false);

interface StatsState {
	data: DashboardStats | null;
	error: string | null;
}

const statsState = $state<StatsState>({
	data: null,
	error: null
});

let lastFetchedFilterKey = $state('');

function createDashboardStore() {
	return {
		get data() {
			return statsState.data;
		},
		get error() {
			return statsState.error;
		},
		get isLoading() {
			return isLoading;
		},

		/**
		 * Load dashboard statistics based on filters
		 */
		load: async (filter: DashboardFilterState) => {
			const currentFilterKey = JSON.stringify(filter);

			// Cache check: if we already fetched this filter, don't re-fetch
			if (statsState.data && lastFetchedFilterKey === currentFilterKey) {
				return;
			}

			statsState.error = null;
			isLoading = true;

			try {
				const stats = await dashboard.getStats({
					year: filter.selectedYear,
					startMonth: filter.startMonth,
					endMonth: filter.endMonth,
					isAllData: filter.isAllData
				});
				statsState.data = stats;
				statsState.error = null;
				lastFetchedFilterKey = currentFilterKey;
			} catch (e) {
				logger.error('Failed to load dashboard stats', e, { context: 'DashboardStore' });
				statsState.error = 'Failed to load dashboard stats';
			} finally {
				isLoading = false;
			}
		},

		/**
		 * Reset the store and filters to initial state
		 */
		reset: () => {
			statsState.data = null;
			statsState.error = null;
			lastFetchedFilterKey = '';
			Object.assign(dashboardFilter, {
				selectedYear: new Date().getFullYear(),
				startMonth: 0,
				endMonth: 11,
				isAllData: false
			});
			isLoading = false;
		},

		/**
		 * Invalidate cache to force next load
		 */
		invalidate: () => {
			statsState.data = null;
			statsState.error = null;
			lastFetchedFilterKey = '';
			isLoading = false;
		},

		/**
		 * Legacy subscribe method for backward compatibility
		 */
		subscribe: (fn: (val: { data: DashboardStats | null; error: string | null }) => void) => {
			$effect.root(() => {
				$effect(() => {
					fn({ data: statsState.data, error: statsState.error });
				});
			});
			return () => {};
		}
	};
}

export const dashboardStatsData = createDashboardStore();

// Compatibility properties
export const isDashboardLoading = {
	get value() {
		return isLoading;
	},
	subscribe: (fn: (val: boolean) => void) => {
		$effect.root(() => {
			$effect(() => {
				fn(isLoading);
			});
		});
		return () => {};
	}
};

// Export aliases for compatibility
export const resetDashboard = () => dashboardStatsData.reset();
export const invalidateDashboard = () => dashboardStatsData.invalidate();
