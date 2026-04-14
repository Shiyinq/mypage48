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
	return 'auto';
}

// Shared Rune State for Theme
let currentTheme = $state<Theme>(getInitialTheme());

export const theme = {
	get value() {
		return currentTheme;
	},

	apply(selectedTheme: Theme): void {
		if (!browser) return;

		const root = document.documentElement;
		let effectiveTheme: 'light' | 'dark';

		if (selectedTheme === 'auto') {
			effectiveTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
		} else {
			effectiveTheme = selectedTheme;
		}

		if (effectiveTheme === 'dark') {
			root.classList.add('dark');
		} else {
			root.classList.remove('dark');
		}
	},

	set(newTheme: Theme): void {
		if (!browser) return;

		localStorage.setItem(THEME_KEY, newTheme);
		currentTheme = newTheme;

		startCircularViewTransition(() => {
			this.apply(newTheme);
		});
	},

	init(): void {
		if (!browser) return;

		const current = getInitialTheme();
		this.apply(current);

		// Listen to system preference changes when on 'auto'
		const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
		mediaQuery.addEventListener('change', () => {
			if (localStorage.getItem(THEME_KEY) === 'auto') {
				this.apply('auto');
			}
		});
	}
};

// Backward compatibility for functions
export const setTheme = (newTheme: Theme) => theme.set(newTheme);
export const applyTheme = (selectedTheme: Theme) => theme.apply(selectedTheme);
export const initTheme = () => theme.init();
