import { storageApi } from '$lib/apis/storage';
import type { ImageCategory, ImageUploadResponse, PresignedUrlResponse } from '$lib/types';

function createStorageStore() {
	return {
		uploadImage: async (image: string, category: ImageCategory): Promise<ImageUploadResponse> => {
			return await storageApi.uploadImage(image, category);
		},

		getImageUrl: async (filename: string): Promise<PresignedUrlResponse> => {
			return await storageApi.getImageUrl(filename);
		}
	};
}

export const storageStore = createStorageStore();
