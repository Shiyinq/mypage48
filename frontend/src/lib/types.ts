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
	notes?: string; // User's personal notes/diary for the show
	two_shot?: {
		imageUrl?: string;
		member_name: string;
		type: 'Roulette' | 'Birthday';
		price: number;
	} | null;
}

export interface PaginationMeta {
	current_page: number;
	last_page: number;
	total_data: number;
	per_page: number;
	next_page: number | null;
}

export interface PaginationState {
	page: number;
	hasMore: boolean;
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

// Memories types
export type MemoryFilterType = 'ALL' | 'TICKET' | '2SHOT';

export interface MemoryItem {
	uniqueId: string;
	type: 'TICKET' | '2SHOT';
	imageUrl: string;
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

export type ViewState =
	| 'DASHBOARD'
	| 'UPLOAD'
	| 'HISTORY'
	| 'SHOWS'
	| 'ACHIEVEMENTS'
	| 'PROFILE'
	| 'MEMORIES'
	| 'TOP2SHOT';

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

// Auth Types
export interface UserOshi {
	name: string;
	nickname: string;
	generation: string;
	profilePicture: string;
	catchphrase: string;
	socials?: {
		twitter: string | null;
		instagram: string | null;
		tiktok: string | null;
		threads: string | null;
		showroom: string | null;
		idn_app: string | null;
	} | null;
}

export interface User {
	userId?: string;
	email: string;
	username: string;
	name?: string;
	memberId?: string;
	ofcStatus?: string;
	profilePicture?: string | null;
	oshi?: UserOshi | null;
	isPublic?: boolean;
	publicYear?: number | null;
}

export interface AuthResponse {
	access_token: string;
	token_type: string;
	user: User;
}

export interface LoginRequest {
	username: string; // OAuth2PasswordRequestForm usually uses username for email
	password: string;
}

export interface RegisterRequest {
	memberId: string;
	username: string;
	fullName: string;
	email: string;
	ofcStatus: string;
	password: string;
	confirmPassword: string;
}

export interface EmailVerificationRequest {
	email: string;
}

export interface VerifyEmailRequest {
	token: string;
}

export interface PasswordResetRequest {
	email: string;
}

export interface PasswordResetConfirmRequest {
	token: string;
	new_password: string;
	confirm_password: string;
}

export interface GenericResponse {
	message: string;
}

export interface ApiError {
	detail: string | Record<string, unknown>;
}

export interface APIKeysResponse {
	detail?: string;
	apiKey: string;
}

// Dashboard Types
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
}

export interface TopMemberResponse {
	name: string;
	count: number;
	image?: string | null;
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

// Profile Full Response Types
export interface RankInfo {
	current: string;
	xp: number;
	nextLevelXp: number;
	nextRankTitle: string;
}

export interface ProfileStats {
	totalShows: number;
	totalAchievements: number;
}

export interface ProfileRecentActivity {
	ticketId: string;
	title: string;
	date: string;
	section: string;
	number: string;
	hasTwoShot: boolean;
	twoShotMember?: string;
}

export interface OshiTwoShotCounts {
	roulette: number;
	birthday: number;
}

export interface ProfileFullResponse {
	profile: User;
	oshi: UserOshi | null;
	rank: RankInfo;
	stats: ProfileStats;
	oshiTwoShots: OshiTwoShotCounts;
	recentActivity: ProfileRecentActivity[];
}

/**
 * Extended User type with profile stats for the profile page.
 * These optional fields are populated from ProfileFullResponse when fetching profile.
 */
export interface UserWithProfileStats extends User {
	profileRank?: RankInfo;
	profileStats?: ProfileStats;
	profileOshiTwoShots?: OshiTwoShotCounts;
	profileRecentActivity?: ProfileRecentActivity[];
}

/**
 * Single achievement with unlock status and progress.
 */
export interface AchievementItem {
	id: string;
	title: string;
	description: string;
	icon: string;
	color: string;
	isUnlocked: boolean;
	progress: string | null;
}

/**
 * Response from achievements API.
 */
export interface AchievementsResponse {
	achievements: AchievementItem[];
	unlockedCount: number;
	totalCount: number;
}
