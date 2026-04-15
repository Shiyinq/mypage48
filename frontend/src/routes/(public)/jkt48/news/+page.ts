import { newsStore } from '$lib/stores/news.svelte';
import { browser } from '$app/environment';

export const load = async () => {
	if (browser) {
		setTimeout(() => {
			newsStore.load(1);
		}, 0);
	}
};
