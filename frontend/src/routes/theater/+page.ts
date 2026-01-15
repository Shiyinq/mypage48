import { setlistsStore } from '$lib/stores/theater';

import { browser } from '$app/environment';

export const prerender = false;

export const load = async () => {
    if (browser) {
        // Defer store loading to next tick to avoid SvelteKit warning about using window.fetch during load
        setTimeout(() => {
            setlistsStore.load();
        }, 0);
    }
};
