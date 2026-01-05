import { writable, get } from 'svelte/store';
import { setlistsApi, type Setlist, type SetlistDetailResponse } from '$lib/apis/setlists';
import { members as membersApi, type Member } from '$lib/apis/members';
import { logger } from '$lib/utils/logger';

// --- Setlists Store ---
function createSetlistsStore() {
	const { subscribe, set } = writable<Setlist[] | null>(null);
	const detailCache = writable<Record<string, SetlistDetailResponse>>({});

	return {
		subscribe,
		set,
		load: async () => {
			if (get({ subscribe })) return; // Use cache if available
			try {
				const response = await setlistsApi.getAll();
				set(response.setlists);
				maxAttendanceStore.set(response.maxAttendance || 1);
			} catch (e) {
				logger.error('Failed to load setlists', e, { context: 'SetlistsStore' });
				throw e;
			}
		},
		loadDetail: async (id: string) => {
			const cache = get(detailCache);
			if (cache[id]) return cache[id];

			try {
				const detail = await setlistsApi.getDetail(id);
				detailCache.update((c) => ({ ...c, [id]: detail }));
				return detail;
			} catch (e) {
				logger.error('Failed to load details', e, { context: 'SetlistsStore' });
				throw e;
			}
		},
		reset: () => {
			set(null);
			detailCache.set({});
		}
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
}

function createMembersStore() {
	const initialState: MembersState = {
		list: [],
		pagination: { page: 0, hasMore: true },
		cache: {},
		generationsCache: null,
		currentFilter: {}
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
					currentFilter: { generation: params.generation, search: params.search }
				}));
				return;
			}

			// Check if we need to load more at all
			if (!reset && !state.pagination.hasMore) return;

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
					cache: {
						...s.cache,
						[cacheKey]: { members: newList, pagination: newPagination }
					}
				};
			});
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
