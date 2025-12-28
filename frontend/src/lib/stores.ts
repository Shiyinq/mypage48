import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import type { Ticket, User } from './types';

const AUTH_KEY = 'oshi_log_auth';
const OLD_STORAGE_KEY = 'oshi_log_tickets_v2'; // For cleanup

// Initialize auth from localStorage if in browser
const initialAuth = browser ? localStorage.getItem(AUTH_KEY) === 'true' : false;

// Tickets are now fetched from API only, not stored in localStorage
export const tickets = writable<Ticket[]>([]);
export const isAuthenticated = writable<boolean>(initialAuth);
export const userProfile = writable<User | null>(null);
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
        if (value) localStorage.setItem(AUTH_KEY, 'true');
        else localStorage.removeItem(AUTH_KEY);
    });
}

