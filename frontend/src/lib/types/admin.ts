import type { Member } from '$lib/apis/members';
import type { Setlist } from '$lib/apis/setlists';
import type { UserListItem } from '$lib/apis/users';

export interface AdminState {
    members: {
        data: Member[];
        loading: boolean;
        hasMore: boolean;
        page: number;
        total: number;
        search: string;
        error: string | null;
    };
    setlists: {
        data: Setlist[];
        loading: boolean;
        hasMore: boolean;
        skip: number;
        limit: number;
        total: number;
        search: string;
        error: string | null;
    };
    users: {
        data: UserListItem[];
        loading: boolean;
        hasMore: boolean;
        page: number;
        total: number;
        search: string;
        error: string | null;
    };
}
