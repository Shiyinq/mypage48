import { writable } from 'svelte/store';
import type { ComponentType } from 'svelte';

export interface PageHeaderState {
	title: string;
	subtitle?: string;
	badge?: string;
	loading?: boolean;
	icon?: ComponentType;
	theme?: 'red' | 'blue' | 'green' | 'purple' | 'pink' | 'amber' | 'yellow' | 'orange' | 'rose' | 'indigo';
	showBackButton?: boolean;
	handleBack?: () => void;
	actions?: Array<{
		icon: ComponentType;
		label?: string;
		onClick: () => void;
		theme?: string;
	}>;
}

function createPageHeaderStore() {
	const { subscribe, set, update } = writable<PageHeaderState | null>(null);

	return {
		subscribe,
		set: (state: PageHeaderState | null) => set(state),
		reset: () => set(null)
	};
}

export const pageHeaderStore = createPageHeaderStore();
