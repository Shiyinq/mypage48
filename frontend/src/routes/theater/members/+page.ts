import { membersStore } from '$lib/stores/theater.svelte';
import { browser } from '$app/environment';

export const load = async () => {
	if (browser) {
		// Use SAME params as onMount ({ limit: 100 }, true) so dedup key matches
		// and concurrent requests (hover-prefetch + onMount) share one in-flight promise.
		setTimeout(() => {
			membersStore.load({ limit: 100 }, true);
			membersStore.getGenerations();
		}, 0);
	}
};
