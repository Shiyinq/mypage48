import { eventsStore } from '$lib/stores/events';
import { browser } from '$app/environment';

export const load = async () => {
	if (browser) {
		setTimeout(() => {
			eventsStore.loadHistory(1);
		}, 0);
	}
};
