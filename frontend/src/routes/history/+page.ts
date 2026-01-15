
import { ticketsStore } from '$lib/stores';
import { browser } from '$app/environment';

export const load = async () => {
    if (browser) {
        // Defer store loading to next tick to avoid SvelteKit warning about using window.fetch during load
        setTimeout(() => {
            ticketsStore.load(1);
        }, 0);
    }
};
