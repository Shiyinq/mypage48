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
	return formatDurationSeconds(diff, showSeconds);
}

/**
 * Format a duration in seconds into a human readable string.
 * @param seconds Duration in seconds
 * @param showSeconds If true, show seconds even when hours are present (default true)
 * @returns Formatted duration string
 */
export function formatDurationSeconds(seconds: number, showSeconds: boolean = true): string {
	const h = Math.floor(seconds / 3600);
	const m = Math.floor((seconds % 3600) / 60);
	const s = seconds % 60;

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

/**
 * Format a date into a relative time ago string using i18n.
 *
 * @param dateStr ISO date string
 * @param t Translation function
 * @returns Relative time string
 */
export function formatTimeAgo(
	dateStr: string | undefined | null,
	t: (key: string, vars?: Record<string, string | number>) => string
): string {
	if (!dateStr) return '';

	let parsedDateStr = dateStr;
	const timePart = dateStr.split('T')[1] || '';
	if (!dateStr.endsWith('Z') && !timePart.includes('+') && !timePart.includes('-')) {
		parsedDateStr = dateStr.trim().replace(' ', 'T');
		if (!parsedDateStr.includes('T')) {
			// fallback if it's just a date without time but no 'T'
			parsedDateStr = parsedDateStr + 'T00:00:00';
		}
		parsedDateStr += 'Z';
	}

	const date = new Date(parsedDateStr).getTime();
	if (isNaN(date)) return '';

	const diffMs = new Date().getTime() - date;
	const diffMins = Math.floor(diffMs / (1000 * 60));
	const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
	const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

	if (diffMins < 1) {
		return t('time.relative.justNow');
	} else if (diffMins < 60) {
		return t('time.relative.minsAgo', { count: diffMins });
	} else if (diffHours < 24) {
		return t('time.relative.hoursAgo', { count: diffHours });
	} else if (diffDays === 1) {
		return t('time.relative.yesterday');
	} else if (diffDays < 7) {
		return t('time.relative.daysAgo', { count: diffDays });
	} else {
		return t('time.relative.weeksAgo', { count: Math.floor(diffDays / 7) });
	}
}

/**
 * Ensures a date string is treated as UTC if it lacks timezone info.
 */
export function parseUTCDate(dateStr: string): Date {
	if (!dateStr) return new Date(NaN);
	const timePart = dateStr.split('T')[1] || '';
	if (!dateStr.endsWith('Z') && !timePart.includes('+') && !timePart.includes('-')) {
		return new Date(dateStr + 'Z');
	}
	return new Date(dateStr);
}

/**
 * Format a date for Live History with the given locale.
 */
export function formatLiveDate(dateStr: string, locale: string = 'id'): string {
	if (!dateStr) return '';
	const localeMap: Record<string, string> = { id: 'id-ID', en: 'en-US', ja: 'ja-JP' };
	return new Intl.DateTimeFormat(localeMap[locale] || 'id-ID', {
		day: 'numeric',
		month: 'short',
		year: 'numeric',
		hour: '2-digit',
		minute: '2-digit'
	}).format(parseUTCDate(dateStr));
}

/**
 * Format start and end date/time for live history.
 * If they are on the same day, only show the time for the end date.
 * If they are on different days, show the full date and time for the end date.
 */
export function formatLiveStartEnd(
	startAtStr: string | undefined | null,
	endAtStr: string | undefined | null,
	locale: string = 'id'
): string {
	if (!startAtStr) return '';
	const start = parseUTCDate(startAtStr);
	const formattedStart = formatLiveDate(startAtStr, locale);

	if (!endAtStr) return formattedStart;
	const end = parseUTCDate(endAtStr);
	if (isNaN(start.getTime()) || isNaN(end.getTime())) return formattedStart;

	const isSameDay =
		start.getFullYear() === end.getFullYear() &&
		start.getMonth() === end.getMonth() &&
		start.getDate() === end.getDate();

	const localeMap: Record<string, string> = { id: 'id-ID', en: 'en-US', ja: 'ja-JP' };
	const loc = localeMap[locale] || 'id-ID';

	if (isSameDay) {
		const formattedEndTime = new Intl.DateTimeFormat(loc, {
			timeStyle: 'short'
		}).format(end);
		return `${formattedStart} - ${formattedEndTime}`;
	} else {
		const formattedEndFull = formatLiveDate(endAtStr, locale);
		return `${formattedStart} - ${formattedEndFull}`;
	}
}
