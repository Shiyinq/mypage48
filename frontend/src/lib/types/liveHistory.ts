export interface LiveHistoryUpdateRequest {
	live_id: string;
	member_id: string;
	member_name: string;
	member_nickname?: string;
	platform: string;
	ping_duration: number;
	live_title?: string;
}

export interface LiveHistory {
	_id: string;
	live_id: string;
	member_id: string;
	member_name: string;
	member_nickname?: string;
	platform: string;
	live_title?: string;
	duration: number;
	started_at: string;
	last_updated_at: string;
}

export interface LiveHistoryStats {
	total_duration: number;
	total_watches: number;
	top_member_id: string | null;
	top_member_name: string | null;
	top_member_watches: number;
	member_counts: Record<string, number>;
	member_durations: Record<string, number>;
	platform_counts: Record<string, number>;
	longest_watch?: LongestWatchInfo | null;
}

export interface LongestWatchInfo {
	duration: number;
	live_title?: string;
	platform?: string;
	started_at?: string;
	member_name?: string;
}

export interface MemberLiveHistoryStats {
	member_id: string;
	total_watches: number;
	total_duration: number;
	platform_counts?: Record<string, number>;
	longest_watch?: LongestWatchInfo | null;
}

export interface GlobalSingleMemberLiveHistoryStats {
	member_id: string;
	total_lives: number;
	total_duration: number;
	platform_counts?: Record<string, number>;
	longest_live?: LongestWatchInfo | null;
}

export interface LiveHistoryResponse {
	data: LiveHistory[];
	meta: {
		current_page: number;
		last_page: number;
		total_data: number;
		per_page: number;
		next_page: number | null;
	};
}

export interface GlobalLiveHistory {
	_id: string;
	live_id: string;
	platform: string;
	title?: string;
	image?: string;
	view_num: number;
	start_at: string;
	end_at?: string;
	last_seen_at: string;
	status: string;
	member: {
		id: string;
		name: string;
		nickname?: string;
		img?: string;
	};
	duration: number;
}

export interface GlobalLiveHistoryResponse {
	data: GlobalLiveHistory[];
	total: number;
	page: number;
	limit: number;
	total_pages: number;
}

export interface WatchedLiveMemberRankingItem {
	member_id: string;
	member_name?: string;
	total_watches: number;
	total_duration: number;
}

export interface WatchedLiveMemberRankingResponse {
	data: WatchedLiveMemberRankingItem[];
	meta: {
		current_page: number;
		last_page: number;
		total_data: number;
		per_page: number;
		next_page: number | null;
	};
}

export interface GlobalLiveHistoryStats {
	total_lives: number;
	total_duration: number;
	unique_members_count: number;
	top_member_id: string | null;
	top_member_name: string | null;
	top_member_watches: number;
	top_member_duration: number;
	platform_counts: Record<string, number>;
	highest_view_live?: LongestWatchInfo | null;
}

export interface GlobalLiveMemberRankingItem {
	member_id: string;
	member_name?: string;
	total_watches: number;
	total_duration: number;
}

export interface GlobalLiveMemberRankingResponse {
	data: GlobalLiveMemberRankingItem[];
	meta: {
		current_page: number;
		last_page: number;
		total_data: number;
		per_page: number;
		next_page: number | null;
	};
}
