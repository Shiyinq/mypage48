/**
 * File upload validation utilities
 * Provides security validation for file uploads
 */

export const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp'] as const;

export const MAX_FILE_SIZE_BYTES = 3 * 1024 * 1024; // 3 MB

export interface FileValidationResult {
	valid: boolean;
	error?: 'FILE_TOO_LARGE' | 'INVALID_TYPE' | 'NO_FILE';
}

/**
 * Validate a file for upload
 * Checks file type and size
 */
export function validateImageFile(file: File | null | undefined): FileValidationResult {
	if (!file) {
		return { valid: false, error: 'NO_FILE' };
	}

	// Check file size
	if (file.size > MAX_FILE_SIZE_BYTES) {
		return { valid: false, error: 'FILE_TOO_LARGE' };
	}

	// Check MIME type
	if (!ALLOWED_IMAGE_TYPES.includes(file.type as (typeof ALLOWED_IMAGE_TYPES)[number])) {
		return { valid: false, error: 'INVALID_TYPE' };
	}

	return { valid: true };
}

/**
 * Validate base64 image string
 * Checks if it's a valid image data URL and validates approximate size
 */
export function validateBase64Image(base64: string): FileValidationResult {
	if (!base64) {
		return { valid: false, error: 'NO_FILE' };
	}

	// Check if it starts with valid image data URL prefix
	const validPrefixes = ['data:image/jpeg', 'data:image/png', 'data:image/webp'];

	const hasValidPrefix = validPrefixes.some((prefix) => base64.startsWith(prefix));
	if (!hasValidPrefix) {
		return { valid: false, error: 'INVALID_TYPE' };
	}

	// Approximate file size from base64 length
	// Base64 increases size by ~33%, so original ≈ base64.length * 0.75
	const approximateSize = base64.length * 0.75;
	if (approximateSize > MAX_FILE_SIZE_BYTES) {
		return { valid: false, error: 'FILE_TOO_LARGE' };
	}

	return { valid: true };
}

/**
 * Get human-readable error message for validation result
 */
export function getValidationErrorMessage(error: FileValidationResult['error']): string {
	switch (error) {
		case 'FILE_TOO_LARGE':
			return 'File is too large. Maximum 3MB allowed.';
		case 'INVALID_TYPE':
			return 'File format not supported. Please use JPEG, PNG, or WebP.';
		case 'NO_FILE':
			return 'No file selected.';
		default:
			return 'An error occurred while validating the file.';
	}
}

/**
 * Get i18n key for validation error
 * Returns the key to use with $t() for localized messages
 */
export function getValidationErrorI18nKey(error: FileValidationResult['error']): string {
	switch (error) {
		case 'FILE_TOO_LARGE':
			return 'validation.alert.fileTooLarge';
		case 'INVALID_TYPE':
			return 'validation.alert.invalidType';
		case 'NO_FILE':
			return 'validation.alert.noFile';
		default:
			return 'validation.alert.noFile';
	}
}
