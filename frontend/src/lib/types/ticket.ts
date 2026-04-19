/**
 * Ticket-related types for theater tickets.
 */

import type { PaginationMeta } from './common';

export interface Ticket {
	_id: string;
	user_id: string | null;
	ticket_id: string;
	event: {
		title: string;
		date: string; // YYYY-MM-DD
		day: string;
		time: string;
		gate_open?: string;
		venue: string;
	};
	seat: {
		section: string;
		number: string | number;
	};
	price: number;
	currency: string;
	rules: {
		refund_allowed: boolean;
		exchange_allowed: boolean;
	};
	created_at: string;
	updated_at: string;
	imageUrl?: string; // Kept for local UI display functionality
	blurHash?: string;
	notes?: string; // User's personal notes/diary for the show
	two_shot?: {
		imageUrl?: string;
		blurHash?: string;
		member_name: string;
		type: 'Roulette' | 'Birthday';
		price: number;
	} | null;
}

export interface TicketFilters {
	title?: string;
	hasTwoShot?: boolean;
	days?: string[];
	startDate?: string;
	endDate?: string;
}

export interface TicketPaginationResponse {
	data: Ticket[];
	meta: PaginationMeta;
}

export interface AnalysisResult {
	title: string;
	date: string;
	time: string;
	gate_open: string;
	day: string;
	section: string;
	number: string;
	price: number;
	ticket_id: string;
}
