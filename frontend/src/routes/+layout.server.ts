import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ cookies, url }) => {
	// Check if we are on a public profile route
	const isPublicProfile = url.pathname.startsWith('/u/');

	// Default fallback: 'en' for public profiles, 'id' for others
	const defaultLocale = isPublicProfile ? 'en' : 'id';

	// Get locale from query param first (?lang=..), then cookie, then default fallback
	const urlLocale = url.searchParams.get('lang');
	let locale = cookies.get('mypage48_locale') || defaultLocale;
	
	// If valid lang param is provided, override and set cookie for future visits
	if (urlLocale && ['id', 'en', 'ja'].includes(urlLocale)) {
		locale = urlLocale;
		cookies.set('mypage48_locale', locale as string, { path: '/', maxAge: 31536000, sameSite: 'lax' });
	}

	// Check for auth hint cookie
	const hasSession = cookies.get('mypage48_auth') === 'true';

	return {
		locale,
		hasSession
	};
};
