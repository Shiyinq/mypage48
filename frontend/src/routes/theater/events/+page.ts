import { eventsStore } from '$lib/stores/events.svelte';
import { membersStore } from '$lib/stores/theater.svelte';

import { browser } from '$app/environment';

export const load = async () => {
	if (browser) {
		// Defer store loading to next tick to avoid SvelteKit warning about using window.fetch during load
		setTimeout(() => {
			eventsStore.loadUpcoming();
			membersStore.loadBirthdays();
		}, 0);
	}
};
