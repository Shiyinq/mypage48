import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ cookies, url }) => {
	// Check if we are on a public profile route
	const isPublicProfile = url.pathname.startsWith('/u/');

	// Default fallback: 'en' for public profiles, 'id' for others
	const defaultLocale = isPublicProfile ? 'en' : 'id';

	// Get locale from cookie, default to determined fallback if not present
	const locale = cookies.get('mypage48_locale') || defaultLocale;

	// Check for auth hint cookie
	const hasSession = cookies.get('mypage48_auth') === 'true';

	return {
		locale,
		hasSession
	};
};
