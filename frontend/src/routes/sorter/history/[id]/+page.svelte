<script lang="ts">
	import type { PageData } from './$types';
	import SEO from '$lib/components/SEO.svelte';

	import { onMount } from 'svelte';
	import { sorterNavbarStore } from '$lib/stores/sorterNavbar.svelte';
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

	const { locale } = useTranslation();

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
			img_medium: found?.img_medium || '',
			blurHash: found?.blurHash || '',
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
	});

	function shareResult() {
		// Share logic here
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
	path={`/sorter/history/${historyItem._id}`}
	description={historyItem.description || 'Hasil Oshi Sorter'}
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
