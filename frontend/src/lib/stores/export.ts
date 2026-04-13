import { writable } from 'svelte/store';
import { exportApi, type ExportResponse } from '$lib/apis/export';
import { logger } from '$lib/utils/logger';

interface ExportStoreState {
	status: ExportResponse['status'];
	message: string;
	expiresAt?: string;
	error: string | null;
}

const initialState: ExportStoreState = {
	status: 'IDLE',
	message: '',
	expiresAt: undefined,
	error: null
};

// Separate loading states as per project pattern
export const isExportLoading = writable(false);
export const isExportProcessing = writable(false);
export const isExportDownloading = writable(false);

function createExportStore() {
	const { subscribe, set, update } = writable<ExportStoreState>(initialState);

	return {
		subscribe,

		loadStatus: async (silent = false) => {
			if (!silent) isExportLoading.set(true);
			update((s) => ({ ...s, error: null }));
			try {
				const res = await exportApi.getStatus();
				update((s) => ({
					...s,
					status: res.status,
					message: res.message || '',
					expiresAt: res.expires_at
				}));
				return res;
			} catch (e) {
				logger.error('Failed to get export status', e, { context: 'ExportStore' });
				update((s) => ({ ...s, error: 'Failed to load status' }));
				throw e;
			} finally {
				if (!silent) isExportLoading.set(false);
			}
		},

		initiate: async () => {
			isExportProcessing.set(true);
			update((s) => ({ ...s, error: null }));
			try {
				const res = await exportApi.initiateExport();
				update((s) => ({
					...s,
					status: res.status,
					message: res.message || '',
					expiresAt: res.expires_at
				}));
				return res;
			} catch (e) {
				logger.error('Failed to initiate export', e, { context: 'ExportStore' });
				update((s) => ({ ...s, error: 'Failed to initiate export' }));
				throw e;
			} finally {
				isExportProcessing.set(false);
			}
		},

		download: async () => {
			isExportDownloading.set(true);
			update((s) => ({ ...s, error: null }));
			try {
				const blob = await exportApi.download();
				return blob;
			} catch (e) {
				logger.error('Failed to download export', e, { context: 'ExportStore' });
				update((s) => ({ ...s, error: 'Failed to download' }));
				throw e;
			} finally {
				isExportDownloading.set(false);
			}
		},

		reset: () => {
			set(initialState);
			isExportLoading.set(false);
			isExportProcessing.set(false);
			isExportDownloading.set(false);
		}
	};
}

export const exportStore = createExportStore();
