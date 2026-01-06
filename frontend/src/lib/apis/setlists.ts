import { client } from './client';

export interface WatchedStats {
	count: number;
	percentage: number;
	isMostWatched: boolean;
}

export interface Setlist {
	setlistId: string;
	imageUrl: string;
	title: string;
	titleJapanese?: string;
	description: string;
	type: 'setlist' | 'event';
	active: boolean;
	songs?: string[];
	watched: WatchedStats;
}

export interface SetlistListResponse {
	total: number;
	maxAttendance: number;
	setlists: Setlist[];
}

export interface SetlistSeedResponse {
	message: string;
	count: number;
}

// Detail types
export interface TicketEvent {
	title: string;
	date: string;
	time: string;
}

export interface TicketSeat {
	section: string;
	number: number;
}

export interface TicketItem {
	ticketId: string;
	event: TicketEvent;
	seat: TicketSeat;
	price: number;
	notes?: string;
}

export interface SetlistDetailStats {
	totalAttendance: number;
	totalSpent: number;
	avgPrice: number;
	topRow?: string;
	firstDate?: string;
	lastDate?: string;
}

export interface SetlistDetailResponse {
	setlistId: string;
	imageUrl: string;
	title: string;
	titleJapanese?: string;
	description: string;
	type: 'setlist' | 'event';
	active: boolean;
	songs?: string[];
	watched: WatchedStats;
	stats: SetlistDetailStats;
	tickets: TicketItem[];
}

export const setlistsApi = {
	getAll: async (
		params: { skip?: number; limit?: number; type?: string; active?: boolean } = {}
	) => {
		const query = new URLSearchParams();
		if (params.skip) query.append('skip', params.skip.toString());
		if (params.limit) query.append('limit', params.limit.toString());
		if (params.type) query.append('type', params.type);
		if (params.active !== undefined) query.append('active', params.active.toString());

		return client<SetlistListResponse>(`/theater/setlists?${query.toString()}`);
	},

	getById: async (setlistId: string) => {
		return client<Setlist>(`/theater/setlists/id/${setlistId}`);
	},

	getDetail: async (setlistId: string) => {
		return client<SetlistDetailResponse>(`/theater/setlists/detail/${setlistId}`);
	},

	getByTitle: async (title: string) => {
		return client<Setlist>(`/theater/setlists/title/${encodeURIComponent(title)}`);
	},

	seed: async () => {
		return client<SetlistSeedResponse>('/theater/setlists/seed', {
			method: 'POST'
		});
	}
};
