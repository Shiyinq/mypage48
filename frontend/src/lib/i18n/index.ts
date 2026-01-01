import { writable, derived, get } from 'svelte/store';
import type { Writable, Readable } from 'svelte/store';

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

// Create the locale store - start with stored value if available, else default
// We export a set function that can be used to hydrate from server data
const initialLocale = getStoredLocale() ?? DEFAULT_LOCALE;
export const locale: Writable<Locale> = writable<Locale>(initialLocale);

// Subscribe to locale changes and persist to localStorage AND Cookie
locale.subscribe((value) => {
	if (isBrowser) {
		localStorage.setItem(STORAGE_KEY, value);

		// Set cookie for SSR support (expires in 1 year)
		document.cookie = `${STORAGE_KEY}=${value}; path=/; max-age=31536000; SameSite=Lax`;

		// Update html lang attribute
		document.documentElement.lang = value;
	}
});

// Function to change locale
export function setLocale(newLocale: Locale): void {
	if (locales.some((l) => l.code === newLocale)) {
		locale.set(newLocale);
	}
}

// Get current locale info
export const currentLocaleInfo: Readable<LocaleInfo> = derived(locale, ($locale) => {
	return locales.find((l) => l.code === $locale) || locales[0];
});

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

// Translation function
export function t(key: string, params?: Record<string, string | number>): string {
	const currentLocale = get(locale);
	const translation = getNestedValue(translations[currentLocale], key);

	if (params) {
		return Object.entries(params).reduce((str, [paramKey, value]) => {
			return str.replace(new RegExp(`{${paramKey}}`, 'g'), String(value));
		}, translation);
	}

	return translation;
}

// Derived store for reactive translations
export const i18n: Readable<(key: string, params?: Record<string, string | number>) => string> =
	derived(locale, ($locale) => {
		return (key: string, params?: Record<string, string | number>): string => {
			const translation = getNestedValue(translations[$locale], key);

			if (params) {
				return Object.entries(params).reduce((str, [paramKey, value]) => {
					return str.replace(new RegExp(`{${paramKey}}`, 'g'), String(value));
				}, translation);
			}

			return translation;
		};
	});
