import { writable, get } from 'svelte/store';
import { setlistsApi, type Setlist, type SetlistDetailResponse } from '$lib/apis/setlists';
import { members as membersApi, type Member } from '$lib/apis/members';
import { logger } from '$lib/utils/logger';

// --- Setlists Store ---
interface SetlistsState {
	data: Setlist[] | null;
	loading: boolean;
	error: string | null;
	detailCache: Record<string, SetlistDetailResponse>;
	detailLoading: boolean;
	detailError: string | null;
}

function createSetlistsStore() {
	const initialState: SetlistsState = {
		data: null,
		loading: false,
		error: null,
		detailCache: {},
		detailLoading: false,
		detailError: null
	};

	const { subscribe, set, update } = writable<SetlistsState>(initialState);

	return {
		subscribe,
		load: async () => {
			const state = get({ subscribe });
			if (state.data) return; // Use cache if available

			update((s) => ({ ...s, loading: true, error: null }));

			try {
				const response = await setlistsApi.getAll();
				update((s) => ({
					...s,
					data: response.setlists,
					loading: false,
					error: null
				}));
				maxAttendanceStore.set(response.maxAttendance || 1);
			} catch (e) {
				logger.error('Failed to load setlists', e, { context: 'SetlistsStore' });
				update((s) => ({ ...s, loading: false, error: 'Failed to load setlists' }));
				throw e;
			}
		},
		loadDetail: async (id: string) => {
			const state = get({ subscribe });
			if (state.detailCache[id]) return state.detailCache[id];

			update((s) => ({ ...s, detailLoading: true, detailError: null }));

			try {
				const detail = await setlistsApi.getDetail(id);
				update((s) => ({
					...s,
					detailCache: { ...s.detailCache, [id]: detail },
					detailLoading: false,
					detailError: null
				}));
				return detail;
			} catch (e) {
				logger.error('Failed to load details', e, { context: 'SetlistsStore' });
				update((s) => ({ ...s, detailLoading: false, detailError: 'Failed to load detail' }));
				throw e;
			}
		},
		reset: () => set(initialState)
	};
}

export const setlistsStore = createSetlistsStore();
export const maxAttendanceStore = writable<number>(1);

// --- Members Store ---
interface MembersState {
	list: Member[];
	pagination: { page: number; hasMore: boolean };
	cache: Record<string, { members: Member[]; pagination: { page: number; hasMore: boolean } }>; // Cache by filter key
	generationsCache: string[] | null;
	currentFilter: { generation?: string; search?: string }; // Track current filter
	loading: boolean;
	error: string | null;
}

function createMembersStore() {
	const initialState: MembersState = {
		list: [],
		pagination: { page: 0, hasMore: true },
		cache: {},
		generationsCache: null,
		currentFilter: {},
		loading: false,
		error: null
	};

	const { subscribe, set, update } = writable<MembersState>(initialState);

	return {
		subscribe,
		load: async (
			params: { page?: number; limit?: number; generation?: string; search?: string } = {},
			reset = false
		) => {
			const state = get({ subscribe });
			const cacheKey = JSON.stringify({ generation: params.generation, search: params.search });

			// If resetting, check if we have this filter cached
			if (reset && state.cache[cacheKey]) {
				const cached = state.cache[cacheKey];
				update((s) => ({
					...s,
					list: cached.members,
					pagination: cached.pagination,
					currentFilter: { generation: params.generation, search: params.search },
					loading: false,
					error: null
				}));
				return;
			}

			// Check if we need to load more at all
			if (!reset && !state.pagination.hasMore) return;

			update((s) => ({ ...s, loading: true, error: null }));

			try {
				const pageToLoad = reset ? 1 : state.pagination.page + 1;

				const res = await membersApi.getAll({
					...params,
					page: pageToLoad,
					limit: params.limit || 20
				});

				update((s) => {
					const newList = reset ? res.data : [...s.list, ...res.data];
					const newPagination = {
						page: pageToLoad,
						hasMore: !!res.meta.next_page
					};

					return {
						...s,
						list: newList,
						pagination: newPagination,
						currentFilter: { generation: params.generation, search: params.search },
						loading: false,
						cache: {
							...s.cache,
							[cacheKey]: { members: newList, pagination: newPagination }
						}
					};
				});
			} catch (e) {
				logger.error('Failed to load members', e, { context: 'MembersStore' });
				update((s) => ({ ...s, loading: false, error: 'Failed to load members' }));
				throw e;
			}
		},
		getGenerations: async () => {
			const state = get({ subscribe });
			// Return cached generations if available
			if (state.generationsCache) {
				return state.generationsCache;
			}
			const generations = await membersApi.getGenerations();
			update((s) => ({ ...s, generationsCache: generations }));
			return generations;
		},
		reset: () => set(initialState)
	};
}

export const membersStore = createMembersStore();

// Backwards compatibility/Convenience exports for components that might need direct access (though mostly internal now)
export const membersPagination = {
	subscribe: (cb: (val: { page: number; hasMore: boolean }) => void) => {
		// Return a derived-like subscription to just pagination part
		// This is a temporary shim if needed, or we just refactor I to use $membersStore.pagination
		return membersStore.subscribe((val) => cb(val.pagination));
	}
};

export function invalidateTheater() {
	setlistsStore.reset();
	membersStore.reset();
}
