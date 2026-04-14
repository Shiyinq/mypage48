<script lang="ts">
	import { Search, X, Check } from 'lucide-svelte';
	import { logger } from '$lib/utils/logger';
	import Button from '$lib/components/Button.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { members as membersApi, type Member } from '$lib/apis/members';
	import { fade, scale } from 'svelte/transition';
	import { tick } from 'svelte';
	import { getExternalMediaUrl } from '$lib/utils/media';

	interface Props {
		show?: boolean;
		// members prop removed, we fetch internally
		saving?: boolean;
		onClose: () => void;
		onSave: (member: Member) => void;
	}

	let { show = false, saving = false, onClose, onSave }: Props = $props();

	const { t } = useTranslation();

	let searchQuery = $state('');
	let selectedOshiId: string | number | null = $state(null);

	let memberList: Member[] = $state([]);
	let loading = $state(false);
	let page = 1;
	let hasMore = true;
	let isAppending = $state(false);
	let searchTimeout: ReturnType<typeof setTimeout>;

	let observer: IntersectionObserver | undefined = $state();
	let sentinel: HTMLElement | undefined = $state();

	function handleVisibilityChange(isVisible: boolean) {
		if (isVisible) {
			if (memberList.length === 0) {
				fetchMembers(true);
			}
		} else {
			searchQuery = '';
			selectedOshiId = null;
			memberList = [];
		}
	}

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
		if (selectedOshiId) {
			const member = memberList.find((m) => m.id === selectedOshiId);
			if (member) onSave(member);
		}
	}
	// Reset/Fetch when modal opens
	$effect(() => {
		handleVisibilityChange(show);
	});
	$effect(() => {
		if (sentinel && observer) {
			observer.observe(sentinel);
		}
	});
</script>

{#if show}
	<div class="fixed inset-0 z-[100] flex items-center justify-center p-4">
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
				class="p-6 border-b border-gray-100 dark:border-zinc-800 flex justify-between items-center bg-white dark:bg-zinc-900 z-10"
			>
				<div>
					<h3 class="text-xl font-black text-gray-800 dark:text-white">
						{$t('profile.oshiModal.title')}
					</h3>
					<p class="text-sm text-gray-500 dark:text-gray-400">{$t('profile.oshiModal.subtitle')}</p>
				</div>
				<button
					onclick={onClose}
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
						type="text"
						bind:value={searchQuery}
						oninput={handleSearch}
						placeholder={$t('profile.oshiModal.searchPlaceholder')}
						class="w-full pl-10 pr-4 py-2 rounded-xl border border-gray-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-gray-900 dark:text-white focus:outline-none focus:border-red-300 focus:ring-4 focus:ring-red-50 dark:focus:ring-red-900/30 transition-all font-medium text-sm"
					/>
				</div>
			</div>

			<!-- Member Grid -->
			<div class="flex-1 overflow-y-auto p-6 scrollbar-hide">
				{#if loading && memberList.length === 0}
					<div class="flex flex-col items-center justify-center py-12">
						<div
							class="w-10 h-10 border-4 border-red-100 border-t-red-500 rounded-full animate-spin mb-4"
						></div>
						<p class="text-sm text-gray-500">{$t('profile.oshiModal.loading')}</p>
					</div>
				{:else if memberList.length === 0}
					<div class="text-center py-12">
						<Search class="w-12 h-12 text-gray-200 mx-auto mb-3" />
						<p class="text-gray-500">
							{$t('profile.oshiModal.noMembers', { query: searchQuery })}
						</p>
					</div>
				{:else}
					<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
						{#each memberList as member}
							<button
								class="group relative flex flex-col items-center text-center p-3 rounded-2xl transition-all duration-200 border-2 cursor-pointer
								{selectedOshiId === member.id
									? 'border-red-500 bg-red-50/50 dark:bg-red-900/20'
									: 'border-transparent hover:bg-gray-50 dark:hover:bg-zinc-800 hover:border-gray-100 dark:hover:border-zinc-700'}"
								onclick={() => (selectedOshiId = member.id)}
							>
								<div class="relative w-20 h-20 mb-3">
									<img
										src={getExternalMediaUrl(member.img)}
										alt={member.name}
										class="w-full h-full rounded-full object-cover shadow-sm group-hover:shadow-md transition-shadow {selectedOshiId ===
										member.id
											? 'ring-2 ring-red-500 ring-offset-2 dark:ring-offset-zinc-900'
											: ''}"
									/>
									{#if selectedOshiId === member.id}
										<div
											class="absolute -right-1 -top-1 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-white shadow-sm"
											transition:scale={{ duration: 200 }}
										>
											<Check class="w-3.5 h-3.5" />
										</div>
									{/if}
								</div>
								<h4 class="font-bold text-gray-800 dark:text-white text-sm leading-tight mb-1">
									{member.name}
								</h4>
								<span
									class="text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-wide bg-gray-100 dark:bg-zinc-800 px-2 py-0.5 rounded-full group-hover:bg-white dark:group-hover:bg-zinc-700 transition-colors"
									>{$t('profile.oshiModal.generation', { gen: member.generation })}</span
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
				class="p-6 border-t border-gray-100 dark:border-zinc-800 bg-white dark:bg-zinc-900 flex justify-end gap-3 z-10"
			>
				<Button variant="outline" onclick={onClose} class="cursor-pointer"
					>{$t('profile.oshiModal.cancel')}</Button
				>
				<Button
					variant="primary"
					disabled={!selectedOshiId || saving}
					loading={saving}
					onclick={handleSave}
					class="cursor-pointer"
				>
					{$t('profile.oshiModal.save')}
				</Button>
			</div>
		</div>
	</div>
{/if}
