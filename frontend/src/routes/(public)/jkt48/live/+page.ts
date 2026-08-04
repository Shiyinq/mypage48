import { liveStore } from '$lib/stores/live.svelte';
import { browser } from '$app/environment';

export const load = async () => {
	if (browser) {
		queueMicrotask(() => {
			liveStore.loadLiveList();
			liveStore.loadScheduledList();
		});
	}
};
