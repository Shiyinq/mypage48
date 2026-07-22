<script lang="ts">
	import { onMount } from 'svelte';
	import { setlistsStore } from '$lib/stores/theater.svelte';
	import type { SetlistOption } from '$lib/apis/setlists';
	import { Ticket as TicketIcon, Search, X, Check } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { showToast } from '$lib/stores';
	import { logger } from '$lib/utils/logger';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import { OptimizedImage } from '$lib/components/common';
	import { portal } from '$lib/actions/portal';

	interface Props {
		// Props
		value?: string;
		placeholder?: string;
		title?: string;
		subtitle?: string;
		id?: string;
		name?: string;

		// Events
		onselect?: (option: SetlistOption) => void;
	}

	let { value = $bindable(''), placeholder, title, subtitle, id, name, onselect }: Props = $props();

	const { t } = useTranslation();

	// Modal State
	let isOpen = $state(false);
	let loading = $state(true);
	let allOptions: SetlistOption[] = $state([]);
	let filteredOptions: SetlistOption[] = $state([]);
	let searchQuery = $state('');
	let selectedOption: SetlistOption | null = $state(null);

	async function loadOptions() {
		loading = true;
		try {
			const res = await setlistsStore.loadOptions();
			if (res) {
				allOptions = res;

				// If value exists, try to find the setlist object to highlight
				if (value) {
					const found = allOptions.find((s) => s.title === value);
					if (found) selectedOption = found;
				}
				filterOptions();
			}
		} catch (e) {
			logger.error('Failed to load setlist options', e, { context: 'SetlistSelector' });
			showToast('Failed to load setlist options', 'error');
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		loadOptions();
	});

	function filterOptions() {
		if (!searchQuery) {
			filteredOptions = allOptions;
		} else {
			const q = searchQuery.toLowerCase();
			filteredOptions = allOptions.filter(
				(s) => s.title.toLowerCase().includes(q) || s.type.toLowerCase().includes(q)
			);
		}
	}

	function handleSearch() {
		filterOptions();
	}

	function selectOption(option: SetlistOption) {
		selectedOption = option;
	}

	function confirmSelection() {
		if (selectedOption) {
			value = selectedOption.title;
			onselect?.(selectedOption);
			close();
		}
	}

	function close() {
		isOpen = false;
		searchQuery = '';
		filterOptions();
	}

	$effect(() => {
		if (isOpen && allOptions.length === 0) {
			loadOptions();
		}
	});
</script>

<div class="relative">
	<div class="absolute left-3 top-1/2 -translate-y-1/2 text-red-400">
		<TicketIcon class="w-5 h-5" />
	</div>
	<input
		{id}
		{name}
		type="text"
		readonly
		{value}
		onclick={() => (isOpen = true)}
		onkeydown={(e) => e.key === 'Enter' && (isOpen = true)}
		class="w-full pl-10 pr-10 py-3 bg-gray-50 dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-red-500 outline-none text-sm font-bold text-gray-900 dark:text-gray-100 cursor-pointer"
		{placeholder}
	/>
	<div class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
		<Search class="w-4 h-4" />
	</div>
</div>

{#if isOpen}
	<div use:portal class="fixed inset-0 z-[2000] flex items-center justify-center p-4">
		<!-- Backdrop -->
		<div
			class="absolute inset-0 bg-black/75 animate-fade-in"
			onclick={close}
			role="presentation"
		></div>

		<!-- Modal Content -->
		<div
			class="relative w-full max-w-2xl bg-white dark:bg-zinc-900 rounded-3xl shadow-2xl overflow-hidden animate-fade-in flex flex-col max-h-[85vh]"
		>
			<!-- Header -->
			<div
				class="p-6 border-b border-gray-100 dark:border-zinc-800 flex justify-between items-center bg-white dark:bg-zinc-900 z-10"
			>
				<div>
					<h3 class="text-xl font-black text-gray-800 dark:text-white">
						{title || t('forms.selectSetlist')}
					</h3>
					<p class="text-sm text-gray-500 dark:text-gray-400">
						{subtitle || t('forms.showTitleDescription')}
					</p>
				</div>
				<button
					type="button"
					onclick={close}
					class="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-zinc-800 text-gray-500 dark:text-gray-400 transition-colors cursor-pointer"
				>
					<X class="w-5 h-5" />
				</button>
			</div>

			<!-- Search -->
			<div class="p-4 bg-gray-50 dark:bg-zinc-800/50 border-b border-gray-100 dark:border-zinc-800">
				<div class="relative">
					<Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
					<input
						id="setlist-search"
						name="setlist-search"
						type="text"
						bind:value={searchQuery}
						oninput={handleSearch}
						placeholder={t('forms.searchSetlist')}
						class="w-full pl-10 pr-4 py-2 rounded-xl border border-gray-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-gray-900 dark:text-white focus:outline-none focus:border-red-300 focus:ring-4 focus:ring-red-50 dark:focus:ring-red-900/30 transition-all font-medium text-sm"
					/>
				</div>
			</div>

			<!-- Setlist Grid -->
			<div class="flex-1 overflow-y-auto p-6 scrollbar-hide overscroll-contain">
				{#if loading && allOptions.length === 0}
					<div class="flex flex-col items-center justify-center py-12">
						<div
							class="w-10 h-10 border-4 border-red-100 border-t-red-500 rounded-full animate-spin mb-4"
						></div>
					</div>
				{:else if filteredOptions.length === 0}
					<div class="text-center py-12">
						<Search class="w-12 h-12 text-gray-200 mx-auto mb-3" />
						<p class="text-gray-500">
							{t('forms.noSetlistsFound')}
						</p>
					</div>
				{:else}
					<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2 md:gap-4">
						{#each filteredOptions as option (option.setlistId)}
							<button
								type="button"
								class="group relative flex flex-col items-center text-center p-2 md:p-3 rounded-2xl transition-all duration-200 border-2 cursor-pointer
								{selectedOption?.setlistId === option.setlistId
									? 'border-red-500 bg-red-50/50 dark:bg-red-900/20'
									: 'border-transparent hover:bg-gray-50 dark:hover:bg-zinc-800 hover:border-gray-100 dark:hover:border-zinc-700'}"
								onclick={() => selectOption(option)}
							>
								<div class="relative w-full aspect-[3/4] mb-2 md:mb-3 rounded-xl overflow-hidden">
									<OptimizedImage
										src={getExternalMediaUrl(option.imageUrl)}
										srcMedium={getExternalMediaUrl(option.imageUrl_medium)}
										srcSmall={getExternalMediaUrl(option.imageUrl_small)}
										blurHash={option.blurHash}
										alt={option.title}
										class="w-full h-full object-cover shadow-sm group-hover:shadow-md transition-transform duration-300 group-hover:scale-105"
										sizes="(max-width: 768px) 50vw, (max-width: 1200px) 33vw, 25vw"
									/>

									{#if selectedOption?.setlistId === option.setlistId}
										<div
											class="absolute right-1 top-1 w-5 h-5 md:w-6 md:h-6 bg-red-500 rounded-full flex items-center justify-center text-white shadow-sm animate-scale-up z-10"
										>
											<Check class="w-3 h-3 md:w-3.5 md:h-3.5" />
										</div>
									{/if}
								</div>
								<h4
									class="font-bold text-gray-800 dark:text-white text-[11px] md:text-sm leading-tight mb-0.5 md:mb-1 w-full line-clamp-2"
								>
									{option.title}
								</h4>
								<span
									class="text-[9px] md:text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-wide bg-gray-100 dark:bg-zinc-800 px-1.5 md:px-2 py-0.5 rounded-full group-hover:bg-white dark:group-hover:bg-zinc-700 transition-colors mt-auto"
									>{option.type}</span
								>
							</button>
						{/each}
					</div>
				{/if}
			</div>

			<!-- Footer Action -->
			<div
				class="p-6 border-t border-gray-100 dark:border-zinc-800 bg-white dark:bg-zinc-900 flex justify-end gap-3 z-10"
			>
				<button
					type="button"
					onclick={close}
					class="px-4 py-2 rounded-xl text-gray-500 hover:text-gray-700 font-bold text-sm transition-colors cursor-pointer"
				>
					{t('common.cancel')}
				</button>
				<button
					type="button"
					disabled={!selectedOption}
					onclick={confirmSelection}
					class="idol-gradient text-white px-6 py-2 rounded-xl font-bold text-sm shadow-lg shadow-red-200 hover:shadow-xl hover:scale-105 transition-all disabled:opacity-50 disabled:scale-100 disabled:shadow-none cursor-pointer"
				>
					{t('common.confirmSelection')}
				</button>
			</div>
		</div>
	</div>
{/if}
