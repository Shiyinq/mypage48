<script lang="ts">
	import SEO from '$lib/components/SEO.svelte';

	import { onMount } from 'svelte';
	import { sorterNavbarStore } from '$lib/stores/sorterNavbar.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { membersStore } from '$lib/stores/theater.svelte';
	import { publicSorter } from '$lib/stores/sorter.svelte';
	import type { SorterResponse } from '$lib/apis/sorter';
	import SorterRankDisplay from '$lib/components/sorter/SorterRankDisplay.svelte';
	import SorterEditableHeader from '$lib/components/sorter/SorterEditableHeader.svelte';

	let { data }: { data: { id: string } } = $props();

	const sorter = publicSorter;
	let historyItem = $state<SorterResponse | null>(null);

	const { locale, t } = useTranslation();

	function parseUTCDate(dateStr: string) {
		const timePart = dateStr.split('T')[1] || '';
		if (!dateStr.endsWith('Z') && !timePart.includes('+') && !timePart.includes('-')) {
			return new Date(dateStr + 'Z');
		}
		return new Date(dateStr);
	}

	function formatDateTime(dateStr: string) {
		try {
			const d = parseUTCDate(dateStr);
			const localeMap: Record<string, string> = {
				id: 'id-ID',
				en: 'en-US',
				ja: 'ja-JP'
			};
			return d.toLocaleString(localeMap[locale.value] || 'id-ID', {
				dateStyle: 'medium',
				timeStyle: 'short'
			});
		} catch {
			return dateStr;
		}
	}

	let layoutMode = $state<'card' | 'list'>('card');

	let isEditingTitle = $state(false);
	let isEditingDescription = $state(false);
	let tempTitle = $state('');
	let tempDescription = $state('');

	const TITLE_LIMIT = 50;
	const DESCRIPTION_LIMIT = 100;

	function startEditTitle() {
		if (historyItem) {
			tempTitle = historyItem.title;
			isEditingTitle = true;
		}
	}

	function cancelEditTitle() {
		isEditingTitle = false;
	}

	function saveTitle() {
		if (historyItem && tempTitle.trim() && tempTitle.trim() !== historyItem.title) {
			const newTitle = tempTitle.trim().slice(0, TITLE_LIMIT);

			const saved = localStorage.getItem('oshi_sorter_history');
			if (saved) {
				try {
					let histories: SorterResponse[] = JSON.parse(saved);
					const h = histories.find((h) => h._id === historyItem!._id);
					if (h) {
						h.title = newTitle;
						localStorage.setItem('oshi_sorter_history', JSON.stringify(histories));
						historyItem.title = newTitle;
					}
				} catch (_e) {
					// ignore
				}
			}
		}
		isEditingTitle = false;
	}

	function startEditDescription() {
		if (historyItem) {
			tempDescription = historyItem.description || '';
			isEditingDescription = true;
		}
	}

	function cancelEditDescription() {
		isEditingDescription = false;
	}

	function saveDescription() {
		if (historyItem) {
			const newDesc = tempDescription.trim().slice(0, DESCRIPTION_LIMIT);
			if (newDesc !== (historyItem.description || '')) {
				const saved = localStorage.getItem('oshi_sorter_history');
				if (saved) {
					try {
						let histories: SorterResponse[] = JSON.parse(saved);
						const h = histories.find((h) => h._id === historyItem!._id);
						if (h) {
							h.description = newDesc;
							localStorage.setItem('oshi_sorter_history', JSON.stringify(histories));
							historyItem.description = newDesc;
						}
					} catch (_e) {
						// ignore
					}
				}
			}
		}
		isEditingDescription = false;
	}

	function resolveMember(id: string, name: string) {
		const found = membersStore.list.find((m) => String(m.id) === String(id));
		return {
			id,
			name: found?.name || name,
			nickname: found?.nickname || name,
			img: found?.img || '',
			img_medium: found?.img_medium || '',
			blurHash: found?.blurHash || '',
			member_type: found?.member_type || 'JKT48',
			generation: found?.generation || ''
		};
	}

	let resolvedResults = $derived(
		historyItem
			? historyItem.results.map((item) => ({
					...item,
					...resolveMember(item.id, item.name)
				}))
			: []
	);

	onMount(() => {
		if (membersStore.list.length === 0) {
			membersStore.load({ limit: 100 });
		}

		sorter.loadSavedHistoriesLocal();
		const found = sorter.savedHistories.find((h) => h._id === data.id);
		if (found) {
			historyItem = found;
		} else {
			// If not found in store (maybe refreshed), load from localStorage directly
			try {
				const saved = localStorage.getItem('oshi_sorter_history');
				if (saved) {
					const histories: SorterResponse[] = JSON.parse(saved);
					historyItem = histories.find((h) => h._id === data.id) || null;
				}
			} catch (_e) {
				// ignore
			}
		}
	});

	function shareResult() {
		if (historyItem) {
			// shareLogic
		}
	}

	$effect(() => {
		sorterNavbarStore.update({
			pageType: 'history-detail',
			layoutMode,
			onSetLayout: (mode) => (layoutMode = mode),
			onShare: shareResult
		});
		return () => {
			sorterNavbarStore.reset();
		};
	});
</script>

<SEO
	title={`${historyItem?.title || 'History'} | Oshi Sorter`}
	path={`/jkt48/sorter/history/${data.id}`}
	description={historyItem?.description || 'Hasil Oshi Sorter'}
/>

<div
	class="w-full flex flex-col items-center justify-start min-h-[calc(100svh-64px)] pt-4 md:pt-8 pb-12"
>
	{#if historyItem}
		<div class="w-full flex flex-col items-center">
			<div
				class={`w-full space-y-8 px-4 sm:px-4 mx-auto pb-24 ${layoutMode === 'list' ? 'max-w-3xl' : 'max-w-6xl'}`}
			>
				<div class="flex flex-col md:flex-row md:items-start justify-between gap-4 w-full">
					<div class="flex flex-col gap-2 w-full min-w-0">
						<SorterEditableHeader
							title={historyItem.title}
							description={historyItem.description || ''}
							{tempTitle}
							{tempDescription}
							{isEditingTitle}
							{isEditingDescription}
							isSaving={false}
							date={formatDateTime(historyItem.created_at)}
							onTitleChange={(v) => (tempTitle = v)}
							onDescriptionChange={(v) => (tempDescription = v)}
							onstartEditTitle={startEditTitle}
							oncancelEditTitle={cancelEditTitle}
							onsaveTitle={saveTitle}
							onstartEditDescription={startEditDescription}
							oncancelEditDescription={cancelEditDescription}
							onsaveDescription={saveDescription}
							titleLimit={TITLE_LIMIT}
							descriptionLimit={DESCRIPTION_LIMIT}
							filters={historyItem.filters}
						/>
					</div>
				</div>

				<SorterRankDisplay results={resolvedResults} {layoutMode} isPublic={true} />
			</div>
		</div>
	{:else}
		<div class="flex items-center justify-center min-h-[50vh]">
			<p class="text-zinc-500 font-semibold">
				{t('theater.sorter.noHistoryTitle') || 'Riwayat tidak ditemukan.'}
			</p>
		</div>
	{/if}
</div>
