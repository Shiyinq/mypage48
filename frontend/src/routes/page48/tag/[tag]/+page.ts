import { browser } from '$app/environment';
import type { PageLoad } from './$types';
import { page48Reads } from '$lib/stores/page48.svelte';
import { getActiveMedia } from '$lib/utils/page48';

export const load: PageLoad = async ({ params, url }) => {
	if (browser) {
		const media = getActiveMedia(url.pathname, url.search);
		queueMicrotask(() => {
			void page48Reads.getPostsByTag(params.tag, 20, null, media).catch(() => {});
		});
	}
};
