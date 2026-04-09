<script lang="ts">
	export let title: string;
	export let description: string =
		'MyPage48 - Your ultimate JKT48 theater companion. Track your theater visits, 2-shots, and achievements.';
	export let image: string = '/favicon.png';
	export let path: string = '/';
	export let keywords: string = 'JKT48, Theater, MyPage48, JKT48 Fan, 2shot, Sorter, News';

	const baseUrl = 'https://mypage48.com';
	$: fullTitle =
		title === 'Home' ? 'MyPage48 | Your JKT48 Theater Companion' : `${title} | MyPage48`;
	$: fullUrl = `${baseUrl}${path}`;
	$: fullImage = image.startsWith('http') ? image : `${baseUrl}${image}`;

	const jsonLd = {
		'@context': 'https://schema.org',
		'@type': 'WebSite',
		name: 'MyPage48',
		url: baseUrl,
		description: description,
		potentialAction: {
			'@type': 'SearchAction',
			target: `${baseUrl}/search?q={search_term_string}`,
			'query-input': 'required name=search_term_string'
		}
	};

	const organizationJsonLd = {
		'@context': 'https://schema.org',
		'@type': 'Organization',
		name: 'MyPage48',
		url: baseUrl,
		logo: `${baseUrl}/favicon.png`,
		sameAs: ['https://github.com/Shiyinq/mypage48']
	};

	$: breadcrumbJsonLd =
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
			: null;
</script>

<svelte:head>
	<title>{fullTitle}</title>
	<meta name="description" content={description} />
	<meta name="keywords" content={keywords} />
	<meta name="author" content="MyPage48" />
	<meta name="robots" content="index, follow" />

	<!-- Theme and Mobile -->
	<meta name="theme-color" content="#dc2626" />
	<meta name="apple-mobile-web-app-capable" content="yes" />
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
	<script type="application/ld+json">
		{JSON.stringify(jsonLd)}
	</script>
	<script type="application/ld+json">
		{JSON.stringify(organizationJsonLd)}
	</script>
	{#if breadcrumbJsonLd}
		<script type="application/ld+json">
			{JSON.stringify(breadcrumbJsonLd)}
		</script>
	{/if}

	<!-- Hreflang for Multi-language SEO (using query params) -->
	<link rel="alternate" hreflang="id" href={`${baseUrl}${path === '/' ? '' : path}?lang=id`} />
	<link rel="alternate" hreflang="en" href={`${baseUrl}${path === '/' ? '' : path}?lang=en`} />
	<link rel="alternate" hreflang="ja" href={`${baseUrl}${path === '/' ? '' : path}?lang=ja`} />
	<link rel="alternate" hreflang="x-default" href={`${baseUrl}${path === '/' ? '' : path}`} />
</svelte:head>
