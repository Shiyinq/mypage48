import { replayStore } from '$lib/stores/replay.svelte';
import { membersStore } from '$lib/stores/theater.svelte';
import { browser } from '$app/environment';

export const load = async () => {
	if (browser) {
		queueMicrotask(() => {
			replayStore.loadVideos(1, 20, '', 'all', '', false);
			membersStore.load({ limit: 100 }, true);
		});
	}
};
