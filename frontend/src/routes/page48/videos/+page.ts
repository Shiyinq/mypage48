import { browser } from '$app/environment';
import type { PageLoad } from './$types';
import { page48Reads } from '$lib/stores/page48.svelte';

export const load: PageLoad = async () => {
	if (browser) {
		queueMicrotask(() => {
			// The video feed requests a smaller first page (10), so the warm-up matches.
			void page48Reads.getFeed(10, null, 'video').catch(() => {});
		});
	}
};
