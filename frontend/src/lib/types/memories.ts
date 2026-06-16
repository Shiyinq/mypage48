/**
 * Memories and top 2-shot related types.
 */

import type { PaginationMeta } from './common';

export type MemoryFilterType = 'ALL' | 'TICKET' | '2SHOT';

export interface MemoryFilters {
	type?: MemoryFilterType;
	title?: string;
	isFavorite?: boolean;
	startDate?: string;
	endDate?: string;
	days?: string[];
}

export interface MemoryItem {
	uniqueId: string;
	type: 'TICKET' | '2SHOT';
	imageUrl: string;
	imageUrl_medium?: string;
	imageUrl_small?: string;
	blurHash?: string;
	date: string;
	time: string;
	title: string;
	subtitle: string;
	notes?: string;
	is_favorite?: boolean;
	ticketRef?: string;
	eventTitle?: string;
	twoShotMemberName?: string;
}

export interface MemoriesPaginationResponse {
	data: MemoryItem[];
	meta: PaginationMeta;
}

export interface TopTwoShotMember {
	name: string;
	count: number;
	spend: number;
	lastDate: string;
	image?: string | null;
	image_medium?: string | null;
	image_small?: string | null;
	blurHash?: string | null;
}

export interface TopTwoShotResponse {
	available_years: number[];
	ranking: TopTwoShotMember[];
	totalTwoShotSpend: number;
	totalTwoShotCount: number;
}
