import { liveHistoryStore } from '$lib/stores/liveHistory.svelte';
import { browser } from '$app/environment';

export const load = async () => {
	if (browser) {
		queueMicrotask(() => {
			liveHistoryStore.loadMembersRanking(1, false);
		});
	}
};
