import { writable, derived, get } from 'svelte/store';
import { accessToken } from './accessToken';
import { playgroundApi } from '$lib/apis/playground';
import type { OpenAPISchema, OpenAPIEndpoint, ExecutionPayload, ExecutionResult } from '$lib/types';
import { logger } from '$lib/utils/logger';

interface PlaygroundState {
	schema: OpenAPISchema | null;
	selectedEndpointId: string | null;
	results: Record<string, ExecutionResult>;
	executing: boolean;
	error: string | null;
	apiKey: string | null;
	isSidebarVisible: boolean;
	responseWidth: number;
	useSession: boolean;
}

const initialState: PlaygroundState = {
	schema: null,
	selectedEndpointId: null,
	results: {},
	executing: false,
	error: null,
	apiKey: null,
	isSidebarVisible: true,
	responseWidth: 450, // Default pixel width
	useSession: false
};

function createPlaygroundStore() {
	const { subscribe, set, update } = writable<PlaygroundState>(initialState);

	return {
		subscribe,
		init: async () => {
			update((s) => ({ ...s, error: null }));
			try {
				const schema = await playgroundApi.getSchema();
				const savedApiKey =
					sessionStorage.getItem('mypage48_playground_apiKey') ||
					localStorage.getItem('mypage48_playground_apiKey');
				const savedUseSession = localStorage.getItem('mypage48_playground_useSession');

				// Cleanup legacy insecure storage if migrated
				if (localStorage.getItem('mypage48_playground_apiKey')) {
					localStorage.removeItem('mypage48_playground_apiKey');
				}

				// Initialize sidebar visibility based on screen width on every refresh/load
				const isDesktop = typeof window !== 'undefined' && window.innerWidth >= 768;

				update((s) => ({
					...s,
					schema,
					apiKey: savedApiKey,
					isSidebarVisible: isDesktop,
					responseWidth: 450, // Always use default on refresh
					useSession: savedUseSession === 'true'
				}));
			} catch (err: any) {
				logger.error('Failed to load playground schema', err);
				update((s) => ({ ...s, error: 'Failed to load API metadata' }));
			}
		},

		toggleSidebar: () => {
			update((s) => {
				const newValue = !s.isSidebarVisible;
				localStorage.setItem('mypage48_playground_sidebarVisible', String(newValue));
				return { ...s, isSidebarVisible: newValue };
			});
		},

		setResponseWidth: (width: number) => {
			update((s) => ({ ...s, responseWidth: width }));
		},

		selectEndpoint: (id: string) => {
			update((s) => ({ ...s, selectedEndpointId: id }));
		},

		setApiKey: (key: string | null) => {
			update((s) => ({ ...s, apiKey: key }));
			if (key) {
				sessionStorage.setItem('mypage48_playground_apiKey', key);
			} else {
				sessionStorage.removeItem('mypage48_playground_apiKey');
			}
		},

		setUseSession: (value: boolean) => {
			update((s) => {
				localStorage.setItem('mypage48_playground_useSession', String(value));
				return { ...s, useSession: value };
			});
		},

		execute: async (payload: ExecutionPayload) => {
			const currentId = get({ subscribe }).selectedEndpointId;
			if (!currentId) return;

			update((s) => ({ ...s, executing: true }));
			try {
				const state = get({ subscribe });

				if (state.useSession) {
					const token = get(accessToken);
					if (token) {
						payload.headers['Authorization'] = `Bearer ${token}`;
					}
				} else if (state.apiKey) {
					payload.headers['Authorization'] = `Bearer ${state.apiKey}`;
				}

				const result = await playgroundApi.executeRequest(payload);
				update((s) => ({
					...s,
					results: {
						...s.results,
						[currentId]: result
					}
				}));
				return result;
			} catch (err: any) {
				logger.error('Execution failed', err);
			} finally {
				update((s) => ({ ...s, executing: false }));
			}
		},

		reset: () => set(initialState)
	};
}

export const playgroundStore = createPlaygroundStore();

// Derived store to get the list of endpoints from schema
export const endpoints = derived(playgroundStore, ($store) => {
	if (!$store.schema) return [];

	const endpoints: OpenAPIEndpoint[] = [];
	Object.entries($store.schema.paths).forEach(([path, methods]) => {
		Object.entries(methods).forEach(([method, details]: [string, any]) => {
			// Skip internal/special fields if any
			if (['summary', 'description', 'parameters', 'servers'].includes(method)) return;

			endpoints.push({
				id: `${method.toUpperCase()}:${path}`,
				method,
				path,
				details
			});
		});
	});
	return endpoints;
});

// Derived store for grouping by tags
export const groupedEndpoints = derived(endpoints, ($endpoints) => {
	const groups: Record<string, OpenAPIEndpoint[]> = {};
	$endpoints.forEach((endpoint) => {
		const tag = endpoint.details.tags?.[0] || 'Default';
		if (!groups[tag]) groups[tag] = [];
		groups[tag].push(endpoint);
	});
	return groups;
});

// Derived store for selected endpoint
export const selectedEndpoint = derived([playgroundStore, endpoints], ([$store, $endpoints]) => {
	return $endpoints.find((e) => e.id === $store.selectedEndpointId) || null;
});

// Derived store for selected result
export const selectedResult = derived(playgroundStore, ($store) => {
	if (!$store.selectedEndpointId) return null;
	return $store.results[$store.selectedEndpointId] || null;
});
