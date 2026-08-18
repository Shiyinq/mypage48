import type { Member } from '$lib/apis/members';
import { membersStore } from '$lib/stores/theater.svelte';
import { showToast } from '$lib/stores';
import { sorterApi, type SorterResponse } from '$lib/apis/sorter';
import { goto } from '$app/navigation';
import { t as translate } from '$lib/i18n';
import { getExternalMediaUrl } from '$lib/utils/media';
/**
 * Calculates the total number of element moves in the sorter's merge sort implementation.
 */
export function calculateTotalMoves(n: number): number {
	if (n <= 1) return 0;
	let moves = 0;
	let currentLists = Array(n).fill(1);
	while (currentLists.length > 1) {
		const nextLists: number[] = [];
		for (let i = 0; i < currentLists.length; i += 2) {
			if (i + 1 < currentLists.length) {
				const mergedSize = currentLists[i] + currentLists[i + 1];
				moves += mergedSize;
				nextLists.push(mergedSize);
			} else {
				nextLists.push(currentLists[i]);
			}
		}
		currentLists = nextLists;
	}
	return moves;
}

export type SorterState = 'landing' | 'sorting' | 'results' | 'history';

export interface ResultMember extends Member {
	rank: number;
}

export interface SorterHistoryState {
	lstMember: number[][];
	rec: number[];
	cmp1: number;
	cmp2: number;
	head1: number;
	head2: number;
	nrec: number;
	numQuestion: number;
	finishSize: number;
	finishFlag: number;
}

const LOCAL_PROGRESS_KEY = 'oshi_sorter_progress';
const LOCAL_HISTORY_KEY = 'oshi_sorter_history';

export function createSorter(
	t: (key: string, params?: Record<string, string | number>) => string,
	path: string,
	mode: 'public' | 'theater' = 'public'
) {
	// State
	let currentState = $state<SorterState>('landing');
	let allMembers = $state<Member[]>([]);
	let selectedMembers = $state<Member[]>([]);
	let generations = $state<string[]>([]);
	let selectedGenerations = $state<Set<string>>(new Set());
	let loadingGenerations = $state(true);

	// Sorting Logic State
	let lstMember = $state<number[][]>([]);
	let rec = $state<number[]>([]);
	let cmp1 = $state(0);
	let cmp2 = $state(0);
	let head1 = $state(0);
	let head2 = $state(0);
	let nrec = $state(0);
	let numQuestion = $state(0);
	let finishSize = $state(0);
	let finishFlag = $state(0);
	let totalMoves = $state(0);
	let history = $state<SorterHistoryState[]>([]);
	let results = $state<ResultMember[]>([]);

	let savedHistories = $state<SorterResponse[]>([]);
	let selectedHistory = $state<SorterResponse | null>(null);
	let loadingHistory = $state(false);
	let historyPage = $state(1);
	let historyHasMore = $state(true);

	let hasSavedProgress = $state(false);

	let resultsTitle = $state(t('theater.sorter.results') || 'HASIL');
	let resultsDescription = $state(
		t('theater.sorter.resultsSubtitle') || 'Ini adalah peringkat terbaikmu!'
	);
	let lastSavedLocalHistoryId = $state<string | null>(null);

	// Animation State
	let isAnimating = $state(false);
	let lastSelectedSide = $state<'left' | 'right' | 'tie' | null>(null);

	// Derived
	const leftMember = $derived(selectedMembers[lstMember[cmp1]?.[head1]] || null);
	const rightMember = $derived(selectedMembers[lstMember[cmp2]?.[head2]] || null);

	const progress = $derived(
		finishFlag ? 100 : totalMoves > 0 ? Math.floor((finishSize / totalMoves) * 100) : 0
	);
	const displayProgress = $derived(finishFlag ? 100 : Math.min(progress, 99));

	// Methods
	async function fetchMembers() {
		try {
			await membersStore.load({ limit: 100 }, true);
			allMembers = membersStore.list;
			const gens = await membersStore.getGenerations();
			generations = gens.sort((a, b) => parseInt(a) - parseInt(b));
			selectedGenerations = new Set();

			// Preload medium images for all members as soon as page opens
			for (const m of allMembers) {
				if (m.img_medium) {
					const url = getExternalMediaUrl(m.img_medium);
					if (url) new Image().src = url;
				}
			}
		} catch {
			showToast(t('theater.members.errorTitle') || 'Failed to load members', 'error');
		} finally {
			loadingGenerations = false;
		}

		checkSavedProgress();
	}

	function toggleGeneration(gen: string) {
		const next = new Set(selectedGenerations);
		if (next.has(gen)) {
			next.delete(gen);
		} else {
			next.add(gen);
		}
		selectedGenerations = next;
	}

	function selectAllGenerations() {
		selectedGenerations = new Set(generations);
	}

	function deselectAllGenerations() {
		selectedGenerations = new Set();
	}

	function startSort() {
		selectedMembers = allMembers.filter((m) => selectedGenerations.has(m.generation));
		if (selectedMembers.length < 2) {
			showToast(t('theater.sorter.minSelection'), 'error');
			return;
		}
		selectedMembers = [...selectedMembers].sort(() => Math.random() - 0.5);

		lstMember = selectedMembers.map((_, i) => [i]);
		rec = [];
		nrec = 0;
		numQuestion = 1;
		cmp1 = 0;
		cmp2 = 1;
		head1 = 0;
		head2 = 0;
		finishSize = 0;
		finishFlag = 0;
		totalMoves = calculateTotalMoves(selectedMembers.length);
		history = [];
		currentState = 'sorting';
		saveProgressLocal();
	}

	function checkSavedProgress() {
		try {
			const saved = localStorage.getItem(LOCAL_PROGRESS_KEY);
			if (saved) {
				const parsed = JSON.parse(saved);
				if (parsed && !parsed.finishFlag && parsed.lstMember && parsed.lstMember.length > 0) {
					hasSavedProgress = true;
					return;
				}
			}
		} catch (_e) {
			// ignore
		}
		hasSavedProgress = false;
	}

	function saveProgressLocal() {
		try {
			if (finishFlag) {
				clearProgressLocal();
				return;
			}
			const stateToSave = {
				selectedMembers,
				selectedGenerations: Array.from(selectedGenerations),
				lstMember,
				rec,
				cmp1,
				cmp2,
				head1,
				head2,
				nrec,
				numQuestion,
				finishSize,
				finishFlag,
				totalMoves,
				history
			};
			localStorage.setItem(LOCAL_PROGRESS_KEY, JSON.stringify(stateToSave));
			hasSavedProgress = true;
		} catch (_e) {
			// ignore
		}
	}

	function clearProgressLocal() {
		try {
			localStorage.removeItem(LOCAL_PROGRESS_KEY);
			hasSavedProgress = false;
		} catch (_e) {
			// ignore
		}
	}

	function resumeSort() {
		try {
			const saved = localStorage.getItem(LOCAL_PROGRESS_KEY);
			if (saved) {
				const parsed = JSON.parse(saved);
				if (parsed && !parsed.finishFlag) {
					selectedMembers = parsed.selectedMembers;
					selectedGenerations = new Set(parsed.selectedGenerations);
					lstMember = parsed.lstMember;
					rec = parsed.rec;
					cmp1 = parsed.cmp1;
					cmp2 = parsed.cmp2;
					head1 = parsed.head1;
					head2 = parsed.head2;
					nrec = parsed.nrec;
					numQuestion = parsed.numQuestion;
					finishSize = parsed.finishSize;
					finishFlag = parsed.finishFlag;
					totalMoves = parsed.totalMoves;
					history = parsed.history;
					currentState = 'sorting';
					return;
				}
			}
		} catch (_e) {
			// ignore
		}
		showToast('Failed to resume sorter', 'error');
	}

	function saveHistory() {
		history = [
			...history,
			JSON.parse(
				JSON.stringify({
					lstMember,
					rec,
					cmp1,
					cmp2,
					head1,
					head2,
					nrec,
					numQuestion,
					finishSize,
					finishFlag
				})
			)
		];
		if (history.length > 30) history = history.slice(1);
	}

	function undo() {
		if (history.length === 0) return;
		const last = history[history.length - 1];
		history = history.slice(0, -1);
		lstMember = last.lstMember;
		rec = last.rec;
		cmp1 = last.cmp1;
		cmp2 = last.cmp2;
		head1 = last.head1;
		head2 = last.head2;
		nrec = last.nrec;
		numQuestion = last.numQuestion;
		finishSize = last.finishSize;
		finishFlag = last.finishFlag;
		saveProgressLocal();
	}

	function sortList(flag: number) {
		saveHistory();
		if (flag === 1) {
			rec[nrec] = lstMember[cmp1][head1];
			head1++;
			nrec++;
			finishSize++;
		} else if (flag === -1) {
			rec[nrec] = lstMember[cmp2][head2];
			head2++;
			nrec++;
			finishSize++;
		} else {
			rec[nrec] = lstMember[cmp1][head1];
			head1++;
			nrec++;
			finishSize++;
			rec[nrec] = lstMember[cmp2][head2];
			head2++;
			nrec++;
			finishSize++;
		}

		if (head1 < lstMember[cmp1].length && head2 < lstMember[cmp2].length) {
			numQuestion++;
		} else {
			while (head1 < lstMember[cmp1].length) {
				rec[nrec] = lstMember[cmp1][head1];
				head1++;
				nrec++;
				finishSize++;
			}
			while (head2 < lstMember[cmp2].length) {
				rec[nrec] = lstMember[cmp2][head2];
				head2++;
				nrec++;
				finishSize++;
			}
			lstMember.splice(cmp1, 2, [...rec]);
			cmp1 = cmp1 + 1;
			cmp2 = cmp1 + 1;
			head1 = 0;
			head2 = 0;
			rec = [];
			nrec = 0;
			if (cmp1 >= lstMember.length - 1) {
				if (lstMember.length === 1) {
					finishFlag = 1;
					return;
				}
				cmp1 = 0;
				cmp2 = 1;
			}
			numQuestion++;
		}
		saveProgressLocal();
	}

	async function handleSelect(flag: number) {
		if (isAnimating) return;

		lastSelectedSide = flag === 1 ? 'left' : flag === -1 ? 'right' : 'tie';
		isAnimating = true;

		await new Promise((resolve) => setTimeout(resolve, 450));

		sortList(flag);

		if (finishFlag) {
			await new Promise((resolve) => setTimeout(resolve, 800));
			showResults();
		}

		isAnimating = false;
		lastSelectedSide = null;
	}

	function showResults() {
		const finalOrder = lstMember[0];
		results = finalOrder.map((idxVal: number, i: number) => ({
			...selectedMembers[idxVal],
			rank: i + 1
		}));
		currentState = 'results';
		clearProgressLocal();
		saveHistoryLocalAuto();
	}

	function restart() {
		currentState = 'landing';
		history = [];
		resultsTitle = t('theater.sorter.results') || 'HASIL';
		resultsDescription = t('theater.sorter.resultsSubtitle') || 'Ini adalah peringkat terbaikmu!';
		lastSavedLocalHistoryId = null;
	}

	function updateLocalHistoryTitle(title: string, description: string) {
		resultsTitle = title;
		resultsDescription = description;
		if (lastSavedLocalHistoryId) {
			try {
				const saved = localStorage.getItem(LOCAL_HISTORY_KEY);
				if (saved) {
					const histories: SorterResponse[] = JSON.parse(saved);
					const h = histories.find((h) => h._id === lastSavedLocalHistoryId);
					if (h) {
						h.title = title;
						h.description = description;
						localStorage.setItem(LOCAL_HISTORY_KEY, JSON.stringify(histories));
						savedHistories = histories;
					}
				}
			} catch {
				// ignore
			}
		}
	}

	function saveHistoryLocalAuto() {
		try {
			const reqFilters = [...selectedGenerations].sort((a, b) => parseInt(a) - parseInt(b));
			const reqResults = results.map((r) => ({
				id: String(r.id),
				name: r.name,
				rank: r.rank
			}));
			const d = new Date();

			const newHistory: SorterResponse = {
				_id: `local-${d.getTime()}`,
				user_id: 'local',
				title: resultsTitle,
				description: resultsDescription,
				filters: reqFilters,
				results: reqResults,
				created_at: d.toISOString(),
				updated_at: d.toISOString()
			};
			lastSavedLocalHistoryId = newHistory._id;

			const saved = localStorage.getItem(LOCAL_HISTORY_KEY);
			let histories: SorterResponse[] = [];
			if (saved) {
				try {
					histories = JSON.parse(saved);
				} catch {
					histories = [];
				}
			}

			histories.unshift(newHistory);
			if (histories.length > 30) {
				histories = histories.slice(0, 30);
			}

			localStorage.setItem(LOCAL_HISTORY_KEY, JSON.stringify(histories));
		} catch (e) {
			console.error('Failed to auto-save local history', e);
		}
	}

	async function copyToClipboard(text: string): Promise<boolean> {
		try {
			if (navigator.clipboard?.writeText) {
				await navigator.clipboard.writeText(text);
				return true;
			}
		} catch {
			// Fallback
		}
		try {
			const textarea = document.createElement('textarea');
			textarea.value = text;
			textarea.setAttribute('readonly', '');
			textarea.style.position = 'fixed';
			textarea.style.left = '-9999px';
			document.body.appendChild(textarea);
			textarea.select();
			const ok = document.execCommand('copy');
			document.body.removeChild(textarea);
			return ok;
		} catch {
			return false;
		}
	}

	async function shareResults(customTitle?: string, customSubtitle?: string) {
		const textList = results
			.slice(0, 10)
			.map((r) => `#${r.rank} ${r.name}`)
			.join('\n');
		const headerText = customTitle
			? `${customTitle}${customSubtitle ? ` (${customSubtitle})` : ''}:`
			: t('theater.sorter.shareTextHeader');
		const shareText = `${headerText}\n${textList}\n\n${t('theater.sorter.shareTextFooter')} ${window.location.origin}${path}`;
		if (navigator.share) {
			try {
				await navigator.share({
					title: t('theater.sorter.shareTitle'),
					text: shareText,
					url: window.location.href
				});
				return;
			} catch (err) {
				if (err instanceof DOMException && err.name === 'AbortError') return;
			}
		}
		const copied = await copyToClipboard(shareText);
		if (copied) showToast(t('theater.sorter.copySuccess'), 'success');
		else showToast(t('theater.sorter.copyFailed'), 'error');
	}

	async function loadSavedHistories(reset: boolean = false) {
		if (reset) {
			historyPage = 1;
			historyHasMore = true;
			savedHistories = [];
		}
		if (!historyHasMore || loadingHistory) return;

		loadingHistory = true;
		try {
			const res = await sorterApi.getSorterHistories(historyPage, 15);
			let locals: SorterResponse[] = [];

			if (reset) {
				// Only load local histories on the first page
				try {
					const saved = localStorage.getItem(LOCAL_HISTORY_KEY);
					if (saved) locals = JSON.parse(saved);
				} catch {
					// ignore
				}
				savedHistories = [...locals, ...res.data];
			} else {
				savedHistories = [...savedHistories, ...res.data];
			}
			if (res.meta.next_page) {
				historyPage = res.meta.next_page;
				historyHasMore = true;
			} else {
				historyHasMore = false;
			}
		} catch {
			showToast(t('theater.sorter.loadHistoryFailed') || 'Failed to load sorter history', 'error');
		} finally {
			loadingHistory = false;
		}
	}

	function loadSavedHistoriesLocal() {
		try {
			const saved = localStorage.getItem(LOCAL_HISTORY_KEY);
			if (saved) {
				savedHistories = JSON.parse(saved);
			} else {
				savedHistories = [];
			}
		} catch {
			savedHistories = [];
		}
		historyHasMore = false;
	}

	async function saveCurrentResult(title: string, description: string) {
		try {
			const reqFilters = [...selectedGenerations].sort((a, b) => parseInt(a) - parseInt(b));
			const reqResults = results.map((r) => ({
				id: String(r.id),
				name: r.name,
				rank: r.rank
			}));
			const saved = await sorterApi.saveSorterHistory({
				title,
				description,
				filters: reqFilters,
				results: reqResults
			});

			if (lastSavedLocalHistoryId) {
				deleteSavedHistoryLocal(lastSavedLocalHistoryId, true);
				lastSavedLocalHistoryId = null;
			}

			showToast(t('theater.sorter.saveSuccess') || 'Results saved to history!', 'success');
			return saved;
		} catch (err) {
			showToast(t('theater.sorter.saveFailed') || 'Failed to save results', 'error');
			throw err;
		}
	}

	async function deleteSavedHistory(id: string) {
		if (id.startsWith('local-')) {
			deleteSavedHistoryLocal(id);
			return;
		}
		try {
			await sorterApi.deleteSorterHistory(id);
			savedHistories = savedHistories.filter((h) => h._id !== id);
			showToast(t('theater.sorter.deleteSuccess') || 'History entry deleted', 'success');
			if (selectedHistory?._id === id) {
				selectedHistory = null;
				currentState = 'history';
			}
		} catch {
			showToast(t('theater.sorter.deleteFailed') || 'Failed to delete history entry', 'error');
		}
	}

	function deleteSavedHistoryLocal(id: string, silent: boolean = false) {
		try {
			const saved = localStorage.getItem(LOCAL_HISTORY_KEY);
			if (saved) {
				let histories: SorterResponse[] = JSON.parse(saved);
				histories = histories.filter((h) => h._id !== id);
				localStorage.setItem(LOCAL_HISTORY_KEY, JSON.stringify(histories));
				savedHistories = histories;
				if (!silent)
					showToast(t('theater.sorter.deleteSuccess') || 'History entry deleted', 'success');
				if (selectedHistory?._id === id) {
					selectedHistory = null;
					currentState = 'history';
				}
			}
		} catch {
			if (!silent)
				showToast(t('theater.sorter.deleteFailed') || 'Failed to delete history entry', 'error');
		}
	}

	function viewHistoryDetail(historyItem: SorterResponse) {
		selectedHistory = historyItem;
		if (mode === 'public') {
			goto(`/jkt48/sorter/history/${historyItem._id}`);
		} else {
			goto(`/sorter/history/${historyItem._id}`);
		}
	}

	function goToHistory() {
		currentState = 'history';
		if (mode === 'public') {
			loadSavedHistoriesLocal();
		} else {
			loadSavedHistories();
		}
	}

	return {
		get currentState() {
			return currentState;
		},
		set currentState(val: SorterState) {
			currentState = val;
		},
		get allMembers() {
			return allMembers;
		},
		get selectedMembers() {
			return selectedMembers;
		},
		get generations() {
			return generations;
		},
		get selectedGenerations() {
			return selectedGenerations;
		},
		get loadingGenerations() {
			return loadingGenerations;
		},
		get numQuestion() {
			return numQuestion;
		},
		get finishSize() {
			return finishSize;
		},
		get finishFlag() {
			return finishFlag;
		},
		get displayProgress() {
			return displayProgress;
		},
		get results() {
			return results;
		},
		get leftMember() {
			return leftMember;
		},
		get rightMember() {
			return rightMember;
		},
		get isAnimating() {
			return isAnimating;
		},
		get lastSelectedSide() {
			return lastSelectedSide;
		},
		get history() {
			return history;
		},

		get savedHistories() {
			return savedHistories;
		},
		get historyHasMore() {
			return historyHasMore;
		},
		get selectedHistory() {
			return selectedHistory;
		},
		set selectedHistory(val: SorterResponse | null) {
			selectedHistory = val;
		},
		get loadingHistory() {
			return loadingHistory;
		},
		get hasSavedProgress() {
			return hasSavedProgress;
		},
		get mode() {
			return mode;
		},
		get resultsTitle() {
			return resultsTitle;
		},
		get resultsDescription() {
			return resultsDescription;
		},

		fetchMembers,
		toggleGeneration,
		selectAllGenerations,
		deselectAllGenerations,
		startSort,
		handleSelect,
		undo,
		restart,
		shareResults,
		loadSavedHistories,
		saveCurrentResult,
		deleteSavedHistory,
		deleteSavedHistoryLocal,
		viewHistoryDetail,
		goToHistory,
		resumeSort,
		loadSavedHistoriesLocal,
		updateLocalHistoryTitle
	};
}

export const publicSorter = createSorter(translate, '/jkt48/sorter', 'public');
export const theaterSorter = createSorter(translate, '/sorter', 'theater');
