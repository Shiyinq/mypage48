import { members as membersApi, type Member } from '$lib/apis/members';
import { setlistsApi, type Setlist } from '$lib/apis/setlists';
import { usersApi } from '$lib/apis/users';
import { showToast } from './toast.svelte';
import type { AdminState } from '$lib/types';

/**
 * Admin store - migrated to Svelte 5 Shared Rune State.
 * Manages administrative entities including members, setlists, and users.
 */

const initialState: AdminState = {
	members: {
		data: [],
		hasMore: true,
		page: 1,
		total: 0,
		search: '',
		error: null
	},
	setlists: {
		data: [],
		hasMore: true,
		skip: 0,
		limit: 20,
		total: 0,
		search: '',
		error: null
	},
	users: {
		data: [],
		hasMore: true,
		page: 1,
		total: 0,
		search: '',
		error: null
	}
};

const state = $state<AdminState>(initialState);

// Separate loading states for granular UI control
let isMembersLoading = $state(false);
let isSetlistsLoading = $state(false);
let isUsersLoading = $state(false);

function createAdminStore() {
	return {
		get members() {
			return state.members;
		},
		get setlists() {
			return state.setlists;
		},
		get users() {
			return state.users;
		},
		get isMembersLoading() {
			return isMembersLoading;
		},
		get isSetlistsLoading() {
			return isSetlistsLoading;
		},
		get isUsersLoading() {
			return isUsersLoading;
		},

		// --- Members Actions ---
		async loadMembers(reset = false) {
			if (isMembersLoading || (!state.members.hasMore && !reset)) return;
			if (reset) {
				state.members.data = [];
				state.members.page = 1;
				state.members.hasMore = true;
			}
			state.members.error = null;
			isMembersLoading = true;

			try {
				const res = await membersApi.getAll({
					page: state.members.page,
					limit: 20,
					search: state.members.search
				});

				state.members.data = reset ? res.data : [...state.members.data, ...res.data];
				state.members.page = state.members.page + 1;
				state.members.total = res.meta.total_data;
				state.members.hasMore = res.data.length === 20;
			} catch (e) {
				console.error('Failed to load members', e);
				showToast('Failed to load members', 'error');
				state.members.error = 'Failed to load members';
			} finally {
				isMembersLoading = false;
			}
		},

		setMemberSearch(query: string) {
			state.members.search = query;
			this.loadMembers(true);
		},

		async createMember(data: Omit<Member, 'id'>) {
			isMembersLoading = true;
			try {
				await membersApi.create(data);
				await this.loadMembers(true);
				return true;
			} catch (e) {
				console.error(e);
				throw e;
			} finally {
				isMembersLoading = false;
			}
		},

		async updateMember(id: string | number, data: Partial<Member>) {
			try {
				await membersApi.update(id, data);
				state.members.data = state.members.data.map((m) => (m.id === id ? { ...m, ...data } : m));
				return true;
			} catch (e) {
				console.error(e);
				throw e;
			}
		},

		async deleteMember(id: string | number) {
			try {
				await membersApi.delete(id);
				state.members.data = state.members.data.filter((m) => m.id !== id);
				return true;
			} catch (e) {
				console.error(e);
				throw e;
			}
		},

		// --- Setlists Actions ---
		async loadSetlists(reset = false) {
			if (isSetlistsLoading || (!state.setlists.hasMore && !reset)) return;
			if (reset) {
				state.setlists.data = [];
				state.setlists.skip = 0;
				state.setlists.hasMore = true;
			}
			state.setlists.error = null;
			isSetlistsLoading = true;

			try {
				const res = await setlistsApi.getAll({
					skip: state.setlists.skip,
					limit: state.setlists.limit,
					search: state.setlists.search
				});

				state.setlists.data = reset ? res.setlists : [...state.setlists.data, ...res.setlists];
				state.setlists.skip = state.setlists.skip + res.setlists.length;
				state.setlists.total = res.total;
				state.setlists.hasMore = res.setlists.length === state.setlists.limit;
			} catch (e) {
				console.error('Failed to load setlists', e);
				showToast('Failed to load setlists', 'error');
				state.setlists.error = 'Failed to load setlists';
			} finally {
				isSetlistsLoading = false;
			}
		},

		setSetlistSearch(query: string) {
			state.setlists.search = query;
			this.loadSetlists(true);
		},

		async createSetlist(data: Omit<Setlist, 'setlistId' | 'watched'>) {
			isSetlistsLoading = true;
			try {
				await setlistsApi.create(data);
				await this.loadSetlists(true);
				return true;
			} catch (e) {
				console.error(e);
				throw e;
			} finally {
				isSetlistsLoading = false;
			}
		},

		async updateSetlist(id: string, data: Partial<Omit<Setlist, 'setlistId' | 'watched'>>) {
			try {
				await setlistsApi.update(id, data);
				state.setlists.data = state.setlists.data.map((item) =>
					item.setlistId === id ? { ...item, ...data } : item
				);
				return true;
			} catch (e) {
				console.error(e);
				throw e;
			}
		},

		async deleteSetlist(id: string) {
			try {
				await setlistsApi.delete(id);
				state.setlists.data = state.setlists.data.filter((item) => item.setlistId !== id);
				return true;
			} catch (e) {
				console.error(e);
				throw e;
			}
		},

		// --- Users Actions ---
		async loadUsers(reset = false) {
			if (isUsersLoading || (!state.users.hasMore && !reset)) return;
			if (reset) {
				state.users.data = [];
				state.users.page = 1;
				state.users.hasMore = true;
			}
			state.users.error = null;
			isUsersLoading = true;

			try {
				const res = await usersApi.getAll({
					page: state.users.page,
					limit: 20,
					search: state.users.search
				});

				state.users.data = reset ? res.data : [...state.users.data, ...res.data];
				state.users.page = state.users.page + 1;
				state.users.total = res.meta.total_data;
				state.users.hasMore = res.meta.next_page !== null;
			} catch (e) {
				console.error('Failed to load users', e);
				showToast('Failed to load users', 'error');
				state.users.error = 'Failed to load users';
			} finally {
				isUsersLoading = false;
			}
		},

		setUserSearch(query: string) {
			state.users.search = query;
			this.loadUsers(true);
		},

		/**
		 * Legacy subscribe method for backward compatibility
		 */
		subscribe: (fn: (val: AdminState) => void) => {
			fn(state);
			$effect.root(() => {
				$effect(() => {
					fn(state);
				});
			});
			return () => {};
		}
	};
}

export const adminStore = createAdminStore();

// Compatibility Aliases
export const isAdminMembersLoading = {
	get value() {
		return isMembersLoading;
	},
	subscribe: (fn: (val: boolean) => void) => {
		fn(isMembersLoading);
		$effect.root(() => {
			$effect(() => fn(isMembersLoading));
		});
		return () => {};
	}
};

export const isAdminSetlistsLoading = {
	get value() {
		return isSetlistsLoading;
	},
	subscribe: (fn: (val: boolean) => void) => {
		fn(isSetlistsLoading);
		$effect.root(() => {
			$effect(() => fn(isSetlistsLoading));
		});
		return () => {};
	}
};

export const isAdminUsersLoading = {
	get value() {
		return isUsersLoading;
	},
	subscribe: (fn: (val: boolean) => void) => {
		fn(isUsersLoading);
		$effect.root(() => {
			$effect(() => fn(isUsersLoading));
		});
		return () => {};
	}
};
