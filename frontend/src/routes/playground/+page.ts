import { playgroundStore } from '$lib/stores/playground';
import { browser } from '$app/environment';

export const load = async () => {
	if (browser) {
		setTimeout(() => {
			playgroundStore.init();
		}, 0);
	}
};
