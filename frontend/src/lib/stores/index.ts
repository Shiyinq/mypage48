import { writable } from 'svelte/store';
import { browser } from '$app/environment';

// Imports for local usage (cleanup logic)
import { resetDashboard } from '$lib/stores/dashboard';
import { invalidateTheater } from '$lib/stores/theater';
import { ticketsStore } from '$lib/stores/tickets';
import { userProfile } from '$lib/stores/profile';
import { achievementsStore } from '$lib/stores/achievements';
import { galleryStore, topTwoShotStore } from '$lib/stores/memories';

// Re-export all stores for consumers
export * from '$lib/stores/dashboard';
export * from '$lib/stores/theater';
export * from '$lib/stores/tickets';
export * from '$lib/stores/profile';
export * from '$lib/stores/achievements';
export * from '$lib/stores/memories';
export * from '$lib/stores/toast';
export * from '$lib/stores/storage';
export * from '$lib/stores/events';
export * from '$lib/stores/auth';
export * from '$lib/stores/accessToken';
export * from '$lib/stores/admin';

// App Global State
const AUTH_KEY = 'oshi_log_auth';
const OLD_STORAGE_KEY = 'oshi_log_tickets_v2';

// Initialize auth from localStorage if in browser
const initialAuth = browser ? localStorage.getItem(AUTH_KEY) === 'true' : false;
export const isAuthenticated = writable<boolean>(initialAuth);
export const isInitialDataLoaded = writable<boolean>(false);

// Logout cleanup logic
if (browser) {
	// Cleanup old localStorage data
	localStorage.removeItem(OLD_STORAGE_KEY);

	isAuthenticated.subscribe((value) => {
		if (value) {
			localStorage.setItem(AUTH_KEY, 'true');
			// Set a non-secure cookie for successful auth hint to server (for SSR)
			document.cookie = 'mypage48_auth=true; path=/; max-age=31536000; SameSite=Lax';
		} else {
			localStorage.removeItem(AUTH_KEY);
			// Clear auth hint cookie
			document.cookie = 'mypage48_auth=; path=/; max-age=0; SameSite=Lax';

			// Cleanup state on logout
			ticketsStore.reset();
			achievementsStore.reset();
			galleryStore.reset();
			topTwoShotStore.reset();
			isInitialDataLoaded.set(false);

			// Reset custom stores
			userProfile.reset();
			resetDashboard();
			invalidateTheater();
		}
	});
}
