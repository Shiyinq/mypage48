import { newsStore } from '$lib/stores/news.svelte';
import { browser } from '$app/environment';

export const load = async ({ url }) => {
	const page = Number(url.searchParams.get('page')) || 1;
	if (browser) {
		newsStore.load(page);
	}
};
