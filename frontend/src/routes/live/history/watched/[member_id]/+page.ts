import { liveHistoryStore } from '$lib/stores/liveHistory.svelte';
import { browser } from '$app/environment';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params }) => {
	if (browser && params.member_id) {
		queueMicrotask(() => {
			liveHistoryStore.load(1, params.member_id, false);
			liveHistoryStore.loadMemberStats(params.member_id);
		});
	}
};
