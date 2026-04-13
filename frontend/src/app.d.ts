// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}
	namespace svelteHTML {
		// eslint-disable-next-line @typescript-eslint/no-unused-vars
		interface HTMLAttributes<T> {
			onintersect?: (event: CustomEvent<unknown>) => void;
			'on:intersect'?: (event: CustomEvent<unknown>) => void;
		}
	}
}

export {};
