<script lang="ts">
	import SEO from '$lib/components/SEO.svelte';

	import { onMount } from 'svelte';
	import { sorterNavbarStore } from '$lib/stores/sorterNavbar.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { membersStore } from '$lib/stores/theater.svelte';
	import { sorterApi } from '$lib/apis/sorter';
	import SorterRankDisplay from '$lib/components/sorter/SorterRankDisplay.svelte';
	import SorterEditableHeader from '$lib/components/sorter/SorterEditableHeader.svelte';

	import { Info } from 'lucide-svelte';
	import type { SorterResponse } from '$lib/apis/sorter';
	import { goto } from '$app/navigation';
	import { theaterSorter } from '$lib/stores/sorter.svelte';
	import { showToast } from '$lib/stores';

	let { data }: { data: { id: string; isLocal?: boolean; historyItem?: SorterResponse } } =
		$props();
	let historyItem = $state<SorterResponse | null>(null);

	$effect(() => {
		if (data.isLocal) {
			try {
				const saved = localStorage.getItem('oshi_sorter_history');
				if (saved) {
					const histories: SorterResponse[] = JSON.parse(saved);
					historyItem = histories.find((h) => h._id === data.id) || null;
				}
			} catch (_e) {
				// ignore
			}
		} else {
			historyItem = data.historyItem || null;
		}
	});

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
	let isSaving = $state(false);

	const TITLE_LIMIT = 100;
	const DESCRIPTION_LIMIT = 500;

	function startEditTitle() {
		if (historyItem) {
			tempTitle = historyItem.title;
			isEditingTitle = true;
		}
	}

	function cancelEditTitle() {
		isEditingTitle = false;
	}

	async function saveTitle() {
		if (!historyItem || !tempTitle.trim() || tempTitle.trim() === historyItem.title) {
			isEditingTitle = false;
			return;
		}

		const newTitle = tempTitle.trim().slice(0, TITLE_LIMIT);

		if (data.isLocal) {
			try {
				const saved = localStorage.getItem('oshi_sorter_history');
				if (saved) {
					let histories: SorterResponse[] = JSON.parse(saved);
					const idx = histories.findIndex((h) => h._id === historyItem?._id);
					if (idx !== -1) {
						histories[idx].title = newTitle;
						localStorage.setItem('oshi_sorter_history', JSON.stringify(histories));
						historyItem.title = newTitle;
					}
				}
			} catch (_e) {
				// ignore
			}
			isEditingTitle = false;
			return;
		}

		isSaving = true;
		try {
			const res = await sorterApi.updateSorterHistory(historyItem._id, {
				title: newTitle
			});
			historyItem.title = res.title;
			isEditingTitle = false;
		} catch (e) {
			console.error('Failed to update title', e);
		} finally {
			isSaving = false;
		}
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

	async function saveDescription() {
		if (!historyItem) return;

		const newDesc = tempDescription.trim().slice(0, DESCRIPTION_LIMIT);
		if (newDesc === (historyItem.description || '')) {
			isEditingDescription = false;
			return;
		}

		if (data.isLocal) {
			try {
				const saved = localStorage.getItem('oshi_sorter_history');
				if (saved) {
					let histories: SorterResponse[] = JSON.parse(saved);
					const idx = histories.findIndex((h) => h._id === historyItem?._id);
					if (idx !== -1) {
						histories[idx].description = newDesc;
						localStorage.setItem('oshi_sorter_history', JSON.stringify(histories));
						historyItem.description = newDesc;
					}
				}
			} catch (_e) {
				// ignore
			}
			isEditingDescription = false;
			return;
		}

		isSaving = true;
		try {
			const res = await sorterApi.updateSorterHistory(historyItem._id, {
				title: historyItem.title,
				description: newDesc || undefined
			});
			historyItem.description = res.description;
			isEditingDescription = false;
		} catch (e) {
			console.error('Failed to update description', e);
		} finally {
			isSaving = false;
		}
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
	});

	function shareResult() {
		// Share logic here
	}

	async function saveToDB() {
		if (!historyItem || isSaving) return;
		isSaving = true;
		try {
			const saved = await sorterApi.saveSorterHistory({
				title: historyItem.title,
				description: historyItem.description,
				filters: historyItem.filters,
				results: historyItem.results
			});
			theaterSorter.deleteSavedHistoryLocal(historyItem._id, true);
			showToast(t('theater.sorter.saveSuccess') || 'Results saved to history!', 'success');
			goto(`/sorter/history/${saved._id}`, { replaceState: true });
		} catch (e) {
			console.error('Failed to save', e);
			showToast(t('theater.sorter.saveFailed') || 'Failed to save results', 'error');
		} finally {
			isSaving = false;
		}
	}

	$effect(() => {
		sorterNavbarStore.update({
			pageType: 'history-detail',
			layoutMode,
			isLocalHistory: data.isLocal,
			onSetLayout: (mode) => (layoutMode = mode),
			onShare: shareResult,
			onSave: data.isLocal ? saveToDB : undefined
		});
		return () => {
			sorterNavbarStore.reset();
		};
	});
</script>

<SEO
	title={`${historyItem?.title || 'History'} | Oshi Sorter`}
	path={`/sorter/history/${historyItem?._id || data.id}`}
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
				{#if data.isLocal}
					<div
						class="mb-6 p-4 rounded-2xl bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-900/30 flex gap-3 items-start"
					>
						<Info class="w-5 h-5 text-amber-600 dark:text-amber-500 shrink-0 mt-0.5" />
						<div class="text-sm font-medium text-amber-800 dark:text-amber-200/80">
							{t('theater.sorter.publicHistoryWarning') ||
								'Riwayat yang tersimpan di sini bersifat lokal pada browser perangkat ini. Kapasitas penyimpanan terbatas dan riwayat ini akan hilang secara permanen jika Anda menghapus data situs atau cache browser.'}
							<span class="font-bold">
								{t('theater.sorter.localHistorySaveInstruction') ||
									'Klik tombol Simpan di atas untuk menyimpannya secara permanen.'}
							</span>
						</div>
					</div>
				{/if}

				<div class="flex flex-col md:flex-row md:items-start justify-between gap-4 w-full">
					<div class="flex flex-col gap-2 w-full min-w-0">
						<SorterEditableHeader
							title={historyItem.title}
							description={historyItem.description || ''}
							{tempTitle}
							{tempDescription}
							{isEditingTitle}
							{isEditingDescription}
							{isSaving}
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

				<SorterRankDisplay results={resolvedResults} {layoutMode} isPublic={false} />
			</div>
		</div>
	{/if}
</div>

<style>
	:global(.shiny-card::after) {
		content: '';
		position: absolute;
		top: -50%;
		left: -50%;
		width: 200%;
		height: 200%;
		background: linear-gradient(
			45deg,
			transparent 20%,
			rgba(255, 255, 255, 0.1) 35%,
			rgba(255, 255, 255, 0.2) 40%,
			rgba(255, 255, 255, 0.1) 45%,
			transparent 60%
		);
		transform: rotate(-45deg);
		animation: shine 6s infinite;
		pointer-events: none;
		z-index: 25;
	}

	@keyframes shine {
		0% {
			transform: translateX(-100%) rotate(-45deg);
		}
		20%,
		100% {
			transform: translateX(100%) rotate(-45deg);
		}
	}
</style>
