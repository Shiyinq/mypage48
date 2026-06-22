import { feedback as feedbackApi } from '$lib/apis/feedback';
import type { FeedbackPaginationResponse, FeedbackData } from '$lib/types';
import { logger } from '$lib/utils/logger';

/**
 * Feedback store - migrated to Svelte 5 Shared Rune State.
 * Manages the submission and retrieval of user feedback.
 */

interface FeedbackStoreState {
	data: import('$lib/types').FeedbackMessage[];
	meta: import('$lib/types').PaginationMeta;
	isLoading: boolean;
	isLoaded: boolean;
	error: string | null;
}

const initialState: FeedbackStoreState = {
	data: [],
	meta: {
		current_page: 1,
		last_page: 1,
		total_data: 0,
		per_page: 20,
		next_page: null
	},
	isLoading: false,
	isLoaded: false,
	error: null
};

const state = $state<FeedbackStoreState>(initialState);

function createFeedbackStore() {
	return {
		get data() {
			return state.data;
		},
		get meta() {
			return state.meta;
		},
		get isLoading() {
			return state.isLoading;
		},
		get isLoaded() {
			return state.isLoaded;
		},
		get error() {
			return state.error;
		},

		load: async (page = 1, limit = 20, statuses?: string[]) => {
			state.isLoading = true;
			state.error = null;
			try {
				const res = await feedbackApi.getAll(page, limit, statuses);
				state.data = res.data;
				state.meta = res.meta;
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

		loadMy: async (page = 1, limit = 20, force = false) => {
			if (state.isLoaded && !force) return { data: state.data, meta: state.meta };

			state.isLoading = true;
			state.error = null;
			try {
				const res = await feedbackApi.getMy(page, limit);
				state.data = res.data;
				state.meta = res.meta;
				state.error = null;
				state.isLoaded = true;
				return res;
			} catch (e) {
				logger.error('Failed to load user feedback', e, { context: 'FeedbackStore' });
				state.error = 'Failed to load user feedback';
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
				state.isLoaded = false; // Invalidate cache so it refetches next time
				return res;
			} catch (e) {
				logger.error('Failed to submit feedback', e, { context: 'FeedbackStore' });
				state.error = 'Failed to submit feedback';
				throw e;
			} finally {
				state.isLoading = false;
			}
		},

		updateStatus: async (id: string, status: string, admin_notes?: string) => {
			state.isLoading = true;
			state.error = null;
			try {
				const res = await feedbackApi.updateStatus(id, status, admin_notes);
				// Update in local state if exists
				const index = state.data.findIndex((f) => f.id === id);
				if (index !== -1) {
					state.data[index] = res;
				}
				state.error = null;
				return res;
			} catch (e) {
				logger.error('Failed to update feedback status', e, { context: 'FeedbackStore' });
				state.error = 'Failed to update status';
				throw e;
			} finally {
				state.isLoading = false;
			}
		},

		deleteFeedback: async (id: string) => {
			state.isLoading = true;
			state.error = null;
			try {
				await feedbackApi.delete(id);
				// Remove from local state
				state.data = state.data.filter((f) => f.id !== id);
				state.meta.total_data = Math.max(0, state.meta.total_data - 1);
				state.error = null;
			} catch (e) {
				logger.error('Failed to delete feedback', e, { context: 'FeedbackStore' });
				state.error = 'Failed to delete feedback';
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
		subscribe: (fn: (val: import('$lib/types').FeedbackPaginationResponse) => void) => {
			$effect.root(() => {
				$effect(() => {
					fn({
						data: state.data,
						meta: state.meta
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

export const loadFeedback = (page?: number, limit?: number, statuses?: string[]) =>
	feedbackStore.load(page, limit, statuses);
