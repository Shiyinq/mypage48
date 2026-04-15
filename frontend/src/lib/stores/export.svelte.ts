import { exportApi, type ExportResponse } from '$lib/apis/export';
import { logger } from '$lib/utils/logger';

/**
 * Export store - migrated to Svelte 5 Shared Rune State.
 * Manages the status, initiation, and downloading of data exports.
 */

interface ExportStoreState {
	status: ExportResponse['status'];
	message: string;
	expiresAt?: string;
	error: string | null;
	isLoading: boolean;
	isProcessing: boolean;
	isDownloading: boolean;
}

const initialState: ExportStoreState = {
	status: 'IDLE',
	message: '',
	expiresAt: undefined,
	error: null,
	isLoading: false,
	isProcessing: false,
	isDownloading: false
};

const state = $state<ExportStoreState>(initialState);

function createExportStore() {
	return {
		get status() {
			return state.status;
		},
		get message() {
			return state.message;
		},
		get expiresAt() {
			return state.expiresAt;
		},
		get error() {
			return state.error;
		},
		get isLoading() {
			return state.isLoading;
		},
		get isProcessing() {
			return state.isProcessing;
		},
		get isDownloading() {
			return state.isDownloading;
		},

		loadStatus: async (silent = false) => {
			if (!silent) state.isLoading = true;
			state.error = null;
			try {
				const res = await exportApi.getStatus();
				state.status = res.status;
				state.message = res.message || '';
				state.expiresAt = res.expires_at;
				return res;
			} catch (e) {
				logger.error('Failed to get export status', e, { context: 'ExportStore' });
				state.error = 'Failed to load status';
				throw e;
			} finally {
				if (!silent) state.isLoading = false;
			}
		},

		initiate: async () => {
			state.isProcessing = true;
			state.error = null;
			try {
				const res = await exportApi.initiateExport();
				state.status = res.status;
				state.message = res.message || '';
				state.expiresAt = res.expires_at;
				return res;
			} catch (e) {
				logger.error('Failed to initiate export', e, { context: 'ExportStore' });
				state.error = 'Failed to initiate export';
				throw e;
			} finally {
				state.isProcessing = false;
			}
		},

		download: async () => {
			state.isDownloading = true;
			state.error = null;
			try {
				const blob = await exportApi.download();
				return blob;
			} catch (e) {
				logger.error('Failed to download export', e, { context: 'ExportStore' });
				state.error = 'Failed to download';
				throw e;
			} finally {
				state.isDownloading = false;
			}
		},

		reset: () => {
			Object.assign(state, initialState);
		},

		/**
		 * Legacy subscribe method for backward compatibility
		 */
		subscribe: (
			fn: (val: {
				status: ExportResponse['status'];
				message: string;
				expiresAt?: string;
				error: string | null;
			}) => void
		) => {
			$effect.root(() => {
				$effect(() => {
					fn({
						status: state.status,
						message: state.message,
						expiresAt: state.expiresAt,
						error: state.error
					});
				});
			});
			return () => {};
		}
	};
}

export const exportStore = createExportStore();

// Compatibility aliases
export const isExportLoading = {
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

export const isExportProcessing = {
	get value() {
		return state.isProcessing;
	},
	subscribe: (fn: (val: boolean) => void) => {
		$effect.root(() => {
			$effect(() => fn(state.isProcessing));
		});
		return () => {};
	}
};

export const isExportDownloading = {
	get value() {
		return state.isDownloading;
	},
	subscribe: (fn: (val: boolean) => void) => {
		$effect.root(() => {
			$effect(() => fn(state.isDownloading));
		});
		return () => {};
	}
};
