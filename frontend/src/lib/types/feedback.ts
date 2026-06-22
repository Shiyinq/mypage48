import type { PaginationMeta } from './common';

export type FeedbackStatus =
	| 'pending'
	| 'noted'
	| 'in_progress'
	| 'implemented'
	| 'rejected'
	| 'spam';

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
	email?: string;
	status: FeedbackStatus;
	admin_notes?: string;
	created_at: string;
	user_id?: string;
}

export interface FeedbackPaginationResponse {
	data: FeedbackMessage[];
	meta: PaginationMeta;
}
