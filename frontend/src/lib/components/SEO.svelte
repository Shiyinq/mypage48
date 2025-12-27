<script lang="ts">
	export let title: string;
	export let description: string =
		'MyPage48 - Your ultimate JKT48 theater companion. Track your theater visits, 2-shots, and achievements.';
	export let image: string = '/favicon.png';
	export let path: string = '/';

	const baseUrl = 'https://mypage48.com';
	$: fullTitle = `${title} | MyPage48`;
	$: fullUrl = `${baseUrl}${path}`;
	$: fullImage = image.startsWith('http') ? image : `${baseUrl}${image}`;
</script>

<svelte:head>
	<title>{fullTitle}</title>
	<meta name="description" content={description} />

	<!-- Open Graph / Facebook -->
	<meta property="og:type" content="website" />
	<meta property="og:url" content={fullUrl} />
	<meta property="og:title" content={fullTitle} />
	<meta property="og:description" content={description} />
	<meta property="og:image" content={fullImage} />

	<!-- Twitter -->
	<meta property="twitter:card" content="summary_large_image" />
	<meta property="twitter:url" content={fullUrl} />
	<meta property="twitter:title" content={fullTitle} />
	<meta property="twitter:description" content={description} />
	<meta property="twitter:image" content={fullImage} />

	<link rel="canonical" href={fullUrl} />
</svelte:head>
