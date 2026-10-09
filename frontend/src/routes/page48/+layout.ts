import { browser } from '$app/environment';
import { activeUsersStore, memberXTagsStore, trendingTagsStore } from '$lib/stores/page48.svelte';

/**
 * Warm the Page48 sidebars for every page under `/page48`.
 *
 * The layout runs for any child route SvelteKit prefetches, so one hover gets
 * the sidebars (member hashtags, trending tags, active users) and their mount
 * effects then find the session cache already filled instead of refetching.
 */
export const load = async () => {
	if (browser) {
		queueMicrotask(() => {
			void memberXTagsStore.load();
			void trendingTagsStore.load();
			void activeUsersStore.load();
		});
	}
};
