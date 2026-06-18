<script lang="ts">
	import type { PageData } from './$types';
	import { goto } from '$app/navigation';
	import SEO from '$lib/components/SEO.svelte';

	import { onMount, onDestroy } from 'svelte';
	import { isImmersive } from '$lib/stores';
	import { ChevronLeft, LayoutGrid, List } from 'lucide-svelte';
	import { fade } from 'svelte/transition';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { membersStore } from '$lib/stores/theater.svelte';
	import { sorterApi } from '$lib/apis/sorter';
	import SorterRankDisplay from '$lib/components/sorter/SorterRankDisplay.svelte';
	import SorterEditableHeader from '$lib/components/sorter/SorterEditableHeader.svelte';

	let { data }: { data: PageData } = $props();
	let historyItem = $derived(data.historyItem);

	$effect(() => {
		historyItem = data.historyItem;
	});

	const { t, locale } = useTranslation();

	function handleBack() {
		goto('/theater/sorter/history');
	}

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
		tempTitle = historyItem.title;
		isEditingTitle = true;
	}

	function cancelEditTitle() {
		isEditingTitle = false;
	}

	async function saveTitle() {
		if (!tempTitle.trim() || tempTitle.trim() === historyItem.title) {
			isEditingTitle = false;
			return;
		}
		isSaving = true;
		try {
			const res = await sorterApi.updateSorterHistory(historyItem._id, {
				title: tempTitle.trim().slice(0, TITLE_LIMIT)
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
		tempDescription = historyItem.description || '';
		isEditingDescription = true;
	}

	function cancelEditDescription() {
		isEditingDescription = false;
	}

	async function saveDescription() {
		const newDesc = tempDescription.trim().slice(0, DESCRIPTION_LIMIT);
		if (newDesc === (historyItem.description || '')) {
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
			member_type: found?.member_type || 'JKT48',
			generation: found?.generation || ''
		};
	}

	let resolvedResults = $derived(
		historyItem.results.map((item) => ({
			...item,
			...resolveMember(item.id, item.name)
		}))
	);

	onMount(() => {
		if (membersStore.list.length === 0) {
			membersStore.load({ limit: 100 });
		}
		isImmersive.set(true);
		if (typeof window !== 'undefined') {
			document.body.style.overflow = 'hidden';
		}
	});

	onDestroy(() => {
		isImmersive.set(false);
		if (typeof window !== 'undefined') {
			document.body.style.overflow = '';
		}
	});
</script>

<SEO
	title={`${historyItem.title} - Oshi Sorter`}
	path={`/theater/sorter/history/${historyItem._id}`}
	description={historyItem.description || 'Hasil Oshi Sorter'}
/>

<div
	class="fixed inset-0 bg-gradient-to-b from-pink-50/50 via-white to-white dark:from-zinc-950 dark:via-zinc-950 dark:to-zinc-900 flex flex-col overflow-hidden z-[40]"
	in:fade
>
	<!-- Top Navbar -->
	<div
		class="absolute top-0 left-0 right-0 h-16 border-b border-black/5 dark:border-white/5 bg-white/60 dark:bg-zinc-950/60 backdrop-blur-xl flex items-center justify-between px-4 z-50 shrink-0"
	>
		<div class="flex items-center gap-4">
			<button
				onclick={handleBack}
				class="flex items-center gap-2 text-slate-900 dark:text-white hover:text-red-600 dark:hover:text-red-400 transition-colors bg-transparent border-none p-0 cursor-pointer font-bold"
			>
				<ChevronLeft size={20} />
				<span class="font-extrabold tracking-tight text-sm uppercase"
					>{t('theater.sorter.backToHistory')}</span
				>
			</button>
		</div>

		<!-- Layout controllers -->
		<div class="flex items-center gap-2 sm:gap-3">
			<div
				class="flex bg-gray-50/50 dark:bg-zinc-800/30 backdrop-blur-md rounded-full p-1 border border-zinc-200 dark:border-zinc-800 shadow-inner"
			>
				<button
					onclick={() => (layoutMode = 'card')}
					class={`p-1.5 rounded-full transition-all cursor-pointer ${layoutMode === 'card' ? 'bg-rose-500 text-white shadow-lg shadow-rose-500/20' : 'text-slate-400 hover:text-slate-900 dark:hover:text-white'}`}
					title={t('theater.sorter.gridView')}
				>
					<LayoutGrid size={16} />
				</button>
				<button
					onclick={() => (layoutMode = 'list')}
					class={`p-1.5 rounded-full transition-all cursor-pointer ${layoutMode === 'list' ? 'bg-rose-500 text-white shadow-lg shadow-rose-500/20' : 'text-slate-400 hover:text-slate-900 dark:hover:text-white'}`}
					title={t('theater.sorter.listView')}
				>
					<List size={16} />
				</button>
			</div>
		</div>
	</div>

	<!-- Scrollable Content -->
	<div class="flex-1 overflow-y-auto px-4 pt-20 sm:pt-24 pb-8 sm:pb-8 flex flex-col items-center">
		<div
			class={`w-full space-y-8 px-1.5 sm:px-4 mx-auto pb-24 ${layoutMode === 'list' ? 'max-w-3xl' : 'max-w-6xl'}`}
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
