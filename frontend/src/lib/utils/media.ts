/**
 * Builds a proxied URL for external media (jkt48.com storage).
 *
 * Converts a relative path like `/media/jkt48-member/abigail_rachel.jpg`
 * into `/api/storage/external/media/jkt48-member/abigail_rachel.jpg`
 * which the backend proxies to jkt48.com to avoid cross-site blocking.
 */
export function getExternalMediaUrl(path: string | null | undefined): string {
	if (!path) return '';

	// Strip leading slash for consistent joining
	const cleanPath = path.replace(/^\/+/, '');

	return `/api/storage/external/${cleanPath}`;
}
