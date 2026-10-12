import { browser } from '$app/environment';

/**
 * Shared `lg` breakpoint.
 *
 * Every PostCard needs to know whether the split media viewer fits, so a single
 * listener is shared instead of one per card.
 */
export const viewportStore = $state<{ isWide: boolean }>({ isWide: false });

if (browser) {
	const query = window.matchMedia('(min-width: 1024px)');
	const update = (matches: boolean) => {
		viewportStore.isWide = matches;
	};
	update(query.matches);
	query.addEventListener('change', (event) => update(event.matches));
}
