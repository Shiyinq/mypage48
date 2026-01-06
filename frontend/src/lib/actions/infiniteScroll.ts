/**
 * Action to handle infinite scrolling using IntersectionObserver
 * @param node - The HTML element to observe
 * @param options - IntersectionObserver options (rootMargin, threshold, etc.)
 */
export function infiniteScroll(
	node: HTMLElement,
	options: IntersectionObserverInit = { rootMargin: '200px' }
) {
	const handleIntersect = (entries: IntersectionObserverEntry[]) => {
		if (entries[0].isIntersecting) {
			node.dispatchEvent(new CustomEvent('intersect'));
		}
	};

	const observer = new IntersectionObserver(handleIntersect, options);
	observer.observe(node);

	return {
		destroy() {
			if (observer) {
				observer.disconnect();
			}
		}
	};
}
