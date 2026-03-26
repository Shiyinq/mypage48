export const PLATFORM_LOGOS: Record<string, string> = {
	showroom: 'https://www.showroom-live.com/assets/svg/logo.svg',
	idn: 'https://www.idn.app/_next/static/media/logotype_idn.dadd4d4e.png'
};

export const PLATFORM_COLORS: Record<string, string> = {
	showroom: 'from-blue-600 to-blue-400',
	idn: 'from-red-600 to-red-400'
};

export const PLATFORM_NAMES: Record<string, string> = {
	showroom: 'SR',
	idn: 'IDN'
};

export function getLiveLogoUrl(platform: string): string {
	return PLATFORM_LOGOS[platform.toLowerCase()] || '';
}

export function getPlatformColor(platform: string): string {
	return PLATFORM_COLORS[platform.toLowerCase()] || 'from-gray-600 to-gray-400';
}

export function getPlatformIcon(platform: string): string {
	return PLATFORM_NAMES[platform.toLowerCase()] || platform.toUpperCase();
}
