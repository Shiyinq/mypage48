import { client } from './client';

export interface SorterResultItem {
	id: string;
	name: string;
	rank: number;
}

export interface SorterCreateRequest {
	title: string;
	description?: string;
	filters: string[];
	results: SorterResultItem[];
}

export interface SorterResponse {
	_id: string;
	user_id: string;
	title: string;
	description?: string;
	filters: string[];
	results: SorterResultItem[];
	created_at: string;
	updated_at: string;
}

export interface SorterPaginationResponse {
	data: SorterResponse[];
	meta: {
		current_page: number;
		last_page: number;
		total_data: number;
		per_page: number;
		next_page: number | null;
	};
}

export const sorterApi = {
	saveSorterHistory: async (data: SorterCreateRequest) => {
		return await client<SorterResponse>('/theater/sorter', {
			method: 'POST',
			body: data as unknown as Record<string, unknown>
		});
	},

	getSorterHistories: async (page: number = 1, limit: number = 15) => {
		return await client<SorterPaginationResponse>(`/theater/sorter?page=${page}&limit=${limit}`, {
			method: 'GET'
		});
	},

	getSorterHistory: async (id: string) => {
		return await client<SorterResponse>(`/theater/sorter/${id}`, {
			method: 'GET'
		});
	},

	deleteSorterHistory: async (id: string) => {
		return await client<void>(`/theater/sorter/${id}`, {
			method: 'DELETE'
		});
	},

	updateSorterHistory: async (id: string, data: { title?: string; description?: string }) => {
		return await client<SorterResponse>(`/theater/sorter/${id}`, {
			method: 'PATCH',
			body: data as unknown as Record<string, unknown>
		});
	}
};
