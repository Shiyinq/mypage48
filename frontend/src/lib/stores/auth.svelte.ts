import { auth as authApi } from '$lib/apis/auth';
import type {
	LoginRequest,
	RegisterRequest,
	PasswordResetRequest,
	PasswordResetConfirmRequest,
	VerifyEmailRequest
} from '$lib/types';
import { accessToken } from '$lib/stores/accessToken.svelte';
import { isAuthenticated } from '$lib/stores/authStatus.svelte';

/**
 * Auth actions service - migrated to Svelte 5 Shared Rune State.
 * Provides methods for login, logout, registration and password management.
 */

let isLoggingOut = $state(false);

function createAuthStore() {
	return {
		get isLoggingOut() {
			return isLoggingOut;
		},
		/**
		 * Handle login and set initial auth status
		 */
		login: async (credentials: LoginRequest) => {
			const response = await authApi.login(credentials);
			if (response.access_token) {
				accessToken.set(response.access_token);
				isAuthenticated.set(true);
			}
			return response;
		},

		register: async (data: RegisterRequest) => {
			const response = await authApi.register(data);
			return response;
		},

		/**
		 * Handle logout and clear auth status
		 */
		logout: async () => {
			if (isLoggingOut) return;
			isLoggingOut = true;
			try {
				const response = await authApi.logout();
				return response;
			} finally {
				accessToken.set('');
				isAuthenticated.set(false);
				isLoggingOut = false;
			}
		},

		forgotPassword: async (data: PasswordResetRequest) => {
			return await authApi.forgotPassword(data);
		},

		resetPassword: async (data: PasswordResetConfirmRequest) => {
			return await authApi.resetPassword(data);
		},

		verifyEmail: async (data: VerifyEmailRequest) => {
			return await authApi.verifyEmail(data);
		},

		// Social login URLs
		get googleLoginUrl() {
			return authApi.googleLoginUrl;
		},
		get githubLoginUrl() {
			return authApi.githubLoginUrl;
		}
	};
}

export const authStore = createAuthStore();
export { accessToken } from '$lib/stores/accessToken.svelte';
