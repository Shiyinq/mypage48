import { sorterApi } from '$lib/apis/sorter';
import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const ssr = false;

export const load: PageLoad = async ({ params }) => {
	if (params.id.startsWith('local-')) {
		return { isLocal: true, id: params.id };
	}
	try {
		const historyItem = await sorterApi.getSorterHistory(params.id);
		return { isLocal: false, historyItem };
	} catch (_e) {
		throw error(404, 'Sorter history not found');
	}
};
