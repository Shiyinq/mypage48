import { membersStore } from '$lib/stores/theater.svelte';
import { browser } from '$app/environment';

export const load = async () => {
	if (browser) {
		await membersStore.load({ limit: 100 }, true);
		await membersStore.getGenerations();
	}
};
