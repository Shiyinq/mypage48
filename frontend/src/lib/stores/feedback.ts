import { writable } from 'svelte/store';
import { feedback as feedbackApi } from '$lib/apis/feedback';
import type { FeedbackPaginationResponse, FeedbackData } from '$lib/types';

import { logger } from '$lib/utils/logger';

export const isFeedbackLoading = writable(false);

function createFeedbackStore() {
	const initialState: FeedbackPaginationResponse = {
		data: [],
		page: 1,
		limit: 20,
		total: 0,
		has_more: false
	};

	const { subscribe, set, update } = writable<FeedbackPaginationResponse>(initialState);

	return {
		subscribe,
		set,
		update,
		load: async (page = 1, limit = 20) => {
			isFeedbackLoading.set(true);
			try {
				const res = await feedbackApi.getAll(page, limit);
				set(res);
				return res;
			} catch (e) {
				logger.error('Failed to load feedback', e, { context: 'FeedbackStore' });
				throw e;
			} finally {
				isFeedbackLoading.set(false);
			}
		},
		submit: async (data: FeedbackData) => {
			isFeedbackLoading.set(true);
			try {
				const res = await feedbackApi.submit(data);
				return res;
			} catch (e) {
				logger.error('Failed to submit feedback', e, { context: 'FeedbackStore' });
				throw e;
			} finally {
				isFeedbackLoading.set(false);
			}
		}
	};
}

export const feedbackStore = createFeedbackStore();

// Deprecated: loadFeedback is now part of the store, but keeping for backward compatibility if needed
// though we will refactor usage to feedbackStore.load
export const loadFeedback = feedbackStore.load;
