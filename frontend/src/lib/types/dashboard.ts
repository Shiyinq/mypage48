/**
 * Dashboard statistics related types.
 */

export interface DayStat {
	name: string;
	count: number;
}

export interface DayStatsResponse {
	stats: DayStat[];
	max_count: number;
}

export interface RowStatsResponse {
	counts: Record<string, number>;
	max_count: number;
	unique_visited: number;
}

export interface MonthlyStat {
	name: string;
	count: number;
	spent: number;
	is_active: boolean;
}

export interface MonthlyStatsResponse {
	stats: MonthlyStat[];
	max_count: number;
}

export interface TopShowResponse {
	title: string;
	count: number;
	image: string | null;
	image_medium?: string | null;
	image_small?: string | null;
}

export interface TopMemberResponse {
	name: string;
	count: number;
	image?: string | null;
	image_medium?: string | null;
	image_small?: string | null;
}

export interface TwoShotStatsResponse {
	total_spend: number;
	total_count: number;
	unique_count: number;
	top_2_shot: TopMemberResponse | null;
}

export interface ExtremeItem {
	ticket_id: string;
	image: string | null;
	image_medium?: string | null;
	image_small?: string | null;
	title: string;
	date: string;
	time: string;
	detail?: string | null;
}

export interface ExtremesResponse {
	first: ExtremeItem | null;
	last: ExtremeItem | null;
}

export interface TheaterStatsGroup {
	total_visits: number;
	total_spent: number;
	most_frequent_row: string;
	most_frequent_row_count: number;
	top_show: TopShowResponse;
	extremes: ExtremesResponse;
}

export interface TwoShotStatsGroup {
	total_count: number;
	total_spend: number;
	unique_count: number;
	top_2_shot: TopMemberResponse | null;
	extremes: ExtremesResponse;
}

export interface SeatMapStatsGroup {
	row_stats: RowStatsResponse;
	seat_stats: Record<string, number>;
}

export interface PeriodStatsGroup {
	monthly_stats: MonthlyStatsResponse;
	day_stats: DayStatsResponse;
}

export interface DashboardStats {
	available_years: number[];
	theater: TheaterStatsGroup;
	two_shot: TwoShotStatsGroup;
	seat_map: SeatMapStatsGroup;
	period: PeriodStatsGroup;
}
