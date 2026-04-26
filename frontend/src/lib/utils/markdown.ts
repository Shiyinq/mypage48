/**
 * Regex to match full storage proxy URLs containing our categories.
 * Handles multiple path segments after the domain (e.g., /api/storage/m/).
 * Captures the internal path in group 1 (e.g., journal/filename.png).
 */
export const STORAGE_URL_REGEX =
	/https?:\/\/[^/)]+\/(?:[^/)]+\/)*?((?:media\/)?(journal|ticket|twoshot|avatar|member|setlist|jkt48-member|setlists)\/[^?\s)]+)(?:\?[^)\s]*)?/g;

/**
 * Cleanses markdown content by converting full presigned storage URLs
 * back into their relative internal paths (e.g., journal/xyz.png).
 * This ensures that the editor remains clean and prevents saving
 * temporary presigned URLs into the database.
 */
export function cleanseMarkdown(content: string | null | undefined): string {
	if (!content) return '';

	return content.replace(STORAGE_URL_REGEX, (_, internalPath) => {
		return internalPath;
	});
}

/**
 * Cleanses a single storage URL by converting it back into its relative internal path.
 * Example: http://localhost:8080/api/storage/m/ticket/xyz.png?expires=...
 * becomes: ticket/xyz.png
 */
export function cleanseStorageUrl(url: string | null | undefined): string {
	if (!url) return '';
	if (url.startsWith('data:')) return url; // Keep base64 as-is

	// Reuse the regex to extract the internal path
	// We need to reset the regex because it has the 'g' flag
	const regex = new RegExp(STORAGE_URL_REGEX.source);
	const match = regex.exec(url);

	if (match) {
		return match[1];
	}

	return url;
}

/**
 * Extracts internal paths and their full presigned URLs from markdown.
 * Used to populate the cache before cleansing.
 */
export function extractSignatures(content: string | null | undefined): Record<string, string> {
	if (!content) return {};

	const signatures: Record<string, string> = {};

	// Use a new instance of the regex for exec loop to avoid index issues if g flag is used
	const regex = new RegExp(STORAGE_URL_REGEX.source, 'g');
	let match;
	while ((match = regex.exec(content)) !== null) {
		const internalPath = match[1];
		const fullUrl = match[0];
		signatures[internalPath] = fullUrl;
	}

	return signatures;
}
