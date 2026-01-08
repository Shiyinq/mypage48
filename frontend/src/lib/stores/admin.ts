import { writable, get } from 'svelte/store';
import { members as membersApi, type Member } from '$lib/apis/members';
import { setlistsApi, type Setlist } from '$lib/apis/setlists';
import { usersApi, type UserListItem } from '$lib/apis/users';
import { showToast } from './toast';

import type { AdminState } from '$lib/types';

const initialState: AdminState = {
    members: {
        data: [],
        loading: false,
        hasMore: true,
        page: 1,
        search: '',
        error: null
    },
    setlists: {
        data: [],
        loading: false,
        hasMore: true,
        skip: 0,
        limit: 20,
        search: '',
        error: null
    },
    users: {
        data: [],
        loading: false,
        hasMore: true,
        page: 1,
        search: '',
        error: null
    }
};

function createAdminStore() {
    const { subscribe, set, update } = writable<AdminState>(initialState);

    return {
        subscribe,

        // --- Members Actions ---

        async loadMembers(reset = false) {
            const state = get({ subscribe });
            const { loading, hasMore, page, search } = state.members;

            if (loading || (!hasMore && !reset)) return;

            update((s) => ({
                ...s,
                members: { ...s.members, loading: true, error: null, ...(reset ? { data: [], page: 1, hasMore: true } : {}) }
            }));

            try {
                const currentPage = reset ? 1 : page;
                const res = await membersApi.getAll({
                    page: currentPage,
                    limit: 20,
                    search: search
                });

                update((s) => {
                    // Check duplicate avoidance if necessary, but API pagination should be stable typically
                    const newData = reset ? res.data : [...s.members.data, ...res.data];
                    return {
                        ...s,
                        members: {
                            ...s.members,
                            data: newData,
                            loading: false,
                            page: currentPage + 1,
                            hasMore: res.data.length === 20 // Assuming limit is 20
                        }
                    };
                });
            } catch (e) {
                console.error('Failed to load members', e);
                showToast('Failed to load members', 'error');
                update((s) => ({
                    ...s,
                    members: { ...s.members, loading: false, error: 'Failed to load members' }
                }));
            }
        },

        setMemberSearch(query: string) {
            update((s) => ({
                ...s,
                members: { ...s.members, search: query }
            }));
            // Debounce is handled in UI usually, but we can just trigger load(reset=true) immediately
            // The UI will call this method.
            this.loadMembers(true);
        },

        async createMember(data: Omit<Member, 'id'>) {
            try {
                await membersApi.create(data);
                // Refresh list
                this.loadMembers(true);
                return true;
            } catch (e) {
                console.error(e);
                throw e;
            }
        },

        async updateMember(id: number, data: Partial<Member>) {
            try {
                await membersApi.update(id, data);
                // Optimistic update or refresh
                update((s) => ({
                    ...s,
                    members: {
                        ...s.members,
                        data: s.members.data.map((m) => (m.id === id ? { ...m, ...data } : m))
                    }
                }));
                return true;
            } catch (e) {
                console.error(e);
                throw e;
            }
        },

        async deleteMember(id: number) {
            try {
                await membersApi.delete(id);
                update((s) => ({
                    ...s,
                    members: {
                        ...s.members,
                        data: s.members.data.filter((m) => m.id !== id)
                    }
                }));
                return true;
            } catch (e) {
                console.error(e);
                throw e;
            }
        },


        // --- Setlists Actions ---

        async loadSetlists(reset = false) {
            const state = get({ subscribe });
            const { loading, hasMore, skip, limit, search } = state.setlists;

            if (loading || (!hasMore && !reset)) return;

            update((s) => ({
                ...s,
                setlists: { ...s.setlists, loading: true, error: null, ...(reset ? { data: [], skip: 0, hasMore: true } : {}) }
            }));

            try {
                const currentSkip = reset ? 0 : skip;
                const res = await setlistsApi.getAll({
                    skip: currentSkip,
                    limit: limit,
                    search: search
                });

                update((s) => {
                    const newData = reset ? res.setlists : [...s.setlists.data, ...res.setlists];
                    return {
                        ...s,
                        setlists: {
                            ...s.setlists,
                            data: newData,
                            loading: false,
                            skip: currentSkip + res.setlists.length,
                            hasMore: res.setlists.length === limit
                        }
                    };
                });
            } catch (e) {
                console.error('Failed to load setlists', e);
                showToast('Failed to load setlists', 'error');
                update((s) => ({
                    ...s,
                    setlists: { ...s.setlists, loading: false, error: 'Failed to load setlists' }
                }));
            }
        },

        setSetlistSearch(query: string) {
            update((s) => ({
                ...s,
                setlists: { ...s.setlists, search: query }
            }));
            this.loadSetlists(true);
        },

        async createSetlist(data: any) {
            try {
                await setlistsApi.create(data);
                this.loadSetlists(true);
                return true;
            } catch (e) {
                console.error(e);
                throw e;
            }
        },

        async updateSetlist(id: string, data: any) {
            try {
                await setlistsApi.update(id, data);
                // We can just refresh to be safe or optimistic update
                // Optimistic:
                update((s) => ({
                    ...s,
                    setlists: {
                        ...s.setlists,
                        data: s.setlists.data.map((item) => (item.setlistId === id ? { ...item, ...data } : item))
                    }
                }));
                return true;
            } catch (e) {
                console.error(e);
                throw e;
            }
        },

        async deleteSetlist(id: string) {
            try {
                await setlistsApi.delete(id);
                update((s) => ({
                    ...s,
                    setlists: {
                        ...s.setlists,
                        data: s.setlists.data.filter((item) => item.setlistId !== id)
                    }
                }));
                return true;
            } catch (e) {
                console.error(e);
                throw e;
            }
        },

        // --- Users Actions ---

        async loadUsers(reset = false) {
            const state = get({ subscribe });
            const { loading, hasMore, page, search } = state.users;

            if (loading || (!hasMore && !reset)) return;

            update((s) => ({
                ...s,
                users: { ...s.users, loading: true, error: null, ...(reset ? { data: [], page: 1, hasMore: true } : {}) }
            }));

            try {
                const currentPage = reset ? 1 : page;
                const res = await usersApi.getAll({
                    page: currentPage,
                    limit: 20,
                    search: search
                });

                update((s) => {
                    const newData = reset ? res.data : [...s.users.data, ...res.data];
                    return {
                        ...s,
                        users: {
                            ...s.users,
                            data: newData,
                            loading: false,
                            page: currentPage + 1,
                            hasMore: res.meta.next_page !== null
                        }
                    };
                });
            } catch (e) {
                console.error('Failed to load users', e);
                showToast('Failed to load users', 'error');
                update((s) => ({
                    ...s,
                    users: { ...s.users, loading: false, error: 'Failed to load users' }
                }));
            }
        },

        setUserSearch(query: string) {
            update((s) => ({
                ...s,
                users: { ...s.users, search: query }
            }));
            this.loadUsers(true);
        }
    };
}

export const adminStore = createAdminStore();
