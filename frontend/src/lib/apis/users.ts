import { client } from './client';

export interface UserListItem {
	userId: string;
	name: string;
	username: string;
	email: string;
	profilePicture?: string | null;
	isAdmin: boolean;
	isEmailVerified: boolean;
	isAccountLocked: boolean;
	createdAt: string;
}

export interface UserPaginationMeta {
	current_page: number;
	last_page: number;
	total_data: number;
	per_page: number;
	next_page: number | null;
}

export interface UserListResponse {
	data: UserListItem[];
	meta: UserPaginationMeta;
}

export const usersApi = {
	getAll: async (params: { page?: number; limit?: number; search?: string } = {}) => {
		const query = new URLSearchParams();
		if (params.page) query.append('page', params.page.toString());
		if (params.limit) query.append('limit', params.limit.toString());
		if (params.search) query.append('search', params.search);

		return client<UserListResponse>(`/users?${query.toString()}`);
	}
};
