import { client } from './client';
import type { NewsPaginationResponse, News } from '$lib/types';

export const news = {
	getNews: async (page = 1, limit = 12, startDate?: string, endDate?: string) => {
		const query = new URLSearchParams({
			page: page.toString(),
			limit: limit.toString()
		});
		if (startDate) query.append('start_date', startDate);
		if (endDate) query.append('end_date', endDate);

		return await client<NewsPaginationResponse>(`/theater/news?${query.toString()}`);
	},
	getNewsByLink: async (link: string) => {
		return await client<News>(`/theater/news/${link}`);
	}
};
