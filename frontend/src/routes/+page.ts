import { dashboardStatsData, dashboardFilter } from '$lib/stores/dashboard.svelte';
import { isAuthenticated } from '$lib/stores';
import { browser } from '$app/environment';

export const load = async () => {
	// Get current filter value from store
	if (browser) {
		// Defer store loading to next tick to avoid SvelteKit warning about using window.fetch during load
		setTimeout(() => {
			if (isAuthenticated.value) {
				dashboardStatsData.load(dashboardFilter);
			}
		}, 0);
	}
};
