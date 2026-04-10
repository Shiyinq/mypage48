import { liveStore } from '$lib/stores/live';
import { browser } from '$app/environment';

export const load = async () => {
	if (browser) {
		setTimeout(() => {
			liveStore.loadLiveList(true);
		}, 0);
	}
};
