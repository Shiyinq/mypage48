import { setlistsStore } from '$lib/stores/theater.svelte';

import { browser } from '$app/environment';

import { dashboardFilter } from '$lib/stores/dashboard.svelte';

export const load = async ({ params }) => {
	if (browser) {
		// Defer store loading to next tick to avoid SvelteKit warning about using window.fetch during load
		setTimeout(() => {
			setlistsStore.loadDetail(params.setlistId, {
				year: dashboardFilter.selectedYear,
				startMonth: dashboardFilter.startMonth,
				endMonth: dashboardFilter.endMonth,
				isAllData: dashboardFilter.isAllData
			});
		}, 0);
	}
};
