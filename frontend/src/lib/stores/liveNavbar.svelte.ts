import type { Snippet } from 'svelte';

class LiveNavbarStore {
	rightSnippet = $state<Snippet | undefined>(undefined);
}

export const liveNavbarStore = new LiveNavbarStore();
