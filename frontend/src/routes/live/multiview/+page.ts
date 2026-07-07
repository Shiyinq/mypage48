import { liveStore } from '$lib/stores/live.svelte';
import { browser } from '$app/environment';

export const load = async () => {
	if (browser) {
		setTimeout(() => {
			liveStore.loadLiveList(true);
		}, 0);
	}
};
