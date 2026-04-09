import { client } from './client';
import type { NewsPaginationResponse, News } from '$lib/types';

export const news = {
	getNews: async (page = 1, limit = 12) => {
		return await client<NewsPaginationResponse>(`/theater/news/?page=${page}&limit=${limit}`);
	},
	getNewsByLink: async (link: string) => {
		return await client<News>(`/theater/news/${link}`);
	}
};
