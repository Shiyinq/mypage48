import type { ApiError } from '$lib/types/common';

/**
 * Type guard to check if an error is an ApiError.
 */
export function isApiError(error: unknown): error is ApiError {
	return typeof error === 'object' && error !== null && 'detail' in error;
}

/**
 * Helper to extract a user-friendly error message from an ApiError or unknown error.
 * Handles FastAPI validation errors (array of objects) and simple string errors.
 */
export function getErrorMessage(error: unknown): string {
	if (isApiError(error)) {
		const { detail } = error;
		if (typeof detail === 'string') {
			return detail;
		}
		if (Array.isArray(detail) && detail.length > 0) {
			// Handle array of validation errors - return the first one or join them
			// Usually { loc, msg, type }
			const firstError = detail[0];
			if (typeof firstError === 'object' && 'msg' in firstError) {
				return (firstError as { msg: string }).msg;
			}
		}
		if (typeof detail === 'object') {
			// Fallback for object with message property or stringify
			return (detail as { message?: string })?.message || JSON.stringify(detail);
		}
	}

	if (error instanceof Error) {
		return error.message;
	}

	if (typeof error === 'string') {
		return error;
	}

	return 'An unknown error occurred';
}
