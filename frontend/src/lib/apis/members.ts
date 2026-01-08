import { client } from './client';

export interface SocialMedia {
	twitter: string | null;
	instagram: string | null;
	tiktok: string | null;
	threads: string | null;
	showroom: string | null;
	idn_app: string | null;
}

export interface Member {
	id: number;
	name: string;
	nickname: string;
	generation: string;
	jiko: string;
	active: boolean;
	href: string;
	img: string;
	birthdate: string;
	bloodType: string;
	horoscope: string;
	height: string;
	socials: SocialMedia;
}

import type { PaginationMeta } from '$lib/types';

export interface MemberListResponse {
	data: Member[];
	meta: PaginationMeta;
}

export const members = {
	getAll: async (
		params: { page?: number; limit?: number; generation?: string; search?: string } = {}
	) => {
		const query = new URLSearchParams();
		if (params.page) query.append('page', params.page.toString());
		if (params.limit) query.append('limit', params.limit.toString());
		if (params.generation) query.append('generation', params.generation);
		if (params.search) query.append('search', params.search);

		return client<MemberListResponse>(`/members?${query.toString()}`);
	},

	getGenerations: async () => {
		return client<string[]>('/members/generations');
	},

	// Admin-only CRUD operations
	create: async (data: Omit<Member, 'id'>) => {
		return client<Member>('/members', {
			method: 'POST',
			body: JSON.stringify(data)
		});
	},

	update: async (memberId: number, data: Partial<Member>) => {
		return client<Member>(`/members/${memberId}`, {
			method: 'PUT',
			body: JSON.stringify(data)
		});
	},

	delete: async (memberId: number) => {
		return client<{ message: string }>(`/members/${memberId}`, {
			method: 'DELETE'
		});
	}
};
