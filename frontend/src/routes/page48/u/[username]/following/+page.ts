import { browser } from '$app/environment';
import type { PageLoad } from './$types';
import { page48Reads } from '$lib/stores/page48.svelte';

export const load: PageLoad = async ({ params }) => {
	if (browser) {
		queueMicrotask(() => {
			void page48Reads.getFollowing(params.username, 20, null).catch(() => {});
		});
	}
};
