/**
 * Calculate day name from date string (YYYY-MM-DD)
 * Returns English day name in uppercase (e.g., 'MONDAY')
 */
export function calculateDayFromDate(dateStr: string): string {
	const dateObj = new Date(dateStr);
	if (isNaN(dateObj.getTime())) return '';

	const days = ['SUNDAY', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY'];
	return days[dateObj.getDay()];
}

/**
 * Calculate gate open time (30 minutes before show time)
 * Returns time string in HH:mm format
 */
export function calculateGateOpenTime(showTime: string): string {
	const [h, m] = showTime.split(':').map(Number);
	if (isNaN(h) || isNaN(m)) return '';

	const d = new Date();
	d.setHours(h, m - 30);
	return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
}
