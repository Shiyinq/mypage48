import { HTMLAttributes } from 'svelte/elements';

declare global {
	namespace svelteHTML {
		interface HTMLAttributes<T> {
			onintersect?: (event: CustomEvent<any>) => void;
		}
	}
}
