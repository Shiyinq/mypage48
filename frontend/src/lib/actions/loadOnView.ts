export interface LoadOnViewOptions {
	/** Called once, the first time the element enters the viewport. */
	onLoad: () => void;
	/** When false, the manual click-to-load stays in charge (no observer runs). */
	enabled?: boolean;
	/** Preload margin, e.g. `200px 0px` to start loading just before it scrolls in. */
	rootMargin?: string;
	/** Fraction of the element that must be visible to trigger the load. */
	threshold?: number;
}

/**
 * Svelte action that calls `onLoad` once, when the element first scrolls into view.
 * Used to auto-load embeds as they are reached, while the click-to-load path stays
 * in place as a fallback (and for browsers without IntersectionObserver).
 */
export function loadOnView(node: HTMLElement, options: LoadOnViewOptions) {
	let current = options;
	let done = false;
	let observer: IntersectionObserver | null = null;

	const enabled = () => current.enabled !== false;

	const unobserve = () => {
		observer?.disconnect();
		observer = null;
	};

	const observe = () => {
		// No observer support (or disabled): the manual click-to-load stays in charge.
		if (done || observer || !enabled() || typeof IntersectionObserver === 'undefined') return;

		observer = new IntersectionObserver(
			(entries) => {
				if (done || !entries.some((entry) => entry.isIntersecting)) return;
				done = true;
				unobserve();
				current.onLoad();
			},
			{ rootMargin: current.rootMargin ?? '0px', threshold: current.threshold ?? 0 }
		);
		observer.observe(node);
	};

	observe();

	return {
		update(next: LoadOnViewOptions) {
			current = next;
			// Toggling the setting attaches/detaches the observer on the fly.
			if (enabled()) observe();
			else unobserve();
		},
		destroy() {
			unobserve();
		}
	};
}
