import { achievementsStore } from '$lib/stores/achievements';

import { browser } from '$app/environment';

export const load = async () => {
	if (browser) {
		// Defer store loading to next tick to avoid SvelteKit warning about using window.fetch during load
		setTimeout(() => {
			achievementsStore.load();
		}, 0);
	}
};
