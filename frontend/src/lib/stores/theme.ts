import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export type Theme = 'light' | 'dark' | 'auto';

const THEME_KEY = 'mypage48_theme';

// Get initial theme preference
function getInitialTheme(): Theme {
	if (!browser) return 'auto';

	const stored = localStorage.getItem(THEME_KEY) as Theme | null;
	if (stored && ['light', 'dark', 'auto'].includes(stored)) {
		return stored;
	}
	return 'auto';
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

	// Fallback for browsers without View Transitions API
	if (!document.startViewTransition) {
		applyTheme(newTheme);
		return;
	}

	const transition = document.startViewTransition(() => {
		applyTheme(newTheme);
	});

	transition.ready.then(() => {
		const x = window.innerWidth / 2;
		const y = window.innerHeight / 2;
		const endRadius = Math.hypot(
			Math.max(x, window.innerWidth - x),
			Math.max(y, window.innerHeight - y)
		);

		document.documentElement.animate(
			{
				clipPath: [
					`circle(0px at ${x}px ${y}px)`,
					`circle(${endRadius}px at ${x}px ${y}px)`
				]
			},
			{
				duration: 500,
				easing: 'ease-in-out',
				pseudoElement: '::view-transition-new(root)'
			}
		);
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
		if (storedTheme === 'auto' || !storedTheme) {
			applyTheme('auto');
		}
	});
}
