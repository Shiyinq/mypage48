import { writable } from 'svelte/store';
import { browser } from '$app/environment';

// Imports for local usage (cleanup logic)
import { resetDashboard } from '$lib/stores/dashboard';
import { invalidateTheater } from '$lib/stores/theater';
import { ticketsStore } from '$lib/stores/tickets';
import { userProfile } from '$lib/stores/profile';
import { achievementsStore } from '$lib/stores/achievements';
import { galleryStore, topTwoShotStore } from '$lib/stores/memories';
import { isAuthenticated } from '$lib/stores/authStatus';

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
export { isAuthenticated } from '$lib/stores/authStatus';

export const isInitialDataLoaded = writable<boolean>(false);

// Logout cleanup logic
if (browser) {
	isAuthenticated.subscribe((value) => {
		if (!value) {
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
