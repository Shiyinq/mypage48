export interface User {
	userId: string;
	email: string;
	username: string;
	name: string;
	profilePicture?: string;
	provider?: string;
	isEmailVerified: boolean;
	createdAt: string;
}

export interface AuthResponse {
	access_token: string;
	token_type: string;
}

export interface LoginRequest {
	username: string; // email or username
	password: string;
}

export interface RegisterRequest {
	name: string;
	username: string;
	email: string;
	password: string;
	confirmPassword: string;
}

export interface ApiError {
	detail: string | { loc: (string | number)[]; msg: string; type: string }[];
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

export interface APIKeysResponse {
	detail: string;
	apiKey: string;
}
