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
 * Convert gold to IDR based on platform.
 *
 * Showroom: 1 G = 1 JPY, kurs Rp 111.50/JPY (4 Jul 2026) → gold * 111.5
 * IDN:      3 gold = Rp 7.500 → 1 gold = Rp 2.500
 */
export function goldToIdr(gold: number, isShowroom: boolean): number {
	return isShowroom ? gold * 111.5 : (gold * 7500) / 3;
}

/**
 * Format gold to IDR string
 */
export function formatGoldToIdr(gold: number, isShowroom: boolean): string {
	return goldToIdr(gold, isShowroom).toLocaleString('id-ID');
}

/**
 * Mask an email address
 */
export function maskEmail(emailStr: string | undefined | null): string {
	if (!emailStr) return '-';
	const parts = emailStr.split('@');
	if (parts.length !== 2) return '••••••••••••';
	const name = parts[0];
	const domain = parts[1];
	const maskedName = name.length > 2 ? name.substring(0, 2) + '•••' : '•••';
	return `${maskedName}@${domain}`;
}
