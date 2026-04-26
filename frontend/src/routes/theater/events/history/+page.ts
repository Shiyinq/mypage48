import { eventsStore } from '$lib/stores/events.svelte';
import { browser } from '$app/environment';

export const load = async () => {
	if (browser) {
		// Prefetch on hover. Dedup in the store prevents concurrent duplicates.
		// A cache check in the store also prevents re-fetch when hover prefetch already completed.
		setTimeout(() => {
			eventsStore.loadHistory(1);
		}, 0);
	}
};
