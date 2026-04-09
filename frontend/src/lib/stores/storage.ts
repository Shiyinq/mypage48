import { writable, get } from 'svelte/store';
import { storageApi } from '$lib/apis/storage';
import type {
	ImageCategory,
	ImageUploadResponse,
	PresignedUrlResponse,
	BatchPresignedUrlResponse
} from '$lib/types';

function createStorageStore() {
	const { subscribe, update } = writable<Record<string, string>>({});

	return {
		subscribe,
		uploadImage: async (image: string, category: ImageCategory): Promise<ImageUploadResponse> => {
			const res = await storageApi.uploadImage(image, category);
			// Cache the URL immediately
			update((cache) => ({ ...cache, [res.filename]: res.url }));
			return res;
		},

		getImageUrl: async (filename: string): Promise<PresignedUrlResponse> => {
			const res = await storageApi.getImageUrl(filename);
			update((cache) => ({ ...cache, [filename]: res.url }));
			return res;
		},

		presignBulk: async (filenames: string[]): Promise<BatchPresignedUrlResponse> => {
			const cache = get({ subscribe });
			const toResolve = filenames.filter((f) => !cache[f]);

			if (toResolve.length === 0) {
				return { urls: {}, expires_in: 3600 };
			}

			const res = await storageApi.presignBulk(toResolve);
			update((currentCache) => ({ ...currentCache, ...res.urls }));
			return res;
		},

		clearCache: () => {
			update(() => ({}));
		},

		updateCache: (signatures: Record<string, string>) => {
			update((current) => ({ ...current, ...signatures }));
		}
	};
}

export const storageStore = createStorageStore();
