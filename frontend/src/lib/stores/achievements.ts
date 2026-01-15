import { writable, get } from 'svelte/store';
import type { AchievementsResponse } from '$lib/types';
import { achievements as achievementsApi } from '$lib/apis/achievements';
import { logger } from '$lib/utils/logger';

function createAchievementsStore() {
	const { subscribe, set, update } = writable<{
		data: AchievementsResponse | null;
		loading: boolean;
		error: string | null;
	}>({
		data: null,
		loading: false,
		error: null
	});

	return {
		subscribe,
		set,
		load: async () => {
			const state = get({ subscribe });
			// Return cached data if available
			if (state.data) {
				return state.data;
			}

			update((s) => ({ ...s, loading: true, error: null }));

			try {
				const data = await achievementsApi.getAchievements();
				update((s) => ({ ...s, data, loading: false }));
				return data;
			} catch (e) {
				logger.error('Failed to load achievements', e, { context: 'AchievementsStore' });
				update((s) => ({ ...s, loading: false, error: 'Failed to load achievements' }));
				throw e;
			}
		},
		reset: () => set({ data: null, loading: false, error: null })
	};
}

export const achievementsStore = createAchievementsStore();
