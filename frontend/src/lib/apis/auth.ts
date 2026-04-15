import { client, API_BASE } from './client';
import { accessToken } from '$lib/stores/accessToken.svelte';
import type {
	LoginRequest,
	RegisterRequest,
	AuthResponse,
	ApiError,
	EmailVerificationRequest,
	VerifyEmailRequest,
	PasswordResetRequest,
	PasswordResetConfirmRequest,
	GenericResponse,
	ProfileFullResponse
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

		// Update store
		accessToken.set(data.access_token);

		return data as AuthResponse;
	},

	register: async (data: RegisterRequest) => {
		return client<AuthResponse>('/users/signup', {
			method: 'POST',
			body: data as unknown as Record<string, unknown>
		});
	},

	logout: async () => {
		return client<GenericResponse>('/auth/logout', { method: 'POST' });
	},

	updateOshi: async (oshiId: number) => {
		return client<GenericResponse>('/users/oshi', {
			method: 'POST',
			body: { oshiId } as unknown as Record<string, unknown>
		});
	},

	updateProfilePicture: async (profilePicture: string) => {
		return client<GenericResponse>('/users/profile-picture', {
			method: 'POST',
			body: { profilePicture } as unknown as Record<string, unknown>
		});
	},

	refresh: async (): Promise<AuthResponse> => {
		return client<AuthResponse>('/auth/refresh', { method: 'POST' });
	},

	getProfile: async () => {
		return client<ProfileFullResponse>('/users/profile');
	},

	sendVerificationEmail: async (data: EmailVerificationRequest) => {
		return client<GenericResponse>('/auth/send-verification', {
			method: 'POST',
			body: data as unknown as Record<string, unknown>
		});
	},

	verifyEmail: async (data: VerifyEmailRequest) => {
		return client<GenericResponse>('/auth/verify-email', {
			method: 'POST',
			body: data as unknown as Record<string, unknown>
		});
	},

	forgotPassword: async (data: PasswordResetRequest) => {
		return client<GenericResponse>('/auth/forgot-password', {
			method: 'POST',
			body: data as unknown as Record<string, unknown>
		});
	},

	resetPassword: async (data: PasswordResetConfirmRequest) => {
		return client<GenericResponse>('/auth/reset-password', {
			method: 'POST',
			body: data as unknown as Record<string, unknown>
		});
	},

	// Social Login URLs - use getters to avoid accessing API_BASE during initialization
	get googleLoginUrl() {
		return `${API_BASE}/auth/google/signin`;
	},
	get githubLoginUrl() {
		return `${API_BASE}/auth/github/signin`;
	}
};
