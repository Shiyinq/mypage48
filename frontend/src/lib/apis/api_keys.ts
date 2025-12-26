import { client } from './client';
import type { APIKeysResponse } from '$lib/types';

export const apiKeys = {
	create: async (): Promise<APIKeysResponse> => {
		return client<APIKeysResponse>('/key', { method: 'POST' });
	},

	revoke: async (): Promise<APIKeysResponse> => {
		return client<APIKeysResponse>('/key', { method: 'DELETE' });
	}
};
