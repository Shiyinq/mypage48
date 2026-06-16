import { newsStore, newsFilter } from '$lib/stores/news.svelte';
import { browser } from '$app/environment';

export const load = async ({ url }) => {
	const page = Number(url.searchParams.get('page')) || 1;
	if (browser) {
		// Defer store loading to next tick to avoid SvelteKit warning about
		// updating state during render, while preserving background fetch
		setTimeout(() => {
			newsStore.load(page, 12, false, newsFilter);
		}, 0);
	}
};
