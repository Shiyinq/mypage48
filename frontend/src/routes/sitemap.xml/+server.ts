import type { RequestHandler } from './$types';

export const GET: RequestHandler = async () => {
	const baseUrl = 'https://mypage48.com';
	const languages = ['id', 'en', 'ja'];
	const pages = [
		'', // Home
		'/jkt48/events',
		'/jkt48/news',
		'/jkt48/live',
		'/jkt48/live/multiview',
		'/jkt48/members',
		'/jkt48/calendar',
		'/jkt48/event-history',
		'/jkt48/sorter',
		'/about',
		'/login',
		'/register',
		'/privacy',
		'/terms',
		'/cookies'
	];

	const sitemap = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
${pages
	.map((page) => {
		let priority = '0.5';
		let changefreq = 'weekly';

		if (page === '') {
			priority = '1.0';
			changefreq = 'daily';
		} else if (
			[
				'/jkt48/events',
				'/jkt48/news',
				'/jkt48/live',
				'/jkt48/live/multiview',
				'/jkt48/members',
				'/jkt48/calendar',
				'/jkt48/event-history'
			].includes(page)
		) {
			priority = '0.9';
			changefreq = 'daily';
		} else if (['/privacy', '/terms', '/cookies'].includes(page)) {
			priority = '0.1';
			changefreq = 'monthly';
		}

		const url = `${baseUrl}${page}`;

		// Generate localized alternates
		const alternates = languages
			.map(
				(lang) => `    <xhtml:link rel="alternate" hreflang="${lang}" href="${url}?lang=${lang}" />`
			)
			.join('\n');
		const xDefault = `    <xhtml:link rel="alternate" hreflang="x-default" href="${url}" />`;

		return `  <url>
    <loc>${url}</loc>
${alternates}
${xDefault}
    <changefreq>${changefreq}</changefreq>
    <priority>${priority}</priority>
  </url>`;
	})
	.join('\n')}
</urlset>`.trim();

	return new Response(sitemap, {
		headers: {
			'Content-Type': 'text/xml',
			'Cache-Control': 'public, max-age=3600'
		}
	});
};
