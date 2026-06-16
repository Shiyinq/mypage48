import { client } from './client';
import type {
	ImageCategory,
	ImageUploadResponse,
	PresignedUrlResponse,
	BatchPresignedUrlResponse
} from '$lib/types';

export const storageApi = {
	/**
	 * Upload a base64 encoded image to storage.
	 * Returns the filename and presigned URL.
	 */
	uploadImage: async (
		image: string,
		category: ImageCategory,
		slug?: string
	): Promise<ImageUploadResponse> => {
		return await client<ImageUploadResponse>('/storage/upload', {
			method: 'POST',
			body: { image, category, slug }
		});
	},

	/**
	 * Get a presigned URL for an existing image.
	 */
	getImageUrl: async (filename: string): Promise<PresignedUrlResponse> => {
		return await client<PresignedUrlResponse>(`/storage/url/${encodeURIComponent(filename)}`, {
			method: 'GET'
		});
	},

	/**
	 * Get presigned URLs for multiple images in bulk.
	 */
	presignBulk: async (filenames: string[]): Promise<BatchPresignedUrlResponse> => {
		return await client<BatchPresignedUrlResponse>('/storage/presign/bulk', {
			method: 'POST',
			body: { filenames }
		});
	}
};
