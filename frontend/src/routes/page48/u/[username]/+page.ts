import { browser } from '$app/environment';
import type { PageLoad } from './$types';
import { page48Reads } from '$lib/stores/page48.svelte';
import { page48ProfileStore } from '$lib/stores/page48Profile.svelte';

export const load: PageLoad = async ({ params }) => {
	if (browser) {
		const username = params.username;
		queueMicrotask(() => {
			// Only warm the cache what the store does not already hold: a revisited
			// profile would otherwise fire a request whose result is thrown away.
			if (!page48ProfileStore.readProfile(username).isLoaded) {
				void page48Reads.getUserProfile(username).catch(() => {});
			}
			if (!page48ProfileStore.readList(username, 'posts').isLoaded) {
				void page48Reads.getUserPosts(username, 20, null).catch(() => {});
			}
		});
	}
};
