import { error } from '@sveltejs/kit';
import { news } from '$lib/apis/news';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ params }) => {
    const { link } = params;
    
    try {
        // Fetch current news and latest news concurrent
        const [item, recentNewsResponse] = await Promise.all([
            news.getNewsByLink(link),
            news.getNews(1, 10)
        ]);

        return {
            item,
            recentNews: recentNewsResponse.data
        };
    } catch (e: any) {
        throw error(404, e?.detail || 'News not found');
    }
};
