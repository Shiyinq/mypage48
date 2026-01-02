import { writable } from 'svelte/store';
import type { DashboardStats } from '$lib/types';

const currentYear = new Date().getFullYear();

export const dashboardFilter = writable({
    selectedYear: currentYear,
    startMonth: 0,
    endMonth: 11,
    isAllData: false
});

export const dashboardStatsData = writable<DashboardStats | null>(null);
export const lastFetchedFilter = writable<string>("");

// Call this when data changes (upload/delete ticket)
export function invalidateDashboard() {
    dashboardStatsData.set(null);
    lastFetchedFilter.set("");
}

// Call this on logout to fully reset
export function resetDashboard() {
    dashboardFilter.set({
        selectedYear: new Date().getFullYear(),
        startMonth: 0,
        endMonth: 11,
        isAllData: false
    });
    invalidateDashboard();
}
