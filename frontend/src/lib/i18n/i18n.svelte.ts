import { startCircularViewTransition } from '$lib/utils/view-transition';

// Import translation files
import id from './locales/id.json';
import en from './locales/en.json';
import ja from './locales/ja.json';

// Types
export type Locale = 'id' | 'en' | 'ja';

export interface LocaleInfo {
	code: Locale;
	name: string;
	nativeName: string;
	flag: string;
}

export type TranslationValue = string | Record<string, unknown>;

export interface Translations {
	[key: string]: TranslationValue | Translations;
}

// Available locales configuration
export const locales: LocaleInfo[] = [
	{ code: 'id', name: 'Indonesian', nativeName: 'Bahasa Indonesia', flag: '🇮🇩' },
	{ code: 'en', name: 'English', nativeName: 'English', flag: '🇺🇸' },
	{ code: 'ja', name: 'Japanese', nativeName: '日本語', flag: '🇯🇵' }
];

// Translation dictionaries
const translations: Record<Locale, Translations> = {
	id,
	en,
	ja
};

// Default locale (Indonesian)
const DEFAULT_LOCALE: Locale = 'id';
const STORAGE_KEY = 'mypage48_locale';

// Check if we're in browser environment
const isBrowser = typeof window !== 'undefined';

// Get stored locale from localStorage
function getStoredLocale(): Locale | null {
	if (isBrowser) {
		const stored = localStorage.getItem(STORAGE_KEY);
		if (stored && (stored === 'id' || stored === 'en' || stored === 'ja')) {
			return stored as Locale;
		}
	}
	return null;
}

// Global reactive state for locale
let _locale = $state<Locale>(getStoredLocale() ?? DEFAULT_LOCALE);

/**
 * Locale manager - migrated to Svelte 5 Runes
 */
export const locale = {
	get value() {
		return _locale;
	},
	set value(newLocale: Locale) {
		if (locales.some((l) => l.code === newLocale)) {
			_locale = newLocale;
			if (isBrowser) {
				localStorage.setItem(STORAGE_KEY, newLocale);
				// Set cookie for SSR support (expires in 1 year)
				document.cookie = `${STORAGE_KEY}=${newLocale}; path=/; max-age=31536000; SameSite=Lax`;
				// Update html lang attribute
				document.documentElement.lang = newLocale;
			}
		}
	},
	// Compatibility setter
	set: (v: Locale) => {
		locale.value = v;
	}
};

/**
 * Function to change locale with transition
 */
export function setLocale(newLocale: Locale): void {
	if (locales.some((l) => l.code === newLocale)) {
		startCircularViewTransition(() => {
			locale.value = newLocale;
		});
	}
}

/**
 * Get current locale info reactively
 */
export function getCurrentLocaleInfo(): LocaleInfo {
	return locales.find((l) => l.code === _locale) || locales[0];
}

// Get nested value from object using dot notation
function getNestedValue(obj: Translations, path: string): string {
	const keys = path.split('.');
	let current: unknown = obj;

	for (const key of keys) {
		if (current && typeof current === 'object' && key in current) {
			current = (current as Record<string, unknown>)[key];
		} else {
			return path; // Return the key if not found
		}
	}

	return typeof current === 'string' ? current : path;
}

/**
 * Translation function - now a Svelte 5 reactive function
 */
export function t(key: string, params?: Record<string, string | number>): string {
	const translation = getNestedValue(translations[_locale], key);

	if (params) {
		return Object.entries(params).reduce((str, [paramKey, value]) => {
			return str.replace(new RegExp(`{${paramKey}}`, 'g'), String(value));
		}, translation);
	}

	return translation;
}

/**
 * Reactive time formatting
 */
export function formatTime(
	date: Date | string | number,
	options: Intl.DateTimeFormatOptions = {}
): string {
	const d = new Date(date);
	if (isNaN(d.getTime())) return String(date);

	const localeMap: Record<Locale, string> = {
		id: 'id-ID',
		en: 'en-US',
		ja: 'ja-JP'
	};

	return d.toLocaleTimeString(localeMap[_locale], options);
}

/**
 * Reactive date formatting
 */
export function formatDate(
	date: Date | string | number,
	options: Intl.DateTimeFormatOptions = {}
): string {
	const d = new Date(date);
	if (isNaN(d.getTime())) return String(date);

	const localeMap: Record<Locale, string> = {
		id: 'id-ID',
		en: 'en-US',
		ja: 'ja-JP'
	};

	return d.toLocaleDateString(localeMap[_locale], options);
}

// Export a reactive object similar to the old derived store for easier migration
export const i18n = {
	t,
	formatDate,
	formatTime
};
