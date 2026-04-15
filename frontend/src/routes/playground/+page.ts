import { playgroundStore } from '$lib/stores/playground.svelte';
import { browser } from '$app/environment';

export const load = async () => {
	if (browser) {
		setTimeout(() => {
			playgroundStore.init();
		}, 0);
	}
};
