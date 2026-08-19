// Simple reactive store for sorter navbar actions data.
// NO Svelte Snippets here — only plain serializable data to avoid Symbol bugs.

type SorterPageState = {
	pageType: 'sorter' | 'history-detail' | 'history-list' | 'none';
	layoutMode: 'card' | 'list';
	sorterState: 'landing' | 'sorting' | 'results';
	numQuestion: number;
	isSaving: boolean;
	savedHistoryId: string | null;
	isLocalHistory?: boolean;
	// callbacks
	onSetLayout?: (mode: 'card' | 'list') => void;
	onSave?: () => void;
	onShare?: () => void;
	onRestart?: () => void;
};

const defaultState: SorterPageState = {
	pageType: 'none',
	layoutMode: 'card',
	sorterState: 'landing',
	numQuestion: 0,
	isSaving: false,
	savedHistoryId: null,
	isLocalHistory: false
};

const state = $state<SorterPageState>({ ...defaultState });

export const sorterNavbarStore = {
	get pageType() {
		return state.pageType;
	},
	get layoutMode() {
		return state.layoutMode;
	},
	get sorterState() {
		return state.sorterState;
	},
	get numQuestion() {
		return state.numQuestion;
	},
	get isSaving() {
		return state.isSaving;
	},
	get savedHistoryId() {
		return state.savedHistoryId;
	},
	get isLocalHistory() {
		return state.isLocalHistory;
	},
	get onSetLayout() {
		return state.onSetLayout;
	},
	get onSave() {
		return state.onSave;
	},
	get onShare() {
		return state.onShare;
	},
	get onRestart() {
		return state.onRestart;
	},
	update(partial: Partial<SorterPageState>) {
		Object.assign(state, partial);
	},
	reset() {
		Object.assign(state, { ...defaultState });
	}
};
