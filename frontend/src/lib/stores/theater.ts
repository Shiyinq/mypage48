import { writable } from 'svelte/store';
import type { Setlist } from '$lib/apis/setlists';
import type { Member } from '$lib/apis/members';

export const setlistsStore = writable<Setlist[] | null>(null);
export const maxAttendanceStore = writable<number>(1);
export const membersStore = writable<Member[]>([]);
export const membersPagination = writable({ page: 0, hasMore: true });
export const membersCacheStore = writable<
	Record<string, { members: Member[]; pagination: { page: number; hasMore: boolean } }>
>({});

export function invalidateTheater() {
	setlistsStore.set(null);
	membersStore.set([]);
	membersPagination.set({ page: 0, hasMore: true });
	membersCacheStore.set({});
}
