export interface LiveMember {
	id?: string;
	name: string;
	nickname?: string;
	img: string;
	member_type?: string;
}

export interface LiveStatus {
	platform: 'showroom' | 'idn';
	room_id?: string;
	live_id?: string;
	room_url_key: string;
	room_identifier?: string;
	view_num: number;
	title: string;
	start_at?: string;
	end_at?: string;
	status?: string;
	duration?: number;
	member: LiveMember;
	image?: string;
	live_type?: string;
	scheduled_at?: string;
}

export interface StreamingUrl {
	url: string;
	label: string;
}

export interface LiveStreamingResponse {
	streaming_urls: StreamingUrl[];
	room_identifier: string;
	view_num?: number;
	start_at?: string;
	member: LiveMember;
	image?: string;
	live_type?: string;
	room_id?: string;
	live_id?: string;
	room_url_key?: string;
}

export interface LiveChatIDNMessage {
	id: string;
	user: string;
	text: string;
	avatar?: string;
	timestamp: number;
	type: 'chat' | 'gift' | 'letter' | 'system';
	systemType?: 'join' | 'other';
	joinNames?: string[];
	gift?: { name: string; img: string; color?: string };
	letterType?: string;
	recipient?: { name: string; avatar: string };
}

export interface LiveChatShowroomMessage {
	id: string;
	user: string;
	text: string;
	avatar?: string;
}
