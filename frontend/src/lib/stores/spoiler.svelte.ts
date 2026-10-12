/**
 * Which spoiler posts the reader has opened, per session.
 *
 * In memory on purpose: a spoiler is covered again on the next visit, exactly
 * like other apps. A plain object (not a Set) so Svelte can track keys.
 */
const revealed = $state<Record<string, boolean>>({});

export const spoilerStore = {
	isRevealed(postId: string): boolean {
		return revealed[postId] === true;
	},
	reveal(postId: string) {
		revealed[postId] = true;
	}
};
