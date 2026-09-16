import { FEATURES } from '$lib/config/features';
import { liveStore } from '$lib/stores/live.svelte';
import { browser } from '$app/environment';

export const load = async () => {
	if (!FEATURES.OSHI_LIVE_ENABLED) return;
	if (browser) {
		queueMicrotask(() => {
			liveStore.loadLiveList();
			liveStore.loadScheduledList();
		});
	}
};
