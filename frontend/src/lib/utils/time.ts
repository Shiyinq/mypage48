/**
 * Time and duration related utility functions
 */

/**
 * Format a duration since a start date into a human readable string.
 * e.g., "1h 05m" or "45m 12s"
 *
 * @param startAt ISO date string
 * @param currentNow Current timestamp in milliseconds
 * @returns Formatted duration string
 */
/**
 * Format a duration since a start date into a human readable string.
 * e.g., "1h 05m 12s" or "45m 12s"
 *
 * @param startAt ISO date string
 * @param currentNow Current timestamp in milliseconds
 * @param showSeconds If true, show seconds even when hours are present (default true)
 * @returns Formatted duration string
 */
export function formatDuration(
	startAt: string | undefined | null,
	currentNow: number,
	showSeconds: boolean = true
): string {
	if (!startAt) return '';
	const start = new Date(startAt).getTime();
	if (isNaN(start)) return '';

	const diff = Math.max(0, Math.floor((currentNow - start) / 1000));
	const h = Math.floor(diff / 3600);
	const m = Math.floor((diff % 3600) / 60);
	const s = diff % 60;

	if (h > 0) {
		if (showSeconds) {
			return `${h}h ${m.toString().padStart(2, '0')}m ${s.toString().padStart(2, '0')}s`;
		}
		return `${h}h ${m.toString().padStart(2, '0')}m`;
	}
	return `${m}m ${s.toString().padStart(2, '0')}s`;
}

/**
 * Parses an Indonesian date string (e.g., "28 Mei 2009") into a JavaScript Date object.
 *
 * @param dateStr Indonesian date string
 * @returns Date object
 */
export function parseIndonesianDate(dateStr: string | undefined | null): Date {
	if (!dateStr) return new Date(NaN);

	const monthMap: { [key: string]: string } = {
		januari: 'January',
		februari: 'February',
		maret: 'March',
		april: 'April',
		mei: 'May',
		juni: 'June',
		juli: 'July',
		agustus: 'August',
		september: 'September',
		oktober: 'October',
		november: 'November',
		desember: 'December'
	};

	const parts = dateStr.split(' ');
	if (parts.length >= 3) {
		const day = parts[0];
		const month = parts[1].toLowerCase();
		const year = parts[2];
		const engMonth = monthMap[month] || month;
		return new Date(`${engMonth} ${day}, ${year}`);
	}
	return new Date(dateStr);
}
