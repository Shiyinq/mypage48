import { writable } from 'svelte/store';
import { auth as authApi } from '$lib/apis/auth';
import type {
    LoginRequest,
    RegisterRequest,
    PasswordResetRequest,
    PasswordResetConfirmRequest,
    VerifyEmailRequest
} from '$lib/types';
import { accessToken } from '$lib/stores/accessToken';

// Re-export accessToken from separate file
export { accessToken } from '$lib/stores/accessToken';

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
            accessToken.set('');
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

        // Social login URLs - use getters to avoid circular dependency
        get googleLoginUrl() {
            return authApi.googleLoginUrl;
        },
        get githubLoginUrl() {
            return authApi.githubLoginUrl;
        }
    };
}

export const authStore = createAuthStore();
