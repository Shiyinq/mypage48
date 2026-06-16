import { cubicOut } from 'svelte/easing';

type EasingFunction = (t: number) => number;

/**
 * A safe replacement for Svelte's `crossfade` that guards against NaN/Infinity
 * in scale calculations. The built-in crossfade produces `scale(NaN, NaN)` when
 * elements have zero dimensions during page transitions (DOM teardown/creation).
 */

interface SafeCrossfadeOptions {
	duration?: number;
	delay?: number;
	easing?: EasingFunction;
}

interface TransitionConfig {
	delay?: number;
	duration?: number;
	easing?: EasingFunction;
	css?: (t: number, u: number) => string;
}

export function safeCrossfade(options: SafeCrossfadeOptions = {}) {
	const { duration: defaultDuration = 300, easing: defaultEasing = cubicOut } = options;

	const to_receive = new Map<unknown, { rect: DOMRect }>();
	const to_send = new Map<unknown, { rect: DOMRect }>();

	function doCrossfade(
		from: DOMRect,
		node: Element,
		params: SafeCrossfadeOptions & { key: unknown }
	): TransitionConfig {
		const duration = params.duration ?? defaultDuration;
		const easing = params.easing ?? defaultEasing;

		const to = node.getBoundingClientRect();
		const dx = from.left - to.left;
		const dy = from.top - to.top;

		// Guard: if either rect has zero width/height, skip scale and just fade
		const hasValidDimensions = to.width > 0 && to.height > 0 && from.width > 0 && from.height > 0;

		const dw = hasValidDimensions ? from.width / to.width : 1;
		const dh = hasValidDimensions ? from.height / to.height : 1;

		const style = getComputedStyle(node);
		const transform = style.transform === 'none' ? '' : style.transform;
		const opacity = +style.opacity;

		return {
			delay: params.delay ?? 0,
			duration,
			easing,
			css: (t: number, u: number) => {
				const scaleX = t + (1 - t) * dw;
				const scaleY = t + (1 - t) * dh;
				// Final guard: if scale is not finite, fall back to 1
				const safeScaleX = Number.isFinite(scaleX) ? scaleX : 1;
				const safeScaleY = Number.isFinite(scaleY) ? scaleY : 1;

				return (
					`opacity: ${t * opacity};` +
					`transform-origin: top left;` +
					`transform: ${transform} translate(${u * dx}px,${u * dy}px) scale(${safeScaleX}, ${safeScaleY});`
				);
			}
		};
	}

	function fadeFallback(node: Element): TransitionConfig {
		const style = getComputedStyle(node);
		const opacity = +style.opacity;
		return {
			duration: defaultDuration,
			easing: defaultEasing,
			css: (t: number) => `opacity: ${t * opacity}`
		};
	}

	function transition(
		items: Map<unknown, { rect: DOMRect }>,
		counterparts: Map<unknown, { rect: DOMRect }>
	) {
		return (node: Element, params: { key: unknown } & SafeCrossfadeOptions) => {
			items.set(params.key, { rect: node.getBoundingClientRect() });

			return () => {
				if (counterparts.has(params.key)) {
					const { rect } = counterparts.get(params.key)!;
					counterparts.delete(params.key);
					return doCrossfade(rect, node, params);
				}

				items.delete(params.key);
				return fadeFallback(node);
			};
		};
	}

	return [transition(to_send, to_receive), transition(to_receive, to_send)] as const;
}
