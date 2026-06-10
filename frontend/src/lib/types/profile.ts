/**
 * Profile-related types for user profiles.
 */

import type { User, UserOshi } from './auth';

export interface RankInfo {
	current: string;
	xp: number;
	nextLevelXp: number;
	nextRankTitle: string;
}

export interface ProfileStats {
	totalShows: number;
	totalAchievements: number;
	totalTwoShots: number;
	totalLiveWatched: number;
	oshiMeetings: number;
}

export interface ProfileRecentActivity {
	ticketId: string;
	title: string;
	date: string;
	section: string;
	number: string;
	hasTwoShot: boolean;
	twoShotMember?: string;
}

export interface OshiTwoShotCounts {
	roulette: number;
	birthday: number;
}

export interface ProfileFullResponse {
	profile: User;
	oshis: UserOshi[];
	rank: RankInfo;
	stats: ProfileStats;
	oshiTwoShots: OshiTwoShotCounts;
	oshiTwoShotsList: OshiTwoShotCounts[];
	oshiMeetingsList: number[];
	recentActivity: ProfileRecentActivity[];
}

/**
 * Extended User type with profile stats for the profile page.
 * These optional fields are populated from ProfileFullResponse when fetching profile.
 */
export interface UserWithProfileStats extends User {
	profileRank?: RankInfo;
	profileStats?: ProfileStats;
	profileOshiTwoShots?: OshiTwoShotCounts;
	profileOshiTwoShotsList?: OshiTwoShotCounts[];
	profileOshiMeetingsList?: number[];
	profileRecentActivity?: ProfileRecentActivity[];
}

/**
 * Public profile data for public-facing profile pages.
 */
export interface PublicProfileData {
	name: string;
	username: string;
	bio?: string | null;
	profilePicture?: string | null;
	profilePicture_medium?: string | null;
	profilePicture_small?: string | null;
	blurHash?: string | null;
	oshi?: UserOshi | null;
	publicYear?: number | null;
}

/**
 * Public profile recent activity item with type field.
 */
export interface PublicRecentActivity {
	title: string;
	date: string;
	type: 'Theater' | '2-Shot';
}

/**
 * Public profile stats for the stats component.
 */
export interface PublicProfileStats {
	totalShows: number;
	totalTwoShots: number;
	topRow: string | null;
	topRowCount?: number;
	topShow: string | null;
	topShowCount?: number;
	showCounts?: Record<string, number>;
	topTwoShots?: Array<{
		name: string;
		count: number;
		imageUrl?: string | null;
		imageUrl_medium?: string | null;
		imageUrl_small?: string | null;
		blurHash?: string | null;
	}>;
}
