import { eventsStore } from '$lib/stores/events';
import { membersStore } from '$lib/stores/theater';
import { browser } from '$app/environment';

export const load = async () => {
	if (browser) {
		setTimeout(() => {
			eventsStore.loadUpcoming();
			membersStore.loadBirthdays();
		}, 0);
	}
};
