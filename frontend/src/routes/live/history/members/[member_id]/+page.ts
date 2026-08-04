import { liveHistoryStore } from '$lib/stores/liveHistory.svelte';
import { browser } from '$app/environment';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params }) => {
	if (browser && params.member_id) {
		queueMicrotask(() => {
			liveHistoryStore.loadGlobalMemberHistory(params.member_id, 1, false);
			liveHistoryStore.loadGlobalMemberStats(params.member_id);
		});
	}
};
