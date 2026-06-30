export interface ReplayVideo {
	youtube_id: string;
	title: string;
	member: string;
	date: string;
	platform: string;
	added_at: string;
	srt_file: string;
	has_loveletter?: boolean;
	transcript_file?: string;
}

export interface ReplayChatMessage {
	id: number;
	startTime: number;
	username: string;
	message: string;
	isGift: boolean;
}
