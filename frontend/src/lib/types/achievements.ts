/**
 * Achievement-related types.
 */

/**
 * Single achievement with unlock status and progress.
 */
export interface AchievementItem {
    id: string;
    title: string;
    description: string;
    icon: string;
    color: string;
    isUnlocked: boolean;
    progress: string | null;
}

/**
 * Response from achievements API.
 */
export interface AchievementsResponse {
    achievements: AchievementItem[];
    unlockedCount: number;
    totalCount: number;
}
