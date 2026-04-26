/**
 * Memories and top 2-shot related types.
 */

import type { PaginationMeta } from './common';

export type MemoryFilterType = 'ALL' | 'TICKET' | '2SHOT';

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
}

export interface TopTwoShotResponse {
	ranking: TopTwoShotMember[];
	totalTwoShotSpend: number;
	totalTwoShotCount: number;
}
