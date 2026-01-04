import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import type { Ticket, UserWithProfileStats, AchievementsResponse, TicketFilters, PaginationState } from './types';
import { resetDashboard } from '$lib/stores/dashboard';
import { invalidateTheater } from '$lib/stores/theater';

const AUTH_KEY = 'oshi_log_auth';
const OLD_STORAGE_KEY = 'oshi_log_tickets_v2'; // For cleanup

// Initialize auth from localStorage if in browser
const initialAuth = browser ? localStorage.getItem(AUTH_KEY) === 'true' : false;

// Tickets are now fetched from API only, not stored in localStorage
export const tickets = writable<Ticket[]>([]);
export const ticketsFilters = writable<TicketFilters>({});
// Cache for the default (unfiltered) ticket list and its pagination state
// This allows restoring the exact scroll position/page count when clearing filters
export const defaultTickets = writable<Ticket[] | null>(null);
export const defaultTicketsPagination = writable<PaginationState | null>(null);

// Active pagination state for the currently displayed list (filtered or default)
export const ticketsPagination = writable<PaginationState>({
	page: 0,
	hasMore: true
});
export const isAuthenticated = writable<boolean>(initialAuth);
export const userProfile = writable<UserWithProfileStats | null>(null);
export const achievementsData = writable<AchievementsResponse | null>(null);
export const isInitialDataLoaded = writable<boolean>(false);

// Toast Store
export const toast = writable<{ message: string; type?: 'success' | 'error' } | null>(null);

export const showToast = (message: string, type: 'success' | 'error' = 'success') => {
	toast.set({ message, type });
	setTimeout(() => {
		toast.set(null);
	}, 3000);
};

if (browser) {
	// Cleanup old localStorage data
	localStorage.removeItem(OLD_STORAGE_KEY);

	isAuthenticated.subscribe((value) => {
		if (value) {
			localStorage.setItem(AUTH_KEY, 'true');
		} else {
			localStorage.removeItem(AUTH_KEY);
			// Cleanup state on logout
			tickets.set([]);
			ticketsPagination.set({ page: 0, hasMore: true });
			ticketsFilters.set({});
			defaultTickets.set(null);
			defaultTicketsPagination.set(null);
			userProfile.set(null);
			achievementsData.set(null);
			isInitialDataLoaded.set(false);
			resetDashboard();
			invalidateTheater();
		}
	});
}
