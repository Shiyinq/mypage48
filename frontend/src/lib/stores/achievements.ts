import { writable, get } from 'svelte/store';
import type { AchievementsResponse } from '$lib/types';
import { achievements as achievementsApi } from '$lib/apis/achievements';

function createAchievementsStore() {
    const { subscribe, set } = writable<AchievementsResponse | null>(null);

    return {
        subscribe,
        set,
        load: async () => {
            // Return cached data if available
            const current = get({ subscribe });
            if (current) {
                return current;
            }

            try {
                const data = await achievementsApi.getAchievements();
                set(data);
                return data;
            } catch (e) {
                console.error('Failed to load achievements', e);
                throw e;
            }
        },
        reset: () => set(null)
    };
}

export const achievementsStore = createAchievementsStore();
