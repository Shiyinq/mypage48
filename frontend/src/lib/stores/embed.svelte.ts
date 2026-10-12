import { browser } from '$app/environment';

const STORAGE_KEY = 'mypage48_autoload_embeds';

/**
 * Preference for third-party embeds (YouTube excluded — it keeps its thumbnail).
 * When on, embeds load as soon as they scroll into view; when off, they stay behind
 * the click-to-load gate. Device-local, like the theme.
 */
class EmbedPreferences {
	autoLoad = $state(true);

	constructor() {
		if (browser) {
			const saved = localStorage.getItem(STORAGE_KEY);
			if (saved === 'true' || saved === 'false') this.autoLoad = saved === 'true';
		}
	}

	setAutoLoad(value: boolean) {
		this.autoLoad = value;
		if (browser) localStorage.setItem(STORAGE_KEY, String(value));
	}

	toggle() {
		this.setAutoLoad(!this.autoLoad);
	}
}

export const embedPreferences = new EmbedPreferences();
