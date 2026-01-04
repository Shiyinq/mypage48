/**
 * Formatting utility functions used across the application
 */

/**
 * Format number as Indonesian Rupiah currency
 */
export function formatCurrency(value: number): string {
	return new Intl.NumberFormat('id-ID', {
		style: 'currency',
		currency: 'IDR',
		maximumFractionDigits: 0
	}).format(value);
}

/**
 * Format number as compact Indonesian Rupiah (e.g., 5M, 100K)
 */
export function formatCompactCurrency(value: number): string {
	return new Intl.NumberFormat('id-ID', {
		style: 'currency',
		currency: 'IDR',
		notation: 'compact'
	}).format(value);
}

/**
 * Format date string to Indonesian locale
 */
export function formatDate(dateStr: string, includeYear = false): string {
	const d = new Date(dateStr);
	const options: Intl.DateTimeFormatOptions = { day: 'numeric', month: 'short' };
	if (includeYear) options.year = 'numeric';
	return d.toLocaleDateString('id-ID', options);
}

/**
 * Format date with full options
 */
export function formatDateFull(dateStr: string): string {
	const d = new Date(dateStr);
	return d.toLocaleDateString('id-ID', {
		day: 'numeric',
		month: 'short',
		year: '2-digit'
	});
}
