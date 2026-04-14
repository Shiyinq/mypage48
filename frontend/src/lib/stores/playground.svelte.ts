import { accessToken } from './accessToken.svelte';
import { playgroundApi } from '$lib/apis/playground';
import type { OpenAPISchema, OpenAPIEndpoint, ExecutionPayload, ExecutionResult } from '$lib/types';
import { logger } from '$lib/utils/logger';

/**
 * Playground store - migrated to Svelte 5 Shared Rune State.
 * Manages the API playground environment, schema, and execution results.
 */

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
	responseWidth: 450,
	useSession: false
};

const state = $state<PlaygroundState>(initialState);

// Internal derived state for endpoints
const endpoints = $derived.by(() => {
	if (!state.schema) return [];

	const endpoints: OpenAPIEndpoint[] = [];
	Object.entries(state.schema.paths).forEach(([path, methods]) => {
		Object.entries(methods).forEach(([method, details]) => {
			if (['summary', 'description', 'parameters', 'servers'].includes(method)) return;

			endpoints.push({
				id: `${method.toUpperCase()}:${path}`,
				method,
				path,
				details: details as OpenAPIEndpoint['details']
			});
		});
	});
	return endpoints;
});

// Internal derived state for grouping by tags
const groupedEndpoints = $derived.by(() => {
	const groups: Record<string, OpenAPIEndpoint[]> = {};
	endpoints.forEach((endpoint) => {
		const tag = endpoint.details.tags?.[0] || 'Default';
		if (!groups[tag]) groups[tag] = [];
		groups[tag].push(endpoint);
	});
	return groups;
});

// Internal derived state for selected endpoint
const selectedEndpoint = $derived.by(() => {
	return endpoints.find((e) => e.id === state.selectedEndpointId) || null;
});

// Internal derived state for selected result
const selectedResult = $derived.by(() => {
	if (!state.selectedEndpointId) return null;
	return state.results[state.selectedEndpointId] || null;
});

function createPlaygroundStore() {
	return {
		get schema() {
			return state.schema;
		},
		get selectedEndpointId() {
			return state.selectedEndpointId;
		},
		get results() {
			return state.results;
		},
		get executing() {
			return state.executing;
		},
		get error() {
			return state.error;
		},
		get apiKey() {
			return state.apiKey;
		},
		get isSidebarVisible() {
			return state.isSidebarVisible;
		},
		get responseWidth() {
			return state.responseWidth;
		},
		get useSession() {
			return state.useSession;
		},

		// Exposing derived state via getters
		get endpoints() {
			return endpoints;
		},
		get groupedEndpoints() {
			return groupedEndpoints;
		},
		get selectedEndpoint() {
			return selectedEndpoint;
		},
		get selectedResult() {
			return selectedResult;
		},

		init: async () => {
			if (state.schema) return;
			state.error = null;
			try {
				const fetchedSchema = await playgroundApi.getSchema();
				const savedApiKey =
					sessionStorage.getItem('mypage48_playground_apiKey') ||
					localStorage.getItem('mypage48_playground_apiKey');
				const savedUseSession = localStorage.getItem('mypage48_playground_useSession');

				if (localStorage.getItem('mypage48_playground_apiKey')) {
					localStorage.removeItem('mypage48_playground_apiKey');
				}

				const isDesktop = typeof window !== 'undefined' && window.innerWidth >= 768;

				state.schema = fetchedSchema;
				state.apiKey = savedApiKey;
				state.isSidebarVisible = isDesktop;
				state.responseWidth = 450;
				state.useSession = savedUseSession === 'true';
			} catch (err) {
				logger.error('Failed to load playground schema', err);
				state.error = 'Failed to load API metadata';
			}
		},

		toggleSidebar: () => {
			state.isSidebarVisible = !state.isSidebarVisible;
			localStorage.setItem('mypage48_playground_sidebarVisible', String(state.isSidebarVisible));
		},

		setResponseWidth: (width: number) => {
			state.responseWidth = width;
		},

		selectEndpoint: (id: string) => {
			state.selectedEndpointId = id;
		},

		setApiKey: (key: string | null) => {
			state.apiKey = key;
			if (key) {
				sessionStorage.setItem('mypage48_playground_apiKey', key);
			} else {
				sessionStorage.removeItem('mypage48_playground_apiKey');
			}
		},

		setUseSession: (value: boolean) => {
			state.useSession = value;
			localStorage.setItem('mypage48_playground_useSession', String(value));
		},

		execute: async (payload: ExecutionPayload) => {
			if (!state.selectedEndpointId) return;
			state.executing = true;

			try {
				if (state.useSession) {
					const token = accessToken.value;
					if (token) {
						payload.headers['Authorization'] = `Bearer ${token}`;
					}
				} else if (state.apiKey) {
					payload.headers['Authorization'] = `Bearer ${state.apiKey}`;
				}

				const result = await playgroundApi.executeRequest(payload);
				state.results = {
					...state.results,
					[state.selectedEndpointId]: result
				};
				return result;
			} catch (err) {
				logger.error('Execution failed', err);
			} finally {
				state.executing = false;
			}
		},

		reset: () => {
			Object.assign(state, initialState);
		},

		/**
		 * Legacy subscribe method for backward compatibility
		 */
		subscribe: (fn: (val: PlaygroundState) => void) => {
			$effect.root(() => {
				$effect(() => {
					fn(state);
				});
			});
			return () => {};
		}
	};
}

export const playgroundStore = createPlaygroundStore();
