import { pcCollectionStore } from '$lib/stores/pcCollection.svelte';
import { browser } from '$app/environment';

export const load = async () => {
	if (browser) {
		queueMicrotask(() => {
			pcCollectionStore.load('all', 1, false);
		});
	}
};
