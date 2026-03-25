export interface LiveMember {
	name: string;
	img: string;
	member_type?: string;
}

export interface LiveStatus {
	platform: 'showroom' | 'idn';
	room_id?: string;
	live_id?: string;
	room_url_key: string;
	view_num: number;
	title: string;
	member: LiveMember;
}

export interface StreamingUrl {
	url: string;
	label: string;
}

export interface LiveStreamingResponse {
	streaming_urls: StreamingUrl[];
	room_identifier: string;
	member: LiveMember;
}

export interface LiveChatIDNMessage {
	user: string;
	text: string;
	avatar?: string;
	type: 'chat' | 'gift';
	gift?: { name: string; img: string; color?: string };
}

export interface LiveChatShowroomMessage {
	id: string;
	user: string;
	text: string;
	avatar?: string;
}
