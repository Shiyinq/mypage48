import { dashboardStatsData, dashboardFilter } from '$lib/stores/dashboard';
import { isAuthenticated } from '$lib/stores';
import { get } from 'svelte/store';

import { browser } from '$app/environment';

export const load = async () => {
	// Get current filter value from store
	if (browser) {
		// Defer store loading to next tick to avoid SvelteKit warning about using window.fetch during load
		setTimeout(() => {
			if (get(isAuthenticated)) {
				const filter = get(dashboardFilter);
				dashboardStatsData.load(filter);
			}
		}, 0);
	}
};
