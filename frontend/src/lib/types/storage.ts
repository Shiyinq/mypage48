export interface ImageUploadResponse {
    filename: string;
    url: string;
}

export interface PresignedUrlResponse {
    url: string;
    expires_in: number;
}

export type ImageCategory = 'ticket' | 'twoshot' | 'avatar';
