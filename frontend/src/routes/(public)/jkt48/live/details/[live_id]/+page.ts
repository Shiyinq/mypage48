import { liveHistoryDetailStore } from '$lib/stores/liveHistoryDetail.svelte';
import { browser } from '$app/environment';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params }) => {
	if (browser && params.live_id) {
		queueMicrotask(() => {
			liveHistoryDetailStore.loadDetail(params.live_id, false);
		});
	}
};
