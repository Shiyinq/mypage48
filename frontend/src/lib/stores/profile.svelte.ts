import type { UserWithProfileStats } from '$lib/types';
import { auth } from '$lib/apis/auth';
import { client } from '$lib/apis/client';
import { logger } from '$lib/utils/logger';

/**
 * User profile store - migrated to Svelte 5 Shared Rune State.
 * Manages user data, oshi preference, and loading states.
 */

interface UserProfileStoreState {
	data: UserWithProfileStats | null;
	error: string | null;
	isLoading: boolean;
}

const state = $state<UserProfileStoreState>({
	data: null,
	error: null,
	isLoading: false
});

function createUserProfileStore() {
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

		/**
		 * Load profile data from API if not already loaded
		 */
		load: async () => {
			if (state.data) return state.data;

			state.isLoading = true;
			state.error = null;
			try {
				const data = await auth.getProfile();
				const userWithStats: UserWithProfileStats = {
					...data.profile,
					oshi: data.oshi,
					profileRank: data.rank,
					profileStats: data.stats,
					profileOshiTwoShots: data.oshiTwoShots,
					profileRecentActivity: data.recentActivity
				};
				state.data = userWithStats;
				state.error = null;
				return userWithStats;
			} catch (e) {
				logger.error('Failed to load profile', e, { context: 'UserProfileStore' });
				state.error = 'Failed to load profile';
				throw e;
			} finally {
				state.isLoading = false;
			}
		},

		/**
		 * Update the user's oshi preference
		 */
		updateOshi: async (memberId: string) => {
			state.isLoading = true;
			try {
				await auth.updateOshi(parseInt(memberId));
				const data = await auth.getProfile();
				if (state.data) {
					state.data = {
						...state.data,
						oshi: data.oshi,
						profileRank: data.rank,
						profileStats: data.stats,
						profileOshiTwoShots: data.oshiTwoShots,
						profileRecentActivity: data.recentActivity
					};
				}
			} finally {
				state.isLoading = false;
			}
		},

		/**
		 * Update the user's avatar
		 */
		updateAvatar: async (base64Image: string) => {
			await auth.updateProfilePicture(base64Image);
			if (state.data) {
				state.data.profilePicture = base64Image;
			}
		},

		/**
		 * Update public visibility status
		 */
		updatePublicStatus: async (isPublic: boolean, publicYear: number | null) => {
			await client('/users/public-status', {
				method: 'POST',
				body: { isPublic, publicYear }
			});
			if (state.data) {
				state.data.isPublic = isPublic;
				state.data.publicYear = publicYear;
			}
		},

		/**
		 * Legacy set method for manual updates (e.g. from layout)
		 */
		set: (val: Partial<UserProfileStoreState>) => {
			if (val.data !== undefined) state.data = val.data;
			if (val.error !== undefined) state.error = val.error;
			if (val.isLoading !== undefined) state.isLoading = val.isLoading;
		},

		/**
		 * Reset the store to initial state (on logout)
		 */
		reset: () => {
			state.data = null;
			state.error = null;
			state.isLoading = false;
		},

		/**
		 * Legacy subscribe method for backward compatibility
		 */
		subscribe: (fn: (val: { data: UserWithProfileStats | null; error: string | null }) => void) => {
			fn({ data: state.data, error: state.error });
			$effect.root(() => {
				$effect(() => {
					fn({ data: state.data, error: state.error });
				});
			});
			return () => {};
		}
	};
}

export const userProfile = createUserProfileStore();

/**
 * Legacy separated loading store for backward compatibility
 */
export const isUserProfileLoading = {
	get value() {
		return state.isLoading;
	},
	subscribe: (fn: (val: boolean) => void) => {
		fn(state.isLoading);
		$effect.root(() => {
			$effect(() => {
				fn(state.isLoading);
			});
		});
		return () => {};
	}
};
