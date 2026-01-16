import { writable } from 'svelte/store';
import type { UserWithProfileStats } from '$lib/types';
import { auth } from '$lib/apis/auth';
import { client } from '$lib/apis/client';
import { logger } from '$lib/utils/logger';

interface UserProfileStoreState {
	data: UserWithProfileStats | null;
	error: string | null;
}

export const isUserProfileLoading = writable(false);

function createUserProfileStore() {
	const { subscribe, set, update } = writable<UserProfileStoreState>({
		data: null,
		error: null
	});

	return {
		subscribe,
		set,
		update,
		load: async () => {
			isUserProfileLoading.set(true);
			update((s) => ({ ...s, error: null }));
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
				set({ data: userWithStats, error: null });
				return userWithStats;
			} catch (e) {
				logger.error('Failed to load profile', e, { context: 'UserProfileStore' });
				update((s) => ({ ...s, error: 'Failed to load profile' }));
				throw e;
			} finally {
				isUserProfileLoading.set(false);
			}
		},
		updateOshi: async (memberId: string) => {
			await auth.updateOshi(parseInt(memberId));
			const data = await auth.getProfile();
			update((u) => (u.data ? { ...u, data: { ...u.data, oshi: data.oshi } } : u));
		},
		updateAvatar: async (base64Image: string) => {
			await auth.updateProfilePicture(base64Image);
			update((u) => (u.data ? { ...u, data: { ...u.data, profilePicture: base64Image } } : u));
		},
		updatePublicStatus: async (isPublic: boolean, publicYear: number | null) => {
			await client('/users/public-status', {
				method: 'POST',
				body: { isPublic, publicYear }
			});
			update((u) => (u.data ? { ...u, data: { ...u.data, isPublic, publicYear } } : u));
		},
		reset: () => {
			set({ data: null, error: null });
			isUserProfileLoading.set(false);
		}
	};
}

export const userProfile = createUserProfileStore();
