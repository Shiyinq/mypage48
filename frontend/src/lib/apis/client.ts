import { accessToken } from '$lib/stores/accessToken.svelte';
import { isAuthenticated } from '$lib/stores/authStatus.svelte';
import { showToast } from '$lib/stores';
import { t } from '$lib/i18n';
import { isTokenExpired, getCSRFToken } from '$lib/utils/auth';
import type { ApiError, AuthResponse } from '$lib/types';

import {
	PUBLIC_CLIENT_SIDE_API_BASE_URL,
	PUBLIC_SERVER_SIDE_API_BASE_URL
} from '$env/static/public';
import { browser } from '$app/environment';

export const API_BASE = browser ? PUBLIC_CLIENT_SIDE_API_BASE_URL : PUBLIC_SERVER_SIDE_API_BASE_URL;

// Lock to prevent multiple concurrent refresh token calls
let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
	// If a refresh is already in progress, wait for it
	if (refreshPromise) {
		return refreshPromise;
	}

	// Start the refresh and store the promise
	refreshPromise = doRefreshAccessToken();

	try {
		return await refreshPromise;
	} finally {
		// Clear the lock after completion
		refreshPromise = null;
	}
}

async function doRefreshAccessToken(): Promise<string | null> {
	try {
		// Raw fetch to avoid infinite loops
		const csrfToken = getCSRFToken();
		const response = await fetch(`${API_BASE}/auth/refresh`, {
			method: 'POST',
			headers: {
				'X-CSRF-Token': csrfToken
			},
			credentials: 'include'
		});

		if (response.ok) {
			const data: AuthResponse = await response.json();
			accessToken.set(data.access_token);
			return data.access_token;
		}
		return null;
	} catch {
		return null;
	}
}

export async function client<T>(
	endpoint: string,
	options: Omit<RequestInit, 'body'> & {
		body?: BodyInit | Record<string, unknown> | null;
		responseType?: 'json' | 'text' | 'blob';
	} = {}
): Promise<T> {
	// 1. Get current token
	let token: string = accessToken.value;

	// 2. Check expiration and refresh if needed
	const publicEndpoints = [
		'/auth/signin',
		'/users/signup',
		'/auth/forgot-password',
		'/auth/reset-password',
		'/auth/verify-email',
		'/auth/send-verification',
		'/jkt48/live',
		'/theater/news',
		'/theater/setlists',
		'/members',
		'/events',
		'/health',
		'/history/lives?page=',
		'/history/lives/stats',
		'/history/lives/members',
		'/history/lives/pc'
	];

	const isPublic = publicEndpoints.some((p) => endpoint.startsWith(p));
	const hasAuthHint = browser ? localStorage.getItem('mypage48_auth') === 'true' : false;

	// Only refresh if:
	// 1. Token is expired/missing
	// 2. AND (it's a private endpoint OR we have a session hint)
	if (isTokenExpired(token) && (!isPublic || hasAuthHint)) {
		const newToken = await refreshAccessToken();
		if (newToken) {
			token = newToken;
		} else {
			if (hasAuthHint) {
				showToast(t('auth.login.sessionInvalid'), 'error');
			}
			isAuthenticated.set(false);
			if (!isPublic) {
				token = '';
				// Silence the current request by returning a promise that never resolves.
				// This avoids triggering generic error toasts in the UI before the
				// authentication store triggers a logout/redirect.
				return new Promise(() => {});
			}
		}
	}

	// 3. Prepare headers
	const csrfToken = getCSRFToken();
	const defaultHeaders: Record<string, string> = {
		'Content-Type': 'application/json',
		'X-CSRF-Token': csrfToken
	};

	if (token) {
		defaultHeaders['Authorization'] = `Bearer ${token}`;
	}

	const config = {
		...options,
		headers: {
			...defaultHeaders,
			...options.headers
		},
		credentials: 'include' as RequestCredentials
	};

	// 4. Execute fetch
	if (
		config.body &&
		typeof config.body !== 'string' &&
		!(config.body instanceof FormData) &&
		!(config.body instanceof URLSearchParams)
	) {
		config.body = JSON.stringify(config.body);
	}

	const response = await fetch(`${API_BASE}${endpoint}`, config as RequestInit);

	// 5. Handle response
	if (response.status === 204) {
		return undefined as T;
	}

	if (!response.ok) {
		let errorData: unknown;
		// Try parsing JSON error even if we expect blob success
		const contentType = response.headers.get('content-type');
		if (contentType && contentType.includes('application/json')) {
			errorData = await response.json();
		} else {
			errorData = await response.text();
		}

		const error =
			typeof errorData === 'object' && errorData !== null
				? { ...errorData, status: response.status }
				: { detail: errorData, status: response.status };

		throw error as ApiError;
	}

	let data: unknown;

	if (options.responseType === 'blob') {
		data = await response.blob();
	} else if (options.responseType === 'text') {
		data = await response.text();
	} else {
		// Default JSON auto-detection
		const contentType = response.headers.get('content-type');
		if (contentType && contentType.includes('application/json')) {
			data = await response.json();
		} else {
			data = await response.text();
		}
	}

	return data as T;
}
