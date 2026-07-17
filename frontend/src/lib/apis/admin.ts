import { client } from './client';

export interface DataUsersStats {
	total_users: number;
	verified_users: number;
	unverified_users: number;
	total_admins: number;
	total_feedback: number;
	active_users_last_days: number;
	public_profiles: number;
	users_joined_today: number;
}

export interface DataMyPageStats {
	total_tickets: number;
	total_2shot: number;
	total_journal: number;
	total_favorites: number;
	total_sorter: number;
	total_money_spent_idr: number;
}

export interface DataTheaterStats {
	total_members_jkt: number;
	active_members_count: number;
	graduated_members_count: number;
	total_setlists: number;
	active_setlists_count: number;
	inactive_setlists_count: number;
	total_events: number;
	total_show_setlist: number;
	total_upcoming_events_and_shows: number;
	total_upcoming_events: number;
	total_upcoming_shows: number;
	upcoming_birthdays_count: number;
	total_news: number;
	total_live_member: number;
	showroom_live_count: number;
	idn_live_count: number;
	total_replay_live: number;
	showroom_replay_count: number;
	idn_replay_count: number;
}

export interface IDNLivePlusConfig {
	auth_token: string | null;
	access_token: string | null;
	session_id: string | null;
	api_key: string | null;
	aes_key: string | null;
	refresh_token: string | null;
	cognito_client_id: string | null;
	updated_at: string | null;
	enabled: boolean;
}

export interface IDNLivePlusConfigResponse {
	data: IDNLivePlusConfig;
	detail: string;
}
export const adminApi = {
	getUsersStats: async (activeDays: number = 7) => {
		return client<DataUsersStats>(`/admin/dashboard/users?active_days=${activeDays}`);
	},

	getMyPageStats: async () => {
		return client<DataMyPageStats>('/admin/dashboard/mypage');
	},

	getTheaterStats: async () => {
		return client<DataTheaterStats>('/admin/dashboard/theater');
	},

	getIdnLivePlusConfig: async () => {
		return client<IDNLivePlusConfigResponse>('/admin/settings/idnliveplus');
	},

	updateIdnLivePlusConfig: async (config: IDNLivePlusConfig) => {
		return client<IDNLivePlusConfigResponse>('/admin/settings/idnliveplus', {
			method: 'PUT',
			body: JSON.stringify(config)
		});
	}
};
