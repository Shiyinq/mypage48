import { browser } from '$app/environment';
import type { PageLoad } from './$types';
import { page48Reads } from '$lib/stores/page48.svelte';

export const load: PageLoad = async ({ params }) => {
	if (browser) {
		const username = params.username;
		queueMicrotask(() => {
			void page48Reads.getUserProfile(username).catch(() => {});
			void page48Reads.getUserPosts(username, 20, null).catch(() => {});
		});
	}
};
