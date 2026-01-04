/**
 * Time-related constants used across the application
 */

export const MONTHS = [
	'January',
	'February',
	'March',
	'April',
	'May',
	'June',
	'July',
	'August',
	'September',
	'October',
	'November',
	'December'
] as const;

export const DAYS = [
	'Sunday',
	'Monday',
	'Tuesday',
	'Wednesday',
	'Thursday',
	'Friday',
	'Saturday'
] as const;

export const THEATER_ROWS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'] as const;

export type Month = (typeof MONTHS)[number];
export type Day = (typeof DAYS)[number];
export type TheaterRow = (typeof THEATER_ROWS)[number];
