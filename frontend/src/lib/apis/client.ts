import { get } from 'svelte/store';
import { accessToken } from '$lib/stores/accessToken';
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
	options: Omit<RequestInit, 'body'> & { body?: BodyInit | Record<string, unknown> | null } = {}
): Promise<T> {
	// 1. Get current token
	let token = get(accessToken);

	// 2. Check expiration and refresh if needed
	const publicEndpoints = [
		'/auth/signin',
		'/users/signup',
		'/auth/forgot-password',
		'/auth/reset-password',
		'/auth/verify-email',
		'/auth/send-verification'
	];

	const isPublic = publicEndpoints.some((p) => endpoint.includes(p));

	if (!isPublic) {
		// If no token OR token is expired, try to refresh via httpOnly cookie
		if (isTokenExpired(token)) {
			// Try to refresh
			const newToken = await refreshAccessToken();
			if (newToken) {
				token = newToken;
			} else {
				token = '';
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

	let data: unknown;
	const contentType = response.headers.get('content-type');
	if (contentType && contentType.includes('application/json')) {
		data = await response.json();
	} else {
		data = await response.text();
	}

	if (!response.ok) {
		throw data as ApiError;
	}

	return data as T;
}
