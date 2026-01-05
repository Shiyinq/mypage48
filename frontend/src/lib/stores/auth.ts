import { writable } from 'svelte/store';
import { auth as authApi } from '$lib/apis/auth';
import type {
    LoginRequest,
    RegisterRequest,
    PasswordResetRequest,
    PasswordResetConfirmRequest,
    VerifyEmailRequest
} from '$lib/types';

// Access token store (used by API client)
export const accessToken = writable<string | null>(null);

// Auth Store with actions
function createAuthStore() {
    return {
        login: async (credentials: LoginRequest) => {
            const response = await authApi.login(credentials);
            return response;
        },

        register: async (data: RegisterRequest) => {
            const response = await authApi.register(data);
            return response;
        },

        logout: async () => {
            const response = await authApi.logout();
            accessToken.set(null);
            return response;
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
        googleLoginUrl: authApi.googleLoginUrl,
        githubLoginUrl: authApi.githubLoginUrl
    };
}

export const authStore = createAuthStore();
