<script lang="ts">
	import { Search, X, Check } from 'lucide-svelte';
	import { logger } from '$lib/utils/logger';
	import Button from '$lib/components/Button.svelte';
	import { untrack } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { members as membersApi, type Member } from '$lib/apis/members';
	import { fade, scale } from 'svelte/transition';
	import { tick } from 'svelte';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import { OptimizedImage } from '$lib/components/common';

	interface Props {
		show?: boolean;
		saving?: boolean;
		currentOshiIds?: (string | number)[];
		maxCount?: number;
		onClose: () => void;
		onSave: (members: Member[]) => void;
	}

	let {
		show = false,
		saving = false,
		currentOshiIds = [],
		maxCount = 5,
		onClose,
		onSave
	}: Props = $props();

	const { t } = useTranslation();

	let searchQuery = $state('');
	let selectedOshiIds: Set<string | number> = $state(new Set());
	let existingSet = $derived(new Set(currentOshiIds));
	let totalSelected = $derived(selectedOshiIds.size);

	let memberList: Member[] = $state([]);
	let loading = $state(false);
	let page = 1;
	let hasMore = true;
	let isAppending = $state(false);
	let searchTimeout: ReturnType<typeof setTimeout>;

	let observer: IntersectionObserver | undefined = $state();
	let sentinel: HTMLElement | undefined = $state();

	function initObserver() {
		if (observer) observer.disconnect();
		observer = new IntersectionObserver((entries) => {
			if (entries[0].isIntersecting && hasMore && !loading && !isAppending) {
				fetchMembers(false);
			}
		});
		if (sentinel) observer.observe(sentinel);
	}

	// membersCacheStore removed
	// import { membersCacheStore } from '$lib/stores/theater.svelte';
	// import { get } from 'svelte/store'; -- removed

	// ... (imports remain)

	async function fetchMembers(reset = false) {
		// cacheKey logic removed as we are not using global cache for modal

		if (reset) {
			loading = true;
			page = 1;
			hasMore = true;
		} else {
			if (!hasMore || isAppending) return;
			isAppending = true;
		}

		try {
			const res = await membersApi.getAll({
				page: reset ? 1 : page + 1,
				limit: 20,
				search: searchQuery || undefined
			});

			if (reset) {
				memberList = res.data.filter((m) => m.active);
				page = 1;
			} else {
				memberList = [...memberList, ...res.data.filter((m) => m.active)];
				page += 1;
			}

			hasMore = !!res.meta.next_page;

			await tick();
			initObserver();
		} catch (e) {
			logger.error('Failed to load members', e, { context: 'OshiSelectionModal' });
		} finally {
			loading = false;
			isAppending = false;
		}
	}

	function handleSearch() {
		clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			fetchMembers(true);
		}, 500);
	}

	function handleSave() {
		if (selectedOshiIds.size > 0) {
			const newMembers: Member[] = [];
			for (const id of selectedOshiIds) {
				if (existingSet.has(id)) continue;
				const member = memberList.find((m) => m.id === id);
				if (member) newMembers.push(member);
			}
			if (newMembers.length > 0) onSave(newMembers);
		}
	}

	function toggleMember(id: string | number) {
		if (existingSet.has(id)) return;
		if (selectedOshiIds.has(id)) {
			selectedOshiIds.delete(id);
			selectedOshiIds = new Set(selectedOshiIds);
		} else if (selectedOshiIds.size < maxCount) {
			selectedOshiIds = new Set([...selectedOshiIds, id]);
		}
	}
	// Reset/Fetch when modal opens
	$effect(() => {
		if (show) {
			untrack(() => {
				selectedOshiIds = new Set(currentOshiIds);
				if (memberList.length === 0) {
					fetchMembers(true);
				}
			});
		} else {
			untrack(() => {
				searchQuery = '';
				selectedOshiIds = new Set();
				memberList = [];
			});
		}
	});
	$effect(() => {
		if (sentinel && observer) {
			observer.observe(sentinel);
		}
	});
</script>

{#if show}
	<div class="fixed inset-0 z-[1000] flex items-center justify-center p-4">
		<!-- Backdrop -->
		<div
			class="absolute inset-0 bg-black/60 backdrop-blur-sm"
			transition:fade={{ duration: 200 }}
			onclick={onClose}
			onkeydown={(e) => e.key === 'Escape' && onClose()}
			role="button"
			tabindex="-1"
			aria-label="Close modal"
		></div>

		<!-- Modal Content -->
		<div
			class="relative w-full max-w-2xl bg-white dark:bg-zinc-900 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[85vh]"
			transition:scale={{ duration: 200, start: 0.95 }}
		>
			<!-- Header -->
			<div
				class="p-4 md:p-6 border-b border-gray-100 dark:border-zinc-800 bg-white dark:bg-zinc-900 z-10"
			>
				<div class="flex items-start justify-between gap-2">
					<div class="min-w-0 flex-1">
						<h3 class="text-lg md:text-xl font-black text-gray-800 dark:text-white truncate">
							{t('profile.oshiModal.title')}
						</h3>
						<p class="text-xs md:text-sm text-gray-500 dark:text-gray-400 leading-tight mt-0.5">
							{t('profile.oshiModal.subtitle')}
						</p>
					</div>
					<div class="flex items-center gap-2 shrink-0">
						<div
							class="px-2.5 py-1 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-[10px] md:text-xs font-bold rounded-full whitespace-nowrap"
						>
							{totalSelected}/{maxCount} Oshi
						</div>
						<button
							onclick={onClose}
							class="p-1.5 md:p-2 rounded-full hover:bg-gray-100 dark:hover:bg-zinc-800 text-gray-500 dark:text-gray-400 transition-colors cursor-pointer"
						>
							<X class="w-4 h-4 md:w-5 md:h-5" />
						</button>
					</div>
				</div>
			</div>

			<!-- Search -->
			<div
				class="px-4 py-3 md:p-4 bg-gray-50 dark:bg-zinc-800/50 border-b border-gray-100 dark:border-zinc-800"
			>
				<div class="relative">
					<Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
					<input
						type="text"
						bind:value={searchQuery}
						oninput={handleSearch}
						placeholder={t('profile.oshiModal.searchPlaceholder')}
						class="w-full pl-10 pr-4 py-2 rounded-xl border border-gray-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-gray-900 dark:text-white focus:outline-none focus:border-red-300 focus:ring-4 focus:ring-red-50 dark:focus:ring-red-900/30 transition-all font-medium text-sm"
					/>
				</div>
			</div>

			<!-- Member Grid -->
			<div class="flex-1 overflow-y-auto px-4 py-4 md:p-6 scrollbar-hide">
				{#if loading && memberList.length === 0}
					<div class="flex flex-col items-center justify-center py-12">
						<div
							class="w-10 h-10 border-4 border-red-100 border-t-red-500 rounded-full animate-spin mb-4"
						></div>
						<p class="text-sm text-gray-500">{t('profile.oshiModal.loading')}</p>
					</div>
				{:else if memberList.length === 0}
					<div class="text-center py-12">
						<Search class="w-12 h-12 text-gray-200 mx-auto mb-3" />
						<p class="text-gray-500">
							{t('profile.oshiModal.noMembers', { query: searchQuery })}
						</p>
					</div>
				{:else}
					{#if currentOshiIds.length >= maxCount}
						<p class="text-xs text-amber-600 dark:text-amber-400 mb-3 text-center font-bold">
							{t('profile.oshiModal.maxReached', { max: maxCount })}
						</p>
					{/if}
					<div class="grid grid-cols-3 sm:grid-cols-3 md:grid-cols-4 gap-2 md:gap-4">
						{#each memberList as member}
							<button
								class="group relative flex flex-col items-center text-center p-2 md:p-3 rounded-2xl transition-all duration-200 border-2 cursor-pointer
								{selectedOshiIds.has(member.id)
									? 'border-red-500 bg-red-50/50 dark:bg-red-900/20'
									: 'border-transparent hover:bg-gray-50 dark:hover:bg-zinc-800 hover:border-gray-100 dark:hover:border-zinc-700'}"
								onclick={() => toggleMember(member.id)}
							>
								<div class="relative w-14 h-14 md:w-20 md:h-20 mb-2 md:mb-3">
									<OptimizedImage
										src={getExternalMediaUrl(member.img)}
										srcMedium={getExternalMediaUrl(member.img_medium)}
										srcSmall={getExternalMediaUrl(member.img_small)}
										blurHash={member.blurHash}
										alt={member.name}
										class="w-full h-full rounded-full object-cover shadow-sm group-hover:shadow-md transition-shadow {selectedOshiIds.has(
											member.id
										)
											? 'ring-2 ring-red-500 ring-offset-2 dark:ring-offset-zinc-900'
											: ''}"
										sizes="56px 80px"
									/>
									{#if selectedOshiIds.has(member.id)}
										<div
											class="absolute -right-0.5 -top-0.5 w-5 h-5 md:w-6 md:h-6 bg-red-500 rounded-full flex items-center justify-center text-white shadow-sm"
											transition:scale={{ duration: 200 }}
										>
											<Check class="w-3 h-3 md:w-3.5 md:h-3.5" />
										</div>
									{/if}
								</div>
								<h4
									class="font-bold text-gray-800 dark:text-white text-[11px] md:text-sm leading-tight mb-0.5 md:mb-1 truncate w-full"
								>
									{member.name}
								</h4>
								<span
									class="text-[9px] md:text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-wide bg-gray-100 dark:bg-zinc-800 px-1.5 md:px-2 py-0.5 rounded-full group-hover:bg-white dark:group-hover:bg-zinc-700 transition-colors"
									>{t('profile.oshiModal.generation', { gen: member.generation })}</span
								>
							</button>
						{/each}
					</div>

					<!-- Sentinel for Infinite Scroll -->
					<div bind:this={sentinel} class="h-8 w-full flex justify-center items-center py-2">
						{#if isAppending}
							<div class="animate-spin rounded-full h-6 w-6 border-b-2 border-red-500"></div>
						{/if}
					</div>
				{/if}
			</div>

			<!-- Footer Action -->
			<div
				class="p-4 md:p-6 border-t border-gray-100 dark:border-zinc-800 bg-white dark:bg-zinc-900 flex flex-col md:flex-row items-center gap-2 md:gap-3 z-10"
			>
				<p class="text-xs text-gray-400 text-center md:self-center md:flex-1 md:text-left">
					{#if selectedOshiIds.size > 0}
						{t('profile.oshiModal.newSelected', {
							count: selectedOshiIds.size - currentOshiIds.length
						})}
					{/if}
				</p>
				<div class="flex gap-2 w-full md:w-auto">
					<Button variant="outline" onclick={onClose} class="cursor-pointer flex-1 md:flex-none"
						>{t('profile.oshiModal.cancel')}</Button
					>
					<Button
						variant="primary"
						disabled={selectedOshiIds.size <= currentOshiIds.length || saving}
						loading={saving}
						onclick={handleSave}
						class="cursor-pointer flex-1 md:flex-none"
					>
						{t('profile.oshiModal.save')}
					</Button>
				</div>
			</div>
		</div>
	</div>
{/if}
