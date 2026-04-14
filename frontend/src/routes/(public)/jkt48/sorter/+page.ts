import { membersStore } from '$lib/stores/theater.svelte';
import { browser } from '$app/environment';

export const load = async () => {
	if (browser) {
		setTimeout(() => {
			membersStore.load({ limit: 100 }, true);
			membersStore.getGenerations();
		}, 0);
	}
};
