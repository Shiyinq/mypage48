import { liveHistoryStore } from '$lib/stores/liveHistory.svelte';
import { membersStore } from '$lib/stores/theater.svelte';
import { browser } from '$app/environment';

export const load = async () => {
	if (browser) {
		queueMicrotask(() => {
			liveHistoryStore.loadGlobal(1, false);
			liveHistoryStore.loadGlobalStats();
			membersStore.load({ limit: 100 }, true);
		});
	}
};
