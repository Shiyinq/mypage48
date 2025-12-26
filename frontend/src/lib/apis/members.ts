import { client } from './client';
import type { GenericResponse } from '$lib/types';

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

export interface MemberListResponse {
    total: number;
    members: Member[];
}

export const members = {
    getAll: async (params: { skip?: number; limit?: number; generation?: string; search?: string } = {}) => {
        const query = new URLSearchParams();
        if (params.skip) query.append('skip', params.skip.toString());
        if (params.limit) query.append('limit', params.limit.toString());
        if (params.generation) query.append('generation', params.generation);
        if (params.search) query.append('search', params.search);

        return client<MemberListResponse>(`/members/?${query.toString()}`);
    }
};
