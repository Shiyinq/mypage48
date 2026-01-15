
import { userProfile } from '$lib/stores/profile';

import { browser } from '$app/environment';

export const load = async () => {
    if (browser) {
        // Defer store loading to next tick to avoid SvelteKit warning about using window.fetch during load
        setTimeout(() => {
            userProfile.load();
        }, 0);
    }
};
