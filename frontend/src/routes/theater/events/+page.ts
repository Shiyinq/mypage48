import { eventsStore } from '$lib/stores/events';

import { browser } from '$app/environment';

export const load = async () => {
	if (browser) {
		// Defer store loading to next tick to avoid SvelteKit warning about using window.fetch during load
		setTimeout(() => {
			eventsStore.loadUpcoming();
		}, 0);
	}
};
