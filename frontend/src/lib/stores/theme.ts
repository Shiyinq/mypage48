import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import { startCircularViewTransition } from '$lib/utils/view-transition';

export type Theme = 'light' | 'dark' | 'auto';

const THEME_KEY = 'mypage48_theme';

// Get initial theme preference
function getInitialTheme(): Theme {
	if (!browser) return 'light';

	const stored = localStorage.getItem(THEME_KEY) as Theme | null;
	if (stored && ['light', 'dark', 'auto'].includes(stored)) {
		return stored;
	}
	return 'light';
}

// Create the theme store
export const theme = writable<Theme>(getInitialTheme());

// Apply theme to document
export function applyTheme(selectedTheme: Theme): void {
	if (!browser) return;

	const root = document.documentElement;
	let effectiveTheme: 'light' | 'dark';

	if (selectedTheme === 'auto') {
		// Use system preference
		effectiveTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
	} else {
		effectiveTheme = selectedTheme;
	}

	if (effectiveTheme === 'dark') {
		root.classList.add('dark');
	} else {
		root.classList.remove('dark');
	}
}

// Set theme and persist to localStorage
// Set theme and persist to localStorage
export function setTheme(newTheme: Theme): void {
	if (!browser) return;

	localStorage.setItem(THEME_KEY, newTheme);
	theme.set(newTheme);

	startCircularViewTransition(() => {
		applyTheme(newTheme);
	});
}

// Initialize theme on app load
export function initTheme(): void {
	if (!browser) return;

	const currentTheme = getInitialTheme();
	applyTheme(currentTheme);

	// Listen to system preference changes when on 'auto'
	const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
	mediaQuery.addEventListener('change', () => {
		const storedTheme = localStorage.getItem(THEME_KEY) as Theme | null;
		if (storedTheme === 'auto') {
			applyTheme('auto');
		}
	});
}
