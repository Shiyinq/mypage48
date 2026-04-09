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
