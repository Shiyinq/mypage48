import { client, API_BASE } from './client';
import type {
	LoginRequest,
	RegisterRequest,
	AuthResponse,
	User,
	ApiError,
	EmailVerificationRequest,
	VerifyEmailRequest,
	PasswordResetRequest,
	PasswordResetConfirmRequest,
	GenericResponse
} from '$lib/types';

export const auth = {
	login: async (credentials: LoginRequest): Promise<AuthResponse> => {
		const formData = new URLSearchParams();
		formData.append('username', credentials.username);
		formData.append('password', credentials.password);

		// Use client to benefit from global config, but override content-type
		// Actually, login is special, it doesn't need Bearer token.
		// But we DO want to capture the result to update the store.

		// We'll stick to raw fetch for login because 'client' automatically adds JSON content-type
		// unless overridden, and tries to add Bearer token which we don't have yet.
		// AND 'client' tries to refresh token if missing, which is not needed for login.

		// However, we MUST set the store upon success.

		const response = await fetch(`${API_BASE}/auth/signin`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/x-www-form-urlencoded'
			},
			credentials: 'include',
			body: formData
		});

		const data = await response.json();
		if (!response.ok) {
			throw data as ApiError;
		}

		// Import store dynamically or at top level to update it
		const { accessToken } = await import('$lib/store/auth');
		accessToken.set(data.access_token);

		return data as AuthResponse;
	},

	register: async (data: RegisterRequest) => {
		return client<any>('/users/signup', { method: 'POST', body: data as any });
	},

	logout: async () => {
		return client<GenericResponse>('/auth/logout', { method: 'POST' });
	},

	refresh: async (): Promise<AuthResponse> => {
		return client<AuthResponse>('/auth/refresh', { method: 'POST' });
	},

	getProfile: async () => {
		return client<User>('/users/profile');
	},

	sendVerificationEmail: async (data: EmailVerificationRequest) => {
		return client<GenericResponse>('/auth/send-verification', {
			method: 'POST',
			body: data as any
		});
	},

	verifyEmail: async (data: VerifyEmailRequest) => {
		return client<GenericResponse>('/auth/verify-email', { method: 'POST', body: data as any });
	},

	forgotPassword: async (data: PasswordResetRequest) => {
		return client<GenericResponse>('/auth/forgot-password', { method: 'POST', body: data as any });
	},

	resetPassword: async (data: PasswordResetConfirmRequest) => {
		return client<GenericResponse>('/auth/reset-password', { method: 'POST', body: data as any });
	},

	// Social Login URLs
	googleLoginUrl: `${API_BASE}/auth/google/signin`,
	githubLoginUrl: `${API_BASE}/auth/github/signin`
};
