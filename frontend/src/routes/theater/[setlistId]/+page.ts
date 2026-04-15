import { setlistsStore } from '$lib/stores/theater.svelte';

import { browser } from '$app/environment';

export const load = async ({ params }) => {
	if (browser) {
		// Defer store loading to next tick to avoid SvelteKit warning about using window.fetch during load
		setTimeout(() => {
			setlistsStore.loadDetail(params.setlistId);
		}, 0);
	}
};
