/**
 * Event-related types.
 */
import type { PaginationMeta } from './common';

export interface EventTeam {
	id: string;
	img: string;
}

export interface Event {
	id: string;
	title: string;
	date: string;
	url: string;
	label: string;
	imageUrl?: string;
	imageUrl_medium?: string;
	imageUrl_small?: string;
	blurHash?: string;
	totalMembers: number;
	seitansaiMembers?: string[];
	graduationMembers?: string[];
	setlistId?: string;
	team?: EventTeam;
	type?: string;
}

export interface CalendarEvent {
	id?: string;
	title: string;
	date: string;
	url: string;
	setlistId?: string;
	seitansaiMembers?: string[];
	graduationMembers?: string[];
	isBirthday?: boolean;
	label?: string;
	type?: string;
}

export interface EventPaginationResponse {
	data: Event[];
	meta: PaginationMeta;
}

export interface EventMember {
	id: string;
	name: string;
	img?: string;
	img_medium?: string;
	img_small?: string;
	blurHash?: string;
	member_type?: string;
	nickname?: string;
}

export interface EventDetail extends Event {
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	raw_data?: any;
	members?: EventMember[];
}
