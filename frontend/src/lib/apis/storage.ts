import { client } from './client';

export interface ImageUploadResponse {
    filename: string;
    url: string;
}

export interface PresignedUrlResponse {
    url: string;
    expires_in: number;
}

export type ImageCategory = 'ticket' | 'twoshot' | 'avatar';

export const storageApi = {
    /**
     * Upload a base64 encoded image to storage.
     * Returns the filename and presigned URL.
     */
    uploadImage: async (image: string, category: ImageCategory): Promise<ImageUploadResponse> => {
        return await client<ImageUploadResponse>('/storage/upload', {
            method: 'POST',
            body: { image, category }
        });
    },

    /**
     * Get a presigned URL for an existing image.
     */
    getImageUrl: async (filename: string): Promise<PresignedUrlResponse> => {
        return await client<PresignedUrlResponse>(`/storage/url/${encodeURIComponent(filename)}`, {
            method: 'GET'
        });
    }
};
