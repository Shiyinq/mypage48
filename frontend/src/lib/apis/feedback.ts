import { client } from './client';
import type { FeedbackData, FeedbackMessage, FeedbackPaginationResponse } from '$lib/types';

export const feedback = {
	submit: async (data: FeedbackData) => {
		return client<FeedbackMessage>('/feedback', {
			method: 'POST',
			body: data
		});
	},

	getAll: async (page = 1, limit = 20) => {
		return client<FeedbackPaginationResponse>(`/feedback?page=${page}&limit=${limit}`);
	}
};
