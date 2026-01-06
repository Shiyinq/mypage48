import { browser } from '$app/environment';
import {
	PUBLIC_CLIENT_SIDE_API_BASE_URL,
	PUBLIC_SERVER_SIDE_API_BASE_URL
} from '$env/static/public';
import { logger } from '$lib/utils/logger';

/**
 * Validates required environment variables at runtime.
 * Should be called early in the application lifecycle (e.g., layout or client init).
 */
export function validateEnv() {
	const missing: string[] = [];

	if (browser) {
		if (!PUBLIC_CLIENT_SIDE_API_BASE_URL) missing.push('PUBLIC_CLIENT_SIDE_API_BASE_URL');
	} else {
		if (!PUBLIC_SERVER_SIDE_API_BASE_URL) missing.push('PUBLIC_SERVER_SIDE_API_BASE_URL');
	}

	if (missing.length > 0) {
		const msg = `Missing required environment variables: ${missing.join(', ')}`;
		logger.error(msg, new Error(msg), { context: 'EnvValidation' });
		// In development, we might want to throw to alert the developer immediately
		if (import.meta.env.DEV) {
			console.error(`[FATAL] ${msg}`);
		}
	} else {
		logger.info('Environment variables validated', { context: 'EnvValidation' });
	}
}
