import { get } from 'svelte/store';
import { accessToken } from '$lib/store/auth';
import { isTokenExpired, getCSRFToken } from '$lib/utils/auth';
import type { ApiError, AuthResponse } from '$lib/types';

import { PUBLIC_CLIENT_SIDE_API_BASE_URL, PUBLIC_SERVER_SIDE_API_BASE_URL } from '$env/static/public';
import { browser } from '$app/environment';

export const API_BASE = browser ? PUBLIC_CLIENT_SIDE_API_BASE_URL : PUBLIC_SERVER_SIDE_API_BASE_URL;

async function refreshAccessToken(): Promise<string | null> {
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
	} catch (error) {
		return null;
	}
}

export async function client<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
	// 1. Get current token
	let token = get(accessToken);

	// 2. Check expiration and refresh if needed
	// Only check if we have a token (implying we think we are logged in)
	// or if we might need to be logged in.
	// However, for public endpoints (like login), we might have no token.
	// We skip this check if no token is present initially?
	// User logic: "if (isTokenExpired(currentToken)) { refresh... }"
	// If token is empty string, isTokenExpired returns true.
	// We should only try to refresh if we actually expect to be authenticated??
	// But maybe the user IS logged in but the memory store is empty (page reload)?
	// If page reload, store is empty. access_token is lost.
	// We MUST try to refresh on first load if we want persistence.

	// List of public endpoints that don't need auth
	const publicEndpoints = [
		'/auth/signin',
		'/users/signup',
		'/auth/forgot-password',
		'/auth/reset-password',
		'/auth/verify-email',
		'/auth/send-verification'
	];

	const isPublic = publicEndpoints.some((p) => endpoint.includes(p));

	// Only attempt refresh if:
	// 1. Token is present but expired
	// 2. OR Token is missing AND it's NOT a public endpoint (trying to restore session)
	// Actually, simple rule: If we are not accessing a public endpoint, try to ensure we have a token.
	if (!isPublic) {
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

	const config: RequestInit = {
		...options,
		headers: {
			...defaultHeaders,
			...options.headers
		},
		credentials: 'include' // Important for cookies (refresh_token, csrf_token)
	};

	// 4. Execute fetch
	// If options.body is an object, stringify it
	if (
		config.body &&
		typeof config.body !== 'string' &&
		!(config.body instanceof FormData) &&
		!(config.body instanceof URLSearchParams)
	) {
		config.body = JSON.stringify(config.body);
	}

	const response = await fetch(`${API_BASE}${endpoint}`, config);

	// 5. Handle response
	let data: any;
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
