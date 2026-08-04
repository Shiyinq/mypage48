import { liveStore } from '$lib/stores/live.svelte';
import { replayStore } from '$lib/stores/replay.svelte';
import { browser } from '$app/environment';

export const load = async () => {
	if (browser) {
		queueMicrotask(() => {
			liveStore.loadLiveList();
			replayStore.loadVideos(1, 20, '', 'all', '', false);
		});
	}
};
