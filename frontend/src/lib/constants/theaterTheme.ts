export const THEATER_THEMES = {
	pink: {
		navActive: 'bg-pink-600 text-white shadow-lg shadow-pink-500/30 ring-1 ring-pink-400',
		navInactive:
			'hover:text-pink-600 dark:hover:text-pink-400 hover:bg-white dark:hover:bg-pink-900/20 border-gray-100 dark:border-zinc-700',
		headerIcon:
			'bg-pink-50 dark:bg-pink-900/30 text-pink-600 dark:text-pink-400 shadow-pink-100 dark:shadow-pink-900/20',
		titleLine: 'bg-pink-200/60 dark:bg-pink-500/30'
	},
	blue: {
		navActive: 'bg-blue-600 text-white shadow-lg shadow-blue-500/30 ring-1 ring-blue-400',
		navInactive:
			'hover:text-blue-600 dark:hover:text-blue-400 hover:bg-white dark:hover:bg-blue-900/20 border-gray-100 dark:border-zinc-700',
		headerIcon:
			'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 shadow-blue-100 dark:shadow-blue-900/20',
		titleLine: 'bg-blue-200/60 dark:bg-blue-500/30'
	},
	orange: {
		navActive: 'bg-orange-500 text-white shadow-lg shadow-orange-500/30 ring-1 ring-orange-400',
		navInactive:
			'hover:text-orange-600 dark:hover:text-orange-400 hover:bg-white dark:hover:bg-orange-900/20 border-gray-100 dark:border-zinc-700',
		headerIcon:
			'bg-orange-50 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 shadow-orange-100 dark:shadow-orange-900/20',
		titleLine: 'bg-orange-200/60 dark:bg-orange-500/30'
	},
	purple: {
		navActive: 'bg-purple-600 text-white shadow-lg shadow-purple-500/30 ring-1 ring-purple-400',
		navInactive:
			'hover:text-purple-600 dark:hover:text-purple-400 hover:bg-white dark:hover:bg-purple-900/20 border-gray-100 dark:border-zinc-700',
		headerIcon:
			'bg-purple-50 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 shadow-purple-100 dark:shadow-purple-900/20',
		titleLine: 'bg-purple-200/60 dark:bg-purple-500/30'
	},
	red: {
		navActive: 'bg-red-600 text-white shadow-lg shadow-red-500/30 ring-1 ring-red-400',
		navInactive:
			'hover:text-red-600 dark:hover:text-red-400 hover:bg-white dark:hover:bg-red-900/20 border-gray-100 dark:border-zinc-700',
		headerIcon:
			'bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 shadow-red-100 dark:shadow-red-900/20',
		titleLine: 'bg-red-200/60 dark:bg-red-500/30'
	},
	rose: {
		navActive: 'bg-rose-600 text-white shadow-lg shadow-rose-500/30 ring-1 ring-rose-400',
		navInactive:
			'hover:text-rose-600 dark:hover:text-rose-400 hover:bg-white dark:hover:bg-rose-900/20 border-gray-100 dark:border-zinc-700',
		headerIcon:
			'bg-rose-50 dark:bg-rose-900/30 text-rose-600 dark:text-rose-400 shadow-rose-100 dark:shadow-rose-900/20',
		titleLine: 'bg-rose-200/60 dark:bg-rose-500/30'
	}
};

export type TheaterTheme = keyof typeof THEATER_THEMES;

export const getThemeStyles = (theme: string) => {
	return THEATER_THEMES[theme as TheaterTheme] || THEATER_THEMES.purple;
};
