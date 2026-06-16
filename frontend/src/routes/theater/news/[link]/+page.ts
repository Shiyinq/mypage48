import { error } from '@sveltejs/kit';
import { news } from '$lib/apis/news';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params }) => {
	const { link } = params;

	try {
		// Fetch current news
		const item = await news.getNewsByLink(link);

		return {
			item
		};
	} catch (err) {
		// If the API throws an error (e.g., News Not Found),
		// we capture it and throw SvelteKit's built-in 404 error
		const e = err as { detail?: string };
		throw error(404, e?.detail || 'News not found');
	}
};
