import type { CalendarEvent } from '$lib/types/events';

/**
 * Returns the local frontend route for a calendar event, or a fallback to the external jkt48.com URL.
 *
 * @param event The calendar event.
 * @param basePath The current section's base path (e.g. '/theater' or '/jkt48').
 */
export function getEventUrl(event: CalendarEvent, basePath: string): string {
	const isBirthday = event.isBirthday || event.type === 'BIRTHDAY';
	const idMatch = event.url?.match(/\/id\/([a-zA-Z0-9]+)/);
	const id = event.id || (idMatch ? idMatch[1] : null);

	if (!id) return `https://jkt48.com${event.url}`;

	if (isBirthday) {
		if (basePath === '/jkt48') {
			return `/jkt48/members?id=${id}`;
		}
		return `${basePath}/members/${id}`;
	} else {
		return `${basePath}/events/${id}`;
	}
}
