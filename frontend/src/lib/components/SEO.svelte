<script lang="ts">
	import { getExternalMediaUrl } from '$lib/utils/media';
	import type { Event } from '$lib/types/events';
	import type { News } from '$lib/types/news';

	const serializeSchema = (data: Record<string, unknown> | null | undefined) => {
		if (!data) return '';
		return JSON.stringify(data).replace(/</g, '\\u003c').replace(/>/g, '\\u003e');
	};

	interface Props {
		title: string;
		description?: string;
		image?: string;
		path?: string;
		keywords?: string;
		events?: Event[];
		article?: News | null;
		articles?: News[];
	}

	let {
		title,
		description = 'MyPage48 - Your ultimate JKT48 theater companion. Track your theater visits, 2-shots, and achievements.',
		image = '/favicon.png',
		path = '/',
		keywords = 'MyPage48, My Page JKT48, JKT48 Fan, Oshi Sorter, JKT48, JKT48 Theater, JKT48 News, JKT48 Live, JKT48 Showroom, JKT48 IDN Live',
		events = [],
		article = null,
		articles = []
	}: Props = $props();

	const baseUrl = 'https://mypage48.com';
	let fullTitle = $derived(
		title === 'Home' ? 'MyPage48 | Your JKT48 Theater Companion' : `${title} | MyPage48`
	);
	let fullUrl = $derived(`${baseUrl}${path}`);
	let fullImage = $derived(image.startsWith('http') ? image : `${baseUrl}${image}`);

	let jsonLd = $derived({
		'@context': 'https://schema.org',
		'@type': 'WebSite',
		name: 'MyPage48',
		alternateName: 'MyPage48',
		url: 'https://mypage48.com/',
		description: description,
		potentialAction: {
			'@type': 'SearchAction',
			target: `${baseUrl}/search?q={search_term_string}`,
			'query-input': 'required name=search_term_string'
		}
	});

	let webPageJsonLd = $derived({
		'@context': 'https://schema.org',
		'@type': 'WebPage',
		name: fullTitle,
		description: description,
		url: fullUrl,
		image: fullImage,
		publisher: {
			'@type': 'Organization',
			name: 'MyPage48',
			logo: {
				'@type': 'ImageObject',
				url: `${baseUrl}/favicon.png`
			}
		}
	});

	const organizationJsonLd = {
		'@context': 'https://schema.org',
		'@type': 'Organization',
		name: 'MyPage48',
		url: baseUrl,
		logo: `${baseUrl}/favicon.png`,
		sameAs: ['https://github.com/Shiyinq/mypage48']
	};

	let breadcrumbJsonLd = $derived(
		path !== '/'
			? {
					'@context': 'https://schema.org',
					'@type': 'BreadcrumbList',
					itemListElement: [
						{
							'@type': 'ListItem',
							position: 1,
							name: 'Home',
							item: baseUrl
						},
						{
							'@type': 'ListItem',
							position: 2,
							name: title,
							item: fullUrl
						}
					]
				}
			: null
	);

	let eventJsonLd = $derived(
		(events || []).map((event) => {
			const start = new Date(event.date);
			const end = new Date(start.getTime() + 2 * 60 * 60 * 1000); // Estimate 2 hours

			return {
				'@context': 'https://schema.org',
				'@type': 'Event',
				name: event.title,
				startDate: event.date,
				endDate: end.toISOString(),
				location: {
					'@type': 'Place',
					name: 'JKT48 Theater',
					address: {
						'@type': 'PostalAddress',
						streetAddress: 'fX Sudirman F4',
						addressLocality: 'Jakarta',
						addressRegion: 'DKI Jakarta',
						postalCode: '10270',
						addressCountry: 'ID'
					}
				},
				image: event.imageUrl
					? [event.imageUrl]
					: ['https://placehold.co/640x960?text=JKT48+EVENT'],
				description: `${event.label || 'JKT48'} Theater Show - ${event.title}`,
				organizer: {
					'@type': 'Organization',
					name: 'JKT48',
					url: 'https://jkt48.com'
				},
				offers: {
					'@type': 'Offer',
					url: `https://jkt48.com${event.url || '/'}`,
					availability: 'https://schema.org/InStock',
					priceCurrency: 'IDR'
				},
				performer: {
					'@type': 'Organization',
					name: 'JKT48'
				},
				eventStatus: 'https://schema.org/EventScheduled',
				eventAttendanceMode: 'https://schema.org/OfflineEventAttendanceMode'
			};
		})
	);

	let articleJsonLd = $derived(
		article
			? {
					'@context': 'https://schema.org',
					'@type': 'NewsArticle',
					headline: article.title,
					description: article.short_description || article.title,
					image: article.background_image
						? [getExternalMediaUrl(article.background_image)]
						: [`${baseUrl}/favicon.png`],
					datePublished: article.valid_date_from,
					dateModified: article.valid_date_from,
					author: {
						'@type': 'Organization',
						name: 'JKT48',
						url: 'https://jkt48.com'
					},
					publisher: {
						'@type': 'Organization',
						name: 'MyPage48',
						logo: {
							'@type': 'ImageObject',
							url: `${baseUrl}/favicon.png`
						}
					},
					mainEntityOfPage: {
						'@type': 'WebPage',
						'@id': fullUrl
					},
					isBasedOn: `https://jkt48.com/news/${article.link}`
				}
			: null
	);

	let itemListJsonLd = $derived(
		articles && articles.length > 0
			? {
					'@context': 'https://schema.org',
					'@type': 'ItemList',
					itemListElement: articles.map((item, index) => ({
						'@type': 'ListItem',
						position: index + 1,
						item: {
							'@type': 'NewsArticle',
							url: `${baseUrl}/jkt48/news/${item.link}`,
							headline: item.title,
							datePublished: item.valid_date_from,
							image: item.background_image ? [getExternalMediaUrl(item.background_image)] : [],
							author: {
								'@type': 'Organization',
								name: 'JKT48',
								url: 'https://jkt48.com'
							},
							publisher: {
								'@type': 'Organization',
								name: 'MyPage48',
								logo: {
									'@type': 'ImageObject',
									url: `${baseUrl}/favicon.png`
								}
							}
						}
					}))
				}
			: null
	);
	const navigationJsonLd = {
		'@context': 'https://schema.org',
		'@type': 'ItemList',
		name: 'Main Navigation',
		itemListElement: [
			{
				'@type': 'SiteNavigationElement',
				position: 1,
				name: 'Login',
				url: `${baseUrl}/login`
			},
			{
				'@type': 'SiteNavigationElement',
				position: 2,
				name: 'Register',
				url: `${baseUrl}/register`
			},
			{
				'@type': 'SiteNavigationElement',
				position: 3,
				name: 'Live',
				url: `${baseUrl}/jkt48/live`
			},
			{
				'@type': 'SiteNavigationElement',
				position: 4,
				name: 'News',
				url: `${baseUrl}/jkt48/news`
			},
			{
				'@type': 'SiteNavigationElement',
				position: 5,
				name: 'Events',
				url: `${baseUrl}/jkt48/events`
			},
			{
				'@type': 'SiteNavigationElement',
				position: 6,
				name: 'Sorter',
				url: `${baseUrl}/jkt48/sorter`
			}
		]
	};

	let allSchemas = $derived(
		[
			path === '/' ? jsonLd : webPageJsonLd,
			path === '/' ? navigationJsonLd : null,
			organizationJsonLd,
			breadcrumbJsonLd,
			...(eventJsonLd || []),
			articleJsonLd,
			itemListJsonLd
		].filter(Boolean)
	);

	let ldJsonScripts = $derived(
		allSchemas
			.map(
				(schema) => `<script type="application/ld+json">${serializeSchema(schema)}</` + `script>`
			)
			.join('\n')
	);
</script>

<svelte:head>
	<title>{fullTitle}</title>
	<meta name="description" content={description} />
	<meta name="keywords" content={keywords} />
	<meta name="author" content="MyPage48" />
	<meta name="robots" content="index, follow" />

	<!-- Theme and Mobile -->
	<meta name="theme-color" content="#dc2626" />
	<meta name="mobile-web-app-capable" content="yes" />
	<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />

	<!-- Open Graph / Facebook -->
	<meta property="og:type" content="website" />
	<meta property="og:url" content={fullUrl} />
	<meta property="og:title" content={fullTitle} />
	<meta property="og:description" content={description} />
	<meta property="og:image" content={fullImage} />
	<meta property="og:site_name" content="MyPage48" />

	<!-- Twitter -->
	<meta property="twitter:card" content="summary_large_image" />
	<meta property="twitter:url" content={fullUrl} />
	<meta property="twitter:title" content={fullTitle} />
	<meta property="twitter:description" content={description} />
	<meta property="twitter:image" content={fullImage} />

	<link rel="canonical" href={fullUrl} />

	<!-- Structured Data -->
	<!-- eslint-disable-next-line svelte/no-at-html-tags -->
	{@html ldJsonScripts}

	<!-- Hreflang for Multi-language SEO (using query params) -->
	<link rel="alternate" hreflang="id" href={`${baseUrl}${path === '/' ? '' : path}?lang=id`} />
	<link rel="alternate" hreflang="en" href={`${baseUrl}${path === '/' ? '' : path}?lang=en`} />
	<link rel="alternate" hreflang="ja" href={`${baseUrl}${path === '/' ? '' : path}?lang=ja`} />
	<link rel="alternate" hreflang="x-default" href={`${baseUrl}${path === '/' ? '' : path}`} />
</svelte:head>
