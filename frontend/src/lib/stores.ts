import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import type { Ticket } from './types';

const STORAGE_KEY = 'oshi_log_tickets_v2';
const AUTH_KEY = 'oshi_log_auth';

// Initialize from localStorage if in browser
const initialTickets = browser ? JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]') : [];
const initialAuth = browser ? localStorage.getItem(AUTH_KEY) === 'true' : false;

export const tickets = writable<Ticket[]>(initialTickets);
export const isAuthenticated = writable<boolean>(initialAuth);

// Subscribe to changes and update localStorage
// Toast Store
export const toast = writable<{ message: string; type?: 'success' | 'error' } | null>(null);

export const showToast = (message: string, type: 'success' | 'error' = 'success') => {
    toast.set({ message, type });
    setTimeout(() => {
        toast.set(null);
    }, 3000);
};

if (browser) {
    tickets.subscribe((value) => localStorage.setItem(STORAGE_KEY, JSON.stringify(value)));
    isAuthenticated.subscribe((value) => {
        if (value) localStorage.setItem(AUTH_KEY, 'true');
        else localStorage.removeItem(AUTH_KEY);
    });
}
