import { sorterApi } from '$lib/apis/sorter';
import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const ssr = false;

export const load: PageLoad = async ({ params }) => {
	try {
		const historyItem = await sorterApi.getSorterHistory(params.id);
		return { historyItem };
	} catch (_e) {
		throw error(404, 'Sorter history not found');
	}
};
