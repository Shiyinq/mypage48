import { storageApi } from '$lib/apis/storage';
import type {
	ImageCategory,
	ImageUploadResponse,
	PresignedUrlResponse,
	BatchPresignedUrlResponse
} from '$lib/types';

/**
 * Storage cache store - migrated to Svelte 5 Shared Rune State.
 * Manages presigned URL caching for images.
 */

let cache = $state<Record<string, string>>({});

function createStorageStore() {
	return {
		get cache() {
			return cache;
		},

		uploadImage: async (image: string, category: ImageCategory): Promise<ImageUploadResponse> => {
			const res = await storageApi.uploadImage(image, category);
			// Cache the URL immediately
			cache[res.filename] = res.url;
			return res;
		},

		getImageUrl: async (filename: string): Promise<PresignedUrlResponse> => {
			const res = await storageApi.getImageUrl(filename);
			cache[filename] = res.url;
			return res;
		},

		presignBulk: async (filenames: string[]): Promise<BatchPresignedUrlResponse> => {
			const toResolve = filenames.filter((f) => !cache[f]);

			if (toResolve.length === 0) {
				return { urls: {}, expires_in: 3600 };
			}

			const res = await storageApi.presignBulk(toResolve);
			// Update cache with new signatures
			Object.assign(cache, res.urls);
			return res;
		},

		clearCache: () => {
			cache = {};
		},

		updateCache: (signatures: Record<string, string>) => {
			Object.assign(cache, signatures);
		},

		/**
		 * Legacy subscribe method for backward compatibility
		 */
		subscribe: (fn: (val: Record<string, string>) => void) => {
			$effect.root(() => {
				$effect(() => {
					fn(cache);
				});
			});
			return () => {};
		}
	};
}

export const storageStore = createStorageStore();
