import { eventsStore } from '$lib/stores/events';
import { browser } from '$app/environment';

export const load = async ({ url }) => {
	if (browser) {
		const now = new Date();
		const year = parseInt(url.searchParams.get('year') || now.getFullYear().toString());
		const month = parseInt(url.searchParams.get('month') || (now.getMonth() + 1).toString());

		setTimeout(() => {
			eventsStore.loadCalendar(year, month);
		}, 0);
	}
};
