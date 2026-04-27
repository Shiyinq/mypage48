/* 
    Svelte 5 Shared Rune State for UI components
    Replaces the legacy writable stores for page headers and immersive mode.
*/

import type { ComponentType } from 'svelte';

export interface PageHeaderState {
	title: string;
	subtitle?: string;
	badge?: string;
	loading?: boolean;
	icon?: ComponentType;
	theme?:
		| 'red'
		| 'blue'
		| 'green'
		| 'purple'
		| 'pink'
		| 'amber'
		| 'yellow'
		| 'orange'
		| 'rose'
		| 'indigo';
	showBackButton?: boolean;
	handleBack?: () => void;
	actions?: Array<{
		icon?: ComponentType;
		label?: string;
		onClick: () => void;
		theme?: string;
		showLabel?: boolean;
		loading?: boolean;
	}>;
}

// Reactive Page Header State
let headerState = $state<PageHeaderState | null>(null);

export const pageHeaderStore = {
	get value() {
		return headerState;
	},
	set: (state: PageHeaderState | null) => {
		headerState = state;
	},
	reset: () => {
		headerState = null;
	},
	subscribe: (cb: (val: PageHeaderState | null) => void) => {
		// Minimum store contract for legacy components if any
		return $effect.root(() => {
			$effect(() => {
				cb(headerState);
			});
		});
	}
};

// Immersive mode state
let immersive = $state(false);

export const isImmersive = {
	get value() {
		return immersive;
	},
	set: (val: boolean) => {
		immersive = val;
	},
	subscribe: (cb: (val: boolean) => void) => {
		return $effect.root(() => {
			$effect(() => {
				cb(immersive);
			});
		});
	}
};
