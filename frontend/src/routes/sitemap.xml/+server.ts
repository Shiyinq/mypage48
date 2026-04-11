import type { RequestHandler } from './$types';

export const GET: RequestHandler = async () => {
	const baseUrl = 'https://mypage48.com';
	const pages = [
		'',
		'/login',
		'/register',
		'/jkt48/live',
		'/jkt48/live/multiview',
		'/jkt48/sorter',
		'/about',
		'/privacy',
		'/terms',
		'/cookies',
		'/jkt48/news',
		'/jkt48/members',
		'/jkt48/calendar',
		'/jkt48/events',
		'/jkt48/event-history'
	];

	const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${pages
	.map((page) => {
		let priority = '0.8';
		let changefreq = 'weekly';

		if (page === '') {
			priority = '1.0';
			changefreq = 'daily';
		} else if (
			page === '/login' ||
			page === '/register' ||
			page === '/jkt48/live' ||
			page === '/jkt48/live/multiview' ||
			page === '/jkt48/sorter'
		) {
			priority = '0.9';
			changefreq = page.includes('/live') ? 'daily' : 'monthly';
		}

		return `  <url>
    <loc>${baseUrl}${page}</loc>
    <changefreq>${changefreq}</changefreq>
    <priority>${priority}</priority>
  </url>`;
	})
	.join('\n')}
</urlset>`;

	return new Response(sitemap, {
		headers: {
			'Content-Type': 'application/xml',
			'Cache-Control': 'public, max-age=3600'
		}
	});
};
