import { error } from '@sveltejs/kit';
import { news } from '$lib/apis/news';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params }) => {
	const { link } = params;

	try {
		const item = await news.getNewsByLink(link);

		return {
			item
		};
	} catch (err) {
		const e = err as { detail?: string };
		throw error(404, e?.detail || 'News not found');
	}
};
