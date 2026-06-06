import { galleryStore } from '$lib/stores/memories.svelte';

import { browser } from '$app/environment';

export const load = async () => {
	if (browser) {
		// Prefetch first page with default filter
		// Defer store loading to next tick to avoid SvelteKit warning about using window.fetch during load
		setTimeout(() => {
			galleryStore.load(1, { type: 'ALL' });
		}, 0);
	}
};
