import { browser } from '$app/environment';

// Imports for local usage (cleanup logic)
import { resetDashboard } from '$lib/stores/dashboard.svelte';
import { invalidateTheater } from '$lib/stores/theater.svelte';
import { ticketsStore } from '$lib/stores/tickets.svelte';
import { userProfile } from '$lib/stores/profile.svelte';
import { pageHeaderStore } from '$lib/stores/ui.svelte';
import { achievementsStore } from '$lib/stores/achievements.svelte';
import { galleryStore, topTwoShotStore } from '$lib/stores/memories.svelte';
import { isAuthenticated } from '$lib/stores/authStatus.svelte';
import { isInitialDataLoaded } from './global.svelte';

// Re-export all stores for consumers
export * from '$lib/stores/dashboard.svelte';
export * from '$lib/stores/theater.svelte';
export * from '$lib/stores/tickets.svelte';
export * from '$lib/stores/profile.svelte';
export * from '$lib/stores/achievements.svelte';
export * from '$lib/stores/memories.svelte';
export * from '$lib/stores/toast.svelte';
export * from '$lib/stores/ui.svelte';
export * from '$lib/stores/storage.svelte';
export * from '$lib/stores/events.svelte';
export * from '$lib/stores/auth.svelte';
export * from '$lib/stores/theme.svelte';
export * from '$lib/stores/accessToken.svelte';
export * from '$lib/stores/admin.svelte';
export * from '$lib/stores/live.svelte';
export * from '$lib/stores/playground.svelte';
export * from '$lib/stores/radio.svelte';
export { isAuthenticated } from '$lib/stores/authStatus.svelte';
export { isInitialDataLoaded } from './global.svelte';

// Logout cleanup logic
if (browser) {
	isAuthenticated.subscribe((value) => {
		if (!value) {
			// Cleanup state on logout
			ticketsStore.reset();
			achievementsStore.reset();
			galleryStore.reset();
			topTwoShotStore.reset();
			isInitialDataLoaded.value = false;
			pageHeaderStore.reset();

			// Reset custom stores
			userProfile.reset();
			resetDashboard();
			invalidateTheater();
		}
	});
}
