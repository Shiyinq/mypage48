import { client } from './client';
import type { FeedbackData, FeedbackMessage, FeedbackPaginationResponse } from '$lib/types';

export const feedback = {
	submit: async (data: FeedbackData) => {
		return client<FeedbackMessage>('/feedback', {
			method: 'POST',
			body: data
		});
	},

	getAll: async (page = 1, limit = 20, statuses?: string[]) => {
		const params = new URLSearchParams();
		params.append('page', page.toString());
		params.append('limit', limit.toString());
		if (statuses && statuses.length > 0) {
			statuses.forEach((s) => params.append('status', s));
		}
		return client<FeedbackPaginationResponse>(`/feedback?${params.toString()}`);
	},

	getMy: async (page = 1, limit = 20) => {
		return client<FeedbackPaginationResponse>(`/feedback/me?page=${page}&limit=${limit}`);
	},

	updateStatus: async (id: string, status: string, admin_notes?: string) => {
		return client<FeedbackMessage>(`/feedback/${id}/status`, {
			method: 'PATCH',
			body: { status, admin_notes }
		});
	},

	delete: async (id: string) => {
		return client<void>(`/feedback/${id}`, {
			method: 'DELETE'
		});
	}
};
