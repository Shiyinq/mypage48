import { membersStore } from '$lib/stores/theater';
import { browser } from '$app/environment';

export const load = async () => {
	if (browser) {
		setTimeout(() => {
			membersStore.load({ limit: 100 }, true);
		}, 0);
	}
};
