import type { AchievementsResponse } from '$lib/types';
import { achievements as achievementsApi } from '$lib/apis/achievements';
import { logger } from '$lib/utils/logger';

/**
 * Achievements store - migrated to Svelte 5 Shared Rune State.
 * Manages the retrieval and caching of user achievements.
 */

interface AchievementsState {
	data: AchievementsResponse | null;
	error: string | null;
	isLoading: boolean;
}

const initialState: AchievementsState = {
	data: null,
	error: null,
	isLoading: false
};

const state = $state<AchievementsState>(initialState);

function createAchievementsStore() {
	return {
		get data() {
			return state.data;
		},
		get error() {
			return state.error;
		},
		get isLoading() {
			return state.isLoading;
		},

		load: async () => {
			if (state.data) return state.data;

			state.error = null;
			state.isLoading = true;

			try {
				const data = await achievementsApi.getAchievements();
				state.data = data;
				state.error = null;
				return data;
			} catch (e) {
				logger.error('Failed to load achievements', e, { context: 'AchievementsStore' });
				state.error = 'Failed to load achievements';
				throw e;
			} finally {
				state.isLoading = false;
			}
		},

		reset: () => {
			Object.assign(state, initialState);
		},

		/**
		 * Legacy subscribe method for backward compatibility
		 */
		subscribe: (fn: (val: { data: AchievementsResponse | null; error: string | null }) => void) => {
			fn({
				data: state.data,
				error: state.error
			});
			$effect.root(() => {
				$effect(() => {
					fn({
						data: state.data,
						error: state.error
					});
				});
			});
			return () => {};
		}
	};
}

export const achievementsStore = createAchievementsStore();

// Compatibility Alias
export const isAchievementsLoading = {
	get value() {
		return state.isLoading;
	},
	subscribe: (fn: (val: boolean) => void) => {
		fn(state.isLoading);
		$effect.root(() => {
			$effect(() => fn(state.isLoading));
		});
		return () => {};
	}
};
