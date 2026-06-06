import { client } from './client';
import type { MemoriesPaginationResponse, MemoryFilters, TopTwoShotResponse } from '../types';

export const memoriesApi = {
	getMemories: async (page = 1, limit = 20, filters?: MemoryFilters) => {
		const query = new URLSearchParams({
			page: page.toString(),
			limit: limit.toString()
		});

		if (filters) {
			if (filters.type && filters.type !== 'ALL') {
				query.append('type', filters.type);
			}
			if (filters.title) {
				query.append('title', filters.title);
			}
			if (filters.startDate) {
				query.append('start_date', filters.startDate);
			}
			if (filters.endDate) {
				query.append('end_date', filters.endDate);
			}
			if (filters.days && filters.days.length > 0) {
				query.append('days', filters.days.join(','));
			}
		}

		return await client<MemoriesPaginationResponse>(`/memories?${query.toString()}`, {
			method: 'GET'
		});
	},

	getTopTwoShot: async (filters?: {
		selectedYear?: number;
		startMonth?: number;
		endMonth?: number;
		isAllData?: boolean;
	}) => {
		const query = new URLSearchParams();
		if (filters) {
			if (filters.selectedYear !== undefined) query.append('year', filters.selectedYear.toString());
			if (filters.startMonth !== undefined)
				query.append('start_month', filters.startMonth.toString());
			if (filters.endMonth !== undefined) query.append('end_month', filters.endMonth.toString());
			if (filters.isAllData !== undefined)
				query.append('is_all_data', filters.isAllData.toString());
		}

		return await client<TopTwoShotResponse>(`/memories/top-two-shot?${query.toString()}`, {
			method: 'GET'
		});
	}
};
