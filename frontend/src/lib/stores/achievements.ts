import { writable, get } from 'svelte/store';
import type { AchievementsResponse } from '$lib/types';
import { achievements as achievementsApi } from '$lib/apis/achievements';
import { logger } from '$lib/utils/logger';

interface AchievementsState {
	data: AchievementsResponse | null;
	error: string | null;
}

export const isAchievementsLoading = writable(false);

function createAchievementsStore() {
	const { subscribe, set, update } = writable<AchievementsState>({
		data: null,
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

			isAchievementsLoading.set(true);
			update((s) => ({ ...s, error: null }));

			try {
				const data = await achievementsApi.getAchievements();
				update((s) => ({ ...s, data }));
				return data;
			} catch (e) {
				logger.error('Failed to load achievements', e, { context: 'AchievementsStore' });
				update((s) => ({ ...s, error: 'Failed to load achievements' }));
				throw e;
			} finally {
				isAchievementsLoading.set(false);
			}
		},
		reset: () => {
			set({ data: null, error: null });
			isAchievementsLoading.set(false);
		}
	};
}

export const achievementsStore = createAchievementsStore();
