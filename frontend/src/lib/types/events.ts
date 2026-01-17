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
	setlistId?: string;
	team?: EventTeam;
}

export interface CalendarEvent {
	title: string;
	date: string;
	url: string;
	setlistId?: string;
	seitansaiMembers?: string[];
}

export interface EventPaginationResponse {
	data: Event[];
	meta: PaginationMeta;
}
