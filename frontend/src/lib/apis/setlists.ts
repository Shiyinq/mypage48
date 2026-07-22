import { client } from './client';

export interface WatchedStats {
	count: number;
	percentage: number;
	isMostWatched: boolean;
}

export interface Setlist {
	setlistId: string;
	imageUrl: string;
	imageUrl_medium?: string;
	imageUrl_small?: string;
	blurHash?: string;
	title: string;
	titleJapanese?: string;
	description: string;
	type: 'setlist' | 'event';
	active: boolean;
	songs?: string[];
	watched: WatchedStats;
}

export interface SetlistOption {
	setlistId: string;
	title: string;
	type: string;
	active: boolean;
	imageUrl: string;
	imageUrl_medium?: string;
	imageUrl_small?: string;
	blurHash?: string;
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

export interface TwoShotHistoryItem {
	name: string;
	date: string;
	imageUrl?: string;
	imageUrl_medium?: string;
	imageUrl_small?: string;
	blurHash?: string;
}

export interface SetlistDetailStats {
	totalAttendance: number;
	totalSpent: number;
	avgPrice: number;
	topRow?: string;
	topRowCount: number;
	firstDate?: string;
	lastDate?: string;
	firstSeat?: string;
	lastSeat?: string;
	total2Shot: number;
}

export interface SetlistDetailResponse {
	setlistId: string;
	imageUrl: string;
	imageUrl_medium?: string;
	imageUrl_small?: string;
	blurHash?: string;
	title: string;
	titleJapanese?: string;
	description: string;
	type: 'setlist' | 'event';
	active: boolean;
	songs?: string[];
	watched: WatchedStats;
	stats: SetlistDetailStats;
	tickets: TicketItem[];
	twoShots: TwoShotHistoryItem[];
}

export const setlistsApi = {
	getAll: async (
		params: {
			skip?: number;
			limit?: number;
			type?: string;
			active?: boolean;
			search?: string;
			year?: number;
			startMonth?: number;
			endMonth?: number;
			isAllData?: boolean;
		} = {}
	) => {
		const query = new URLSearchParams();
		if (params.skip) query.append('skip', params.skip.toString());
		if (params.limit) query.append('limit', params.limit.toString());
		if (params.type) query.append('type', params.type);
		if (params.active !== undefined) query.append('active', params.active.toString());
		if (params.search) query.append('search', params.search);

		if (params.year !== undefined) query.append('year', params.year.toString());
		if (params.startMonth !== undefined) query.append('startMonth', params.startMonth.toString());
		if (params.endMonth !== undefined) query.append('endMonth', params.endMonth.toString());
		if (params.isAllData !== undefined) query.append('isAllData', params.isAllData.toString());

		return client<SetlistListResponse>(`/theater/setlists?${query.toString()}`);
	},

	getOptions: async () => {
		return client<SetlistOption[]>('/theater/setlists/options');
	},

	getById: async (setlistId: string) => {
		return client<Setlist>(`/theater/setlists/id/${encodeURIComponent(setlistId)}`);
	},

	getDetail: async (
		setlistId: string,
		params: {
			year?: number;
			startMonth?: number;
			endMonth?: number;
			isAllData?: boolean;
		} = {}
	) => {
		const query = new URLSearchParams();
		if (params.year !== undefined) query.append('year', params.year.toString());
		if (params.startMonth !== undefined) query.append('startMonth', params.startMonth.toString());
		if (params.endMonth !== undefined) query.append('endMonth', params.endMonth.toString());
		if (params.isAllData !== undefined) query.append('isAllData', params.isAllData.toString());

		const queryString = query.toString() ? `?${query.toString()}` : '';
		return client<SetlistDetailResponse>(
			`/theater/setlists/detail/${encodeURIComponent(setlistId)}${queryString}`
		);
	},

	getByTitle: async (title: string) => {
		return client<Setlist>(`/theater/setlists/title/${encodeURIComponent(title)}`);
	},

	// Admin-only CRUD operations
	create: async (data: Omit<Setlist, 'setlistId' | 'watched'>) => {
		return client<Setlist>('/theater/setlists', {
			method: 'POST',
			body: JSON.stringify(data)
		});
	},

	update: async (setlistId: string, data: Partial<Omit<Setlist, 'setlistId' | 'watched'>>) => {
		return client<Setlist>(`/theater/setlists/${encodeURIComponent(setlistId)}`, {
			method: 'PUT',
			body: JSON.stringify(data)
		});
	},

	delete: async (setlistId: string) => {
		return client<{ message: string }>(`/theater/setlists/${encodeURIComponent(setlistId)}`, {
			method: 'DELETE'
		});
	}
};
