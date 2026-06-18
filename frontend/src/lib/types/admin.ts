import type { Member } from '$lib/apis/members';
import type { Setlist } from '$lib/apis/setlists';
import type { UserListItem } from '$lib/apis/users';
import type { DataUsersStats, DataMyPageStats, DataTheaterStats } from '$lib/apis/admin';

export interface AdminState {
	members: {
		data: Member[];
		hasMore: boolean;
		page: number;
		total: number;
		search: string;
		error: string | null;
	};
	setlists: {
		data: Setlist[];
		hasMore: boolean;
		skip: number;
		limit: number;
		total: number;
		search: string;
		error: string | null;
	};
	users: {
		data: UserListItem[];
		hasMore: boolean;
		page: number;
		total: number;
		search: string;
		error: string | null;
	};
	dashboardStats: {
		users: DataUsersStats | null;
		mypage: DataMyPageStats | null;
		theater: DataTheaterStats | null;
		error: string | null;
		isLoaded: boolean;
	};
}
