import { eventsStore } from '$lib/stores/events.svelte';
import { membersStore } from '$lib/stores/theater.svelte';
import { browser } from '$app/environment';

export const load = async () => {
	if (browser) {
		setTimeout(() => {
			eventsStore.loadUpcoming();
			membersStore.loadBirthdays();
		}, 0);
	}
};
