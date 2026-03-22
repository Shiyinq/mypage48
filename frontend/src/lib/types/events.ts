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
	totalMembers: number;
	seitansaiMembers?: string[];
	graduationMembers?: string[];
	setlistId?: string;
	team?: EventTeam;
	type?: string;
}

export interface CalendarEvent {
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
