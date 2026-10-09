import { browser } from '$app/environment';
import type { PageLoad } from './$types';
import { page48Reads } from '$lib/stores/page48.svelte';
import { isAuthenticated } from '$lib/stores/authStatus.svelte';

export const load: PageLoad = async () => {
	if (browser && isAuthenticated.value) {
		queueMicrotask(() => {
			void page48Reads.getFeed(20, null, null, true).catch(() => {});
		});
	}
};
