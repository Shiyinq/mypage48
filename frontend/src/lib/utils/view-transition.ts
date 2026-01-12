/**
 * Helper to perform a View Transition with a circular reveal effect from the center of the screen.
 * Falls back to immediate execution if the API is not supported.
 *
 * @param fn The state update function to run within the transition
 */
export function startCircularViewTransition(fn: () => void) {
    if (typeof document === 'undefined' || !document.startViewTransition) {
        fn();
        return;
    }

    const transition = document.startViewTransition(fn);

    transition.ready.then(() => {
        const x = window.innerWidth / 2;
        const y = window.innerHeight / 2;
        const endRadius = Math.hypot(
            Math.max(x, window.innerWidth - x),
            Math.max(y, window.innerHeight - y)
        );

        document.documentElement.animate(
            {
                clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${endRadius}px at ${x}px ${y}px)`]
            },
            {
                duration: 500,
                easing: 'ease-in-out',
                pseudoElement: '::view-transition-new(root)'
            }
        );
    });
}
