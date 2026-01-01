import { derived, get } from 'svelte/store';
import type { Readable } from 'svelte/store';
import { locale, i18n, setLocale, locales, currentLocaleInfo } from './index';
import type { Locale, LocaleInfo } from './index';

/**
 * Custom hook for using translations in Svelte components
 * Provides a reactive way to access translations and locale utilities
 */
export function useTranslation() {
	// Get the reactive translation function
	const t: Readable<(key: string, params?: Record<string, string | number>) => string> = i18n;

	// Get the current locale
	const currentLocale: Readable<Locale> = locale;

	// Get locale info with flag and native name
	const localeInfo: Readable<LocaleInfo> = currentLocaleInfo;

	// Change locale function
	const changeLocale = (newLocale: Locale): void => {
		setLocale(newLocale);
	};

	// Get all available locales
	const availableLocales = locales;

	// Check if current locale matches
	const isLocale = (checkLocale: Locale): boolean => {
		return get(locale) === checkLocale;
	};

	// Derived store to check current locale reactively
	const isCurrentLocale: Readable<(checkLocale: Locale) => boolean> = derived(
		locale,
		($locale) => (checkLocale: Locale) => $locale === checkLocale
	);

	return {
		t,
		locale: currentLocale,
		localeInfo,
		changeLocale,
		availableLocales,
		isLocale,
		isCurrentLocale
	};
}

// Re-export types and utilities for convenience
export { type Locale, type LocaleInfo } from './index';
export { locale, setLocale, locales } from './index';
