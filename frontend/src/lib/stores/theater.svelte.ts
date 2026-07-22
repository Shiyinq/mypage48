import {
	setlistsApi,
	type Setlist,
	type SetlistDetailResponse,
	type SetlistOption
} from '$lib/apis/setlists';
import { members as membersApi, type Member, type BirthdayResponse } from '$lib/apis/members';
import { logger } from '$lib/utils/logger';
import { createRequestDedup } from '$lib/utils/requestDedup';

/**
 * Theater store - migrated to Svelte 5 Shared Rune State.
 * Manages setlists, member listings, birthdays, and seat map availability.
 */

// --- Setlists Store ---
interface SetlistsState {
	data: Setlist[] | null;
	error: string | null;
	detailCache: Record<string, SetlistDetailResponse>;
	detailError: string | null;
	isSetlistsLoading: boolean;
	isSetlistDetailLoading: boolean;
	maxAttendance: number;
	lastFilterKey: string | null;
	options: SetlistOption[] | null;
	isOptionsLoading: boolean;
}

const initialSetlistsState: SetlistsState = {
	data: null,
	error: null,
	detailCache: {},
	detailError: null,
	isSetlistsLoading: false,
	isSetlistDetailLoading: false,
	maxAttendance: 1,
	lastFilterKey: null,
	options: null,
	isOptionsLoading: false
};

const setlistsState = $state<SetlistsState>(initialSetlistsState);
const setlistsDedup = createRequestDedup();

let globalTicketSlideIndex = $state(0);
let ticketSlideTimer: ReturnType<typeof setInterval> | null = null;

function ensureTicketSlideTimer() {
	if (typeof window !== 'undefined' && !ticketSlideTimer) {
		ticketSlideTimer = setInterval(() => {
			globalTicketSlideIndex = (globalTicketSlideIndex + 1) % 2;
		}, 10000);
	}
}

function createSetlistsStore() {
	return {
		get data() {
			return setlistsState.data;
		},
		get error() {
			return setlistsState.error;
		},
		get detailCache() {
			return setlistsState.detailCache;
		},
		get detailError() {
			return setlistsState.detailError;
		},
		get isLoading() {
			return setlistsState.isSetlistsLoading;
		},
		get isDetailLoading() {
			return setlistsState.isSetlistDetailLoading;
		},
		get maxAttendance() {
			return setlistsState.maxAttendance;
		},
		get options() {
			return setlistsState.options;
		},
		get isOptionsLoading() {
			return setlistsState.isOptionsLoading;
		},

		load: async (filter?: {
			year: number;
			startMonth: number;
			endMonth: number;
			isAllData: boolean;
		}) => {
			const filterKey = filter ? JSON.stringify(filter) : 'none';

			// Return cached data if filter hasn't changed
			if (setlistsState.data && setlistsState.lastFilterKey === filterKey) {
				return;
			}

			// Deduplicate concurrent requests
			return setlistsDedup.execute(`setlists-${filterKey}`, async () => {
				setlistsState.error = null;
				setlistsState.isSetlistsLoading = true;

				try {
					const response = await setlistsApi.getAll(filter);
					setlistsState.data = response.setlists;
					setlistsState.maxAttendance = response.maxAttendance || 1;
					setlistsState.lastFilterKey = filterKey;
					setlistsState.error = null;
				} catch (e) {
					logger.error('Failed to load setlists', e, { context: 'SetlistsStore' });
					setlistsState.error = 'Failed to load setlists';
					throw e;
				} finally {
					setlistsState.isSetlistsLoading = false;
				}
			});
		},

		loadDetail: async (
			id: string,
			filter?: {
				year: number;
				startMonth: number;
				endMonth: number;
				isAllData: boolean;
			}
		) => {
			const filterKey = filter ? JSON.stringify(filter) : 'none';
			const cacheKey = `${id}-${filterKey}`;

			if (setlistsState.detailCache[cacheKey]) {
				setlistsState.detailError = null;
				return setlistsState.detailCache[cacheKey];
			}

			// Deduplicate concurrent requests for the same detail id and filter
			return setlistsDedup.execute(`detail:${cacheKey}`, async () => {
				setlistsState.detailError = null;
				setlistsState.isSetlistDetailLoading = true;

				try {
					const detail = await setlistsApi.getDetail(id, filter);
					setlistsState.detailCache[cacheKey] = detail;
					setlistsState.detailError = null;
					return detail;
				} catch (e) {
					logger.error('Failed to load details', e, { context: 'SetlistsStore' });
					setlistsState.detailError = 'Failed to load detail';
					throw e;
				} finally {
					setlistsState.isSetlistDetailLoading = false;
				}
			});
		},

		loadOptions: async () => {
			if (setlistsState.options) {
				return setlistsState.options;
			}

			return setlistsDedup.execute('options', async () => {
				setlistsState.error = null;
				setlistsState.isOptionsLoading = true;

				try {
					const options = await setlistsApi.getOptions();
					setlistsState.options = options;
					setlistsState.error = null;
					return options;
				} catch (e) {
					logger.error('Failed to load setlist options', e, { context: 'SetlistsStore' });
					setlistsState.error = 'Failed to load options';
					throw e;
				} finally {
					setlistsState.isOptionsLoading = false;
				}
			});
		},

		reset: () => {
			Object.assign(setlistsState, initialSetlistsState);
			setlistsDedup.clear();
		},

		/**
		 * Legacy subscribe method for backward compatibility
		 */
		subscribe: (
			fn: (val: {
				data: Setlist[] | null;
				error: string | null;
				detailCache: Record<string, SetlistDetailResponse>;
				detailError: string | null;
			}) => void
		) => {
			fn({
				data: setlistsState.data,
				error: setlistsState.error,
				detailCache: setlistsState.detailCache,
				detailError: setlistsState.detailError
			});
			$effect.root(() => {
				$effect(() => {
					fn({
						data: setlistsState.data,
						error: setlistsState.error,
						detailCache: setlistsState.detailCache,
						detailError: setlistsState.detailError
					});
				});
			});
			return () => {};
		}
	};
}

export const setlistsStore = createSetlistsStore();

// For backward compatibility with theater statistics
export const maxAttendanceStore = {
	get value() {
		return setlistsState.maxAttendance;
	},
	set: (val: number) => {
		setlistsState.maxAttendance = val;
	},
	subscribe: (fn: (val: number) => void) => {
		fn(setlistsState.maxAttendance);
		$effect.root(() => {
			$effect(() => fn(setlistsState.maxAttendance));
		});
		return () => {};
	}
};

// --- Members Store ---
interface MembersState {
	list: Member[];
	birthdays: BirthdayResponse[];
	pagination: { page: number; hasMore: boolean };
	cache: Record<string, { members: Member[]; pagination: { page: number; hasMore: boolean } }>;
	generationsCache: string[] | null;
	currentFilter: { generation?: string; search?: string };
	error: string | null;
	isMembersLoading: boolean;
	isBirthdaysLoading: boolean;
}

const initialMembersState: MembersState = {
	list: [],
	birthdays: [],
	pagination: { page: 0, hasMore: true },
	cache: {},
	generationsCache: null,
	currentFilter: {},
	error: null,
	isMembersLoading: false,
	isBirthdaysLoading: false
};

const membersState = $state<MembersState>(initialMembersState);
const membersDedup = createRequestDedup();

function createMembersStore() {
	return {
		get list() {
			return membersState.list;
		},
		get birthdays() {
			return membersState.birthdays;
		},
		get pagination() {
			return membersState.pagination;
		},
		get currentFilter() {
			return membersState.currentFilter;
		},
		get error() {
			return membersState.error;
		},
		get isLoading() {
			return membersState.isMembersLoading;
		},
		get isBirthdaysLoading() {
			return membersState.isBirthdaysLoading;
		},

		loadBirthdays: async () => {
			if (membersState.birthdays.length > 0) return;

			// Deduplicate concurrent requests
			return membersDedup.execute('birthdays', async () => {
				membersState.isBirthdaysLoading = true;
				try {
					const results = await membersApi.getBirthdays();
					membersState.birthdays = results;
				} catch (e) {
					logger.error('Failed to load birthdays', e, { context: 'MembersStore' });
				} finally {
					membersState.isBirthdaysLoading = false;
				}
			});
		},

		load: async (
			params: { page?: number; limit?: number; generation?: string; search?: string } = {},
			reset = false
		) => {
			const cacheKey = JSON.stringify({ generation: params.generation, search: params.search });

			if (reset && membersState.cache[cacheKey]) {
				const cached = membersState.cache[cacheKey];
				membersState.list = cached.members;
				membersState.pagination = cached.pagination;
				membersState.currentFilter = { generation: params.generation, search: params.search };
				membersState.error = null;
				return;
			}

			if (!reset && !membersState.pagination.hasMore) return;

			// Deduplicate concurrent requests with the same params
			const dedupKey = JSON.stringify({ params, reset });
			return membersDedup.execute(dedupKey, async () => {
				membersState.error = null;
				membersState.isMembersLoading = true;

				try {
					const pageToLoad = reset ? 1 : membersState.pagination.page + 1;
					const res = await membersApi.getAll({
						...params,
						page: pageToLoad,
						limit: params.limit || 100
					});

					const newItems = reset
						? []
						: res.data.filter((item: Member) => !membersState.list.some((m) => m.id === item.id));
					const newList = reset ? res.data : [...membersState.list, ...newItems];
					const newPagination = {
						page: pageToLoad,
						hasMore: !!res.meta.next_page
					};

					membersState.list = newList;
					membersState.pagination = newPagination;
					membersState.currentFilter = { generation: params.generation, search: params.search };
					membersState.cache[cacheKey] = { members: newList, pagination: newPagination };
				} catch (e) {
					logger.error('Failed to load members', e, { context: 'MembersStore' });
					membersState.error = 'Failed to load members';
					throw e;
				} finally {
					membersState.isMembersLoading = false;
				}
			});
		},

		getGenerations: async () => {
			if (membersState.generationsCache) return membersState.generationsCache;
			return membersDedup.execute('generations', async () => {
				const generations = await membersApi.getGenerations();
				membersState.generationsCache = generations;
				return generations;
			});
		},

		reset: () => {
			Object.assign(membersState, initialMembersState);
			membersDedup.clear();
		},

		/**
		 * Legacy subscribe method for backward compatibility
		 */
		subscribe: (fn: (val: MembersState) => void) => {
			fn(membersState);
			$effect.root(() => {
				$effect(() => {
					fn(membersState);
				});
			});
			return () => {};
		}
	};
}

export const membersStore = createMembersStore();

// Derived Compatibility Aliases
export const isMembersLoading = {
	get value() {
		return membersState.isMembersLoading;
	},
	subscribe: (fn: (val: boolean) => void) => {
		fn(membersState.isMembersLoading);
		$effect.root(() => {
			$effect(() => fn(membersState.isMembersLoading));
		});
		return () => {};
	}
};

export const isBirthdaysLoading = {
	get value() {
		return membersState.isBirthdaysLoading;
	},
	subscribe: (fn: (val: boolean) => void) => {
		fn(membersState.isBirthdaysLoading);
		$effect.root(() => {
			$effect(() => fn(membersState.isBirthdaysLoading));
		});
		return () => {};
	}
};

export const membersPagination = {
	get value() {
		return membersState.pagination;
	},
	subscribe: (cb: (val: { page: number; hasMore: boolean }) => void) => {
		cb(membersState.pagination);
		$effect.root(() => {
			$effect(() => cb(membersState.pagination));
		});
		return () => {};
	}
};

export const isSetlistsLoading = {
	get value() {
		return setlistsState.isSetlistsLoading;
	},
	subscribe: (fn: (val: boolean) => void) => {
		fn(setlistsState.isSetlistsLoading);
		$effect.root(() => {
			$effect(() => fn(setlistsState.isSetlistsLoading));
		});
		return () => {};
	}
};

export const isSetlistDetailLoading = {
	get value() {
		return setlistsState.isSetlistDetailLoading;
	},
	subscribe: (fn: (val: boolean) => void) => {
		fn(setlistsState.isSetlistDetailLoading);
		$effect.root(() => {
			$effect(() => fn(setlistsState.isSetlistDetailLoading));
		});
		return () => {};
	}
};

export function invalidateTheater() {
	setlistsStore.reset();
	membersStore.reset();
}

export function getTicketSlideIndex() {
	ensureTicketSlideTimer();
	return globalTicketSlideIndex;
}
