import type { Cookies } from '@sveltejs/kit';

export type Locale = 'id' | 'en' | 'ja';

/**
 * Centrally detects the appropriate locale based on URL, Cookies, and Device settings.
 */
export function detectLocale(request: Request, cookies: Cookies, url: URL): Locale {
	// 1. URL Priority (?lang=)
	const urlLocale = url.searchParams.get('lang');
	if (urlLocale && (urlLocale === 'id' || urlLocale === 'en' || urlLocale === 'ja')) {
		return urlLocale as Locale;
	}

	// 2. Cookie Priority
	const cookieLocale = cookies.get('mypage48_locale');
	if (cookieLocale && (cookieLocale === 'id' || cookieLocale === 'en' || cookieLocale === 'ja')) {
		return cookieLocale as Locale;
	}

	// 3. Device/Browser Language (Accept-Language header)
	const acceptLanguage = request.headers.get('accept-language');
	if (acceptLanguage) {
		const preferredLocales = acceptLanguage.split(',').map((l) => l.split(';')[0].trim().split('-')[0]);
		const found = preferredLocales.find((l) => l === 'id' || l === 'en' || l === 'ja');
		if (found) return found as Locale;
	}

	// 4. Default Fallback
	return 'id';
}
