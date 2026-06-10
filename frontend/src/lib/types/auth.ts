/**
 * Authentication and user-related types.
 */

export interface OshiShow {
	title: string;
	date: string;
	url?: string | null;
}

export interface UserOshi {
	id: string;
	name: string;
	nickname: string;
	generation: string;
	memberType?: string;
	profilePicture: string;
	profilePicture_medium?: string | null;
	profilePicture_small?: string | null;
	blurHash?: string | null;
	catchphrase: string;
	socials?: {
		twitter: string | null;
		instagram: string | null;
		tiktok: string | null;
		threads: string | null;
		showroom: string | null;
		idn_app: string | null;
	} | null;
	totalShows?: number;
	upcomingSchedule?: OshiShow[];
	pastSchedule?: OshiShow[];
}

export interface User {
	userId?: string;
	email: string;
	username: string;
	name?: string;
	bio?: string | null;
	memberId?: string;
	ofcStatus?: string;
	profilePicture?: string | null;
	profilePicture_medium?: string | null;
	profilePicture_small?: string | null;
	blurHash?: string | null;
	oshis?: UserOshi[];
	isPublic?: boolean;
	publicYear?: number | null;
	provider?: string;
	isEmailVerified?: boolean;
	isAdmin?: boolean;
	createdAt?: string;
}

export interface AuthResponse {
	access_token: string;
	token_type: string;
	//	user: User;
}

export interface LoginRequest {
	username: string; // OAuth2PasswordRequestForm usually uses username for email
	password: string;
}

export interface RegisterRequest {
	username: string;
	fullName: string;
	email: string;
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

export interface APIKeysResponse {
	detail?: string;
	apiKey: string;
}
