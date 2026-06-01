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

export const sorterApi = {
	saveSorterHistory: async (data: SorterCreateRequest) => {
		return await client<SorterResponse>('/theater/sorter', {
			method: 'POST',
			body: data as unknown as Record<string, unknown>
		});
	},

	getSorterHistories: async () => {
		return await client<SorterResponse[]>('/theater/sorter', {
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
	}
};
