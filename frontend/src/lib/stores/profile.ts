import { writable } from 'svelte/store';
import type { UserWithProfileStats } from '$lib/types';
import { auth } from '$lib/apis/auth';
import { client } from '$lib/apis/client';

function createUserProfileStore() {
    const { subscribe, set, update } = writable<UserWithProfileStats | null>(null);

    return {
        subscribe,
        set,
        update,
        load: async () => {
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
                set(userWithStats);
                return userWithStats;
            } catch (e) {
                console.error('Failed to load profile', e);
                throw e;
            }
        },
        updateOshi: async (memberId: string) => {
            await auth.updateOshi(parseInt(memberId));
            const data = await auth.getProfile();
            update(u => u ? { ...u, oshi: data.oshi } : null);
        },
        updateAvatar: async (base64Image: string) => {
            await auth.updateProfilePicture(base64Image);
            update(u => u ? { ...u, profilePicture: base64Image } : null);
        },
        updatePublicStatus: async (isPublic: boolean, publicYear: number | null) => {
            await client('/users/public-status', {
                method: 'POST',
                body: { isPublic, publicYear }
            });
            update(u => u ? { ...u, isPublic, publicYear } : u);
        },
        reset: () => set(null)
    };
}

export const userProfile = createUserProfileStore();
