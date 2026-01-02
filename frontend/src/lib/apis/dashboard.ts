import { client } from './client';
import type { DashboardStats } from '$lib/types';

export interface DashboardStatsParams {
    year?: number;
    startMonth?: number;
    endMonth?: number;
    isAllData?: boolean;
}

export const dashboard = {
    getStats: async (params: DashboardStatsParams = {}): Promise<DashboardStats> => {
        const searchParams = new URLSearchParams();

        if (params.year !== undefined) {
            searchParams.set('year', params.year.toString());
        }
        if (params.startMonth !== undefined) {
            searchParams.set('start_month', params.startMonth.toString());
        }
        if (params.endMonth !== undefined) {
            searchParams.set('end_month', params.endMonth.toString());
        }
        if (params.isAllData !== undefined) {
            searchParams.set('is_all_data', params.isAllData.toString());
        }

        const queryString = searchParams.toString();
        const endpoint = `/dashboard/stats${queryString ? `?${queryString}` : ''}`;

        return client<DashboardStats>(endpoint);
    }
};
