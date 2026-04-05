/**
 * Cleanses markdown content by converting full presigned storage URLs 
 * back into their relative internal paths (e.g., journal/xyz.png).
 * This ensures that the editor remains clean and prevents saving 
 * temporary presigned URLs into the database.
 */
export function cleanseMarkdown(content: string | null | undefined): string {
	if (!content) return '';

	// Matches full MinIO URLs containing our categories, followed by optional query params
	// Captures the internal path (e.g., journal/filename.png)
	const storageUrlRegex = /https?:\/\/[^/)]+\/[^/)]+\/((journal|ticket|twoshot|avatar)\/[^?\s)]+)(\?[^)\s]+)?/g;

	return content.replace(storageUrlRegex, (_, internalPath) => {
		return internalPath;
	});
}

/**
 * Extracts internal paths and their full presigned URLs from markdown.
 * Used to populate the cache before cleansing.
 */
export function extractSignatures(content: string | null | undefined): Record<string, string> {
	if (!content) return {};

	const signatures: Record<string, string> = {};
	const storageUrlRegex = /https?:\/\/[^/)]+\/[^/)]+\/((journal|ticket|twoshot|avatar)\/[^?\s)]+)(\?[^)\s]+)?/g;

	let match;
	while ((match = storageUrlRegex.exec(content)) !== null) {
		const internalPath = match[1];
		const fullUrl = match[0];
		signatures[internalPath] = fullUrl;
	}

	return signatures;
}
