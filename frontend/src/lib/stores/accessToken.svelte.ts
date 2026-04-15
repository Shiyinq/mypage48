/**
 * Access token store - migrated to Svelte 5 Shared Rune State
 * This is used for global authentication state and API requests.
 */

let token = $state('');

export const accessToken = {
	get value() {
		return token;
	},
	set: (val: string) => {
		token = val;
	},
	// Compatibility for legacy store-like access
	set value(v: string) {
		token = v;
	}
};
