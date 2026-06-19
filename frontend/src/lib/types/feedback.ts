export type FeedbackData = {
	type: 'issue' | 'suggestion' | 'other';
	message: string;
	email?: string;
	name?: string;
};

export interface FeedbackMessage {
	_id: string; // MongoDB ID (internal)
	id: string; // UUID (public)
	type: 'issue' | 'suggestion' | 'other';
	message: string;
	name?: string;
	created_at: string;
	user_id?: string;
}

export interface FeedbackPaginationResponse {
	data: FeedbackMessage[];
	page: number;
	limit: number;
	total: number;
	has_more: boolean;
}
