import type { PaginationMeta } from './common';

export interface ReplayChatMessage {
	id: number;
	startTime: number;
	username: string;
	message: string;
	isGift: boolean;
	isJoin?: boolean;
	isJoinGroup?: boolean;
	joinGroup?: ReplayChatMessage[];
}

export interface ReplayVideo {
	youtube_id: string;
	title: string;
	youtube_title?: string;
	member: string;
	date: string;
	platform: string;
	added_at: string;
	srt_file?: string;
	live_id?: string;
	has_loveletter?: boolean;
	transcript_file?: string;
	duration?: number;
}

export interface ReplayDetailFiles {
	screenshots: string[];
}

export interface ReplayGiftSummary {
	name: string;
	count: number;
	total_gold: number;
	image?: string;
	free?: boolean;
}

export interface ReplayTopFan {
	user: string;
	avatar?: string;
	total_gold: number;
	count: number;
	free_gold?: number;
	free_count?: number;
}

export interface ReplayDetailResponse {
	id: string;
	live_id: string;
	platform: string;
	member_name: string;
	member_nickname: string;
	title?: string;
	youtube_title?: string;
	image?: string;
	image_medium?: string;
	image_small?: string;
	blurHash?: string;
	view_num?: number;
	duration_seconds: number;
	start_at?: string;
	end_at?: string;
	duration?: number;
	youtube_id?: string;
	files: ReplayDetailFiles;
	total_chats: number;
	total_gifts: number;
	total_free_gifts?: number;
	total_gold: number;
	total_loveletters?: number;
	top_gifts: ReplayGiftSummary[];
	top_fans: ReplayTopFan[];
	chats: Record<string, unknown>[];
	recording_started_at?: string;
	member?: {
		id: string;
		name: string;
		nickname?: string;
		img?: string;
		member_type?: string;
	};
}

export interface ReplayPaginationResponse {
	data: ReplayVideo[];
	meta: PaginationMeta;
}
