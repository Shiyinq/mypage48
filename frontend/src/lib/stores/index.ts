import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import { resetDashboard } from '$lib/stores/dashboard';
import { invalidateTheater } from '$lib/stores/theater';
import { ticketsStore } from '$lib/stores/tickets';
import { userProfile } from '$lib/stores/profile';
import { achievementsStore } from '$lib/stores/achievements';
import { galleryStore, topTwoShotStore } from '$lib/stores/memories';

// Re-export from separate store files
export { ticketsStore, tickets, ticketsPagination, ticketsFilters } from '$lib/stores/tickets';
export { userProfile } from '$lib/stores/profile';
export { achievementsStore } from '$lib/stores/achievements';
export { storageStore } from '$lib/stores/storage';

const AUTH_KEY = 'oshi_log_auth';
const OLD_STORAGE_KEY = 'oshi_log_tickets_v2'; // For cleanup

// Initialize auth from localStorage if in browser
const initialAuth = browser ? localStorage.getItem(AUTH_KEY) === 'true' : false;

// Auth & App State
export const isAuthenticated = writable<boolean>(initialAuth);
export const isInitialDataLoaded = writable<boolean>(false);

// Re-export toast store
export { toast, showToast } from '$lib/stores/toast';

// Logout cleanup logic
if (browser) {
	// Cleanup old localStorage data
	localStorage.removeItem(OLD_STORAGE_KEY);

	isAuthenticated.subscribe((value) => {
		if (value) {
			localStorage.setItem(AUTH_KEY, 'true');
		} else {
			localStorage.removeItem(AUTH_KEY);
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
