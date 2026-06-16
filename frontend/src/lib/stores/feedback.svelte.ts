import { feedback as feedbackApi } from '$lib/apis/feedback';
import type { FeedbackPaginationResponse, FeedbackData } from '$lib/types';
import { logger } from '$lib/utils/logger';

/**
 * Feedback store - migrated to Svelte 5 Shared Rune State.
 * Manages the submission and retrieval of user feedback.
 */

interface FeedbackStoreState extends FeedbackPaginationResponse {
	isLoading: boolean;
	error: string | null;
}

const initialState: FeedbackStoreState = {
	data: [],
	page: 1,
	limit: 20,
	total: 0,
	has_more: false,
	isLoading: false,
	error: null
};

const state = $state<FeedbackStoreState>(initialState);

function createFeedbackStore() {
	return {
		get data() {
			return state.data;
		},
		get page() {
			return state.page;
		},
		get limit() {
			return state.limit;
		},
		get total() {
			return state.total;
		},
		get has_more() {
			return state.has_more;
		},
		get isLoading() {
			return state.isLoading;
		},
		get error() {
			return state.error;
		},

		load: async (page = 1, limit = 20) => {
			state.isLoading = true;
			state.error = null;
			try {
				const res = await feedbackApi.getAll(page, limit);
				Object.assign(state, res);
				state.error = null;
				return res;
			} catch (e) {
				logger.error('Failed to load feedback', e, { context: 'FeedbackStore' });
				state.error = 'Failed to load feedback';
				throw e;
			} finally {
				state.isLoading = false;
			}
		},

		submit: async (data: FeedbackData) => {
			state.isLoading = true;
			state.error = null;
			try {
				const res = await feedbackApi.submit(data);
				state.error = null;
				return res;
			} catch (e) {
				logger.error('Failed to submit feedback', e, { context: 'FeedbackStore' });
				state.error = 'Failed to submit feedback';
				throw e;
			} finally {
				state.isLoading = false;
			}
		},

		reset: () => {
			Object.assign(state, initialState);
		},

		/**
		 * Legacy subscribe method for backward compatibility
		 */
		subscribe: (fn: (val: FeedbackPaginationResponse) => void) => {
			$effect.root(() => {
				$effect(() => {
					fn({
						data: state.data,
						page: state.page,
						limit: state.limit,
						total: state.total,
						has_more: state.has_more
					});
				});
			});
			return () => {};
		}
	};
}

export const feedbackStore = createFeedbackStore();

// Compatibility aliases
export const isFeedbackLoading = {
	get value() {
		return state.isLoading;
	},
	subscribe: (fn: (val: boolean) => void) => {
		$effect.root(() => {
			$effect(() => fn(state.isLoading));
		});
		return () => {};
	}
};

export const loadFeedback = (page?: number, limit?: number) => feedbackStore.load(page, limit);
