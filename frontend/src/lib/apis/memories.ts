import { client } from './client';
import type { MemoriesPaginationResponse, MemoryFilterType, TopTwoShotResponse } from '../types';

export const memoriesApi = {
	getMemories: async (page = 1, limit = 20, type?: MemoryFilterType) => {
		const query = new URLSearchParams({
			page: page.toString(),
			limit: limit.toString()
		});

		if (type && type !== 'ALL') {
			query.append('type', type);
		}

		return await client<MemoriesPaginationResponse>(`/memories?${query.toString()}`, {
			method: 'GET'
		});
	},

	getTopTwoShot: async () => {
		return await client<TopTwoShotResponse>('/memories/top-two-shot', {
			method: 'GET'
		});
	}
};
