import { liveStore } from '$lib/stores/live.svelte';
import { browser } from '$app/environment';

export const load = async () => {
	if (browser) {
		// Use SAME param as onMount (forceRefresh=false default) so dedup key matches.
		// Previously used loadLiveList(true) while onMount used loadLiveList() → different keys.
		setTimeout(() => {
			liveStore.loadLiveList();
		}, 0);
	}
};
