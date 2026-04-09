import { eventsStore } from '$lib/stores/events';
import { browser } from '$app/environment';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ url }) => {
	if (browser) {
		const qYear = url.searchParams.get('year');
		const qMonth = url.searchParams.get('month');

		let year: number;
		let month: number;

		if (qYear && qMonth) {
			year = parseInt(qYear);
			month = parseInt(qMonth);
		} else {
			const now = new Date();
			year = now.getFullYear();
			month = now.getMonth() + 1;
		}

		// Defer store loading to next tick to avoid SvelteKit warning about using window.fetch during load
		setTimeout(() => {
			eventsStore.loadCalendar(year, month);
		}, 0);
	}
};
