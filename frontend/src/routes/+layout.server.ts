import type { LayoutServerLoad } from './$types';
import { detectLocale } from '$lib/i18n/server';

export const load: LayoutServerLoad = async ({ cookies, url, request }) => {
	// Detect locale using centralized utility
	const locale = detectLocale(request, cookies, url);

	// If valid lang param is provided via URL, ensure cookie is set for future visits
	const urlLocale = url.searchParams.get('lang');
	if (urlLocale && ['id', 'en', 'ja'].includes(urlLocale)) {
		cookies.set('mypage48_locale', urlLocale, {
			path: '/',
			maxAge: 31536000,
			sameSite: 'lax'
		});
	} else if (!cookies.get('mypage48_locale')) {
		// Also persist the detected device language to cookie if none exists
		cookies.set('mypage48_locale', locale, {
			path: '/',
			maxAge: 31536000,
			sameSite: 'lax'
		});
	}

	// Check for auth hint cookie
	const hasSession = cookies.get('mypage48_auth') === 'true';

	return {
		locale,
		hasSession
	};
};
