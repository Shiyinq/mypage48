import { t as translate, locale, setLocale, locales, getCurrentLocaleInfo } from './index';
import type { Locale } from './index';

/**
 * Custom hook for using translations in Svelte components - migrated to Svelte 5 Runes
 * Provides a reactive way to access translations and locale utilities
 */
export function useTranslation() {
	// Change locale function
	const changeLocale = (newLocale: Locale): void => {
		setLocale(newLocale);
	};

	// Get all available locales
	const availableLocales = locales;

	// Check if current locale matches
	const isLocale = (checkLocale: Locale): boolean => {
		return locale.value === checkLocale;
	};

	return {
		// Translation function (reactive)
		t: translate,

		// Current locale object (reactive value)
		locale,

		// Locale info with flag and native name (reactive)
		get localeInfo() {
			return getCurrentLocaleInfo();
		},

		changeLocale,
		availableLocales,
		isLocale,

		// Reactive checker
		isCurrentLocale: (checkLocale: Locale) => locale.value === checkLocale
	};
}

// Re-export types and utilities for convenience
export { type Locale, type LocaleInfo } from './index';
export { locale, setLocale, locales } from './index';
