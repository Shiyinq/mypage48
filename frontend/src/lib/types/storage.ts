export interface ImageUploadResponse {
	filename: string;
	url: string;
	blurHash?: string;
}

export interface PresignedUrlResponse {
	url: string;
	expires_in: number;
}

export type ImageCategory = 'ticket' | 'twoshot' | 'avatar' | 'journal';

export interface BatchPresignedUrlRequest {
	filenames: string[];
}

export interface BatchPresignedUrlResponse {
	urls: Record<string, string>;
	expires_in: number;
}
