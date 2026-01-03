import { client } from './client';
import type { AchievementsResponse } from '$lib/types';

export const achievements = {
    getAchievements: async () => {
        return client<AchievementsResponse>('/achievements');
    }
};
