/**
 * Cache expiration time in milliseconds (50 minutes).
 * Presigned URLs typically expire in 60 minutes, so we refresh slightly before.
 */
export const CACHE_EXPIRATION_MS = 50 * 60 * 1000;

/**
 * Checks if the given timestamp is older than the cache expiration time.
 * @param lastUpdated Timestamp of the last update in milliseconds.
 * @returns True if the cache is expired, false otherwise.
 */
export function isCacheExpired(lastUpdated: number): boolean {
	return Date.now() - lastUpdated > CACHE_EXPIRATION_MS;
}
