<script lang="ts">
	import { createEventDispatcher, tick } from 'svelte';
	import { members, type Member } from '$lib/apis/members';
	import { membersCacheStore } from '$lib/stores/theater';
	import { get } from 'svelte/store';
	import { User, Search, X, Check } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { showToast } from '$lib/stores';

	// Props
	export let value: string = '';
	export let placeholder: string = '';
	export let title: string = '';
	export let subtitle: string = '';

	const { t } = useTranslation();
	const dispatch = createEventDispatcher();

	// Modal State
	let isOpen = false;
	let loading = false;
	let memberList: Member[] = [];
	let searchQuery = '';
	let selectedMember: Member | null = null;

	let page = 1;
	let hasMore = true;
	let isAppending = false;
	let searchTimeout: ReturnType<typeof setTimeout>;

	let observer: IntersectionObserver;
	let sentinel: HTMLElement;

	$: if (isOpen && memberList.length === 0) {
		loadMembers(true);
	}

	$: if (isOpen && sentinel && observer) {
		observer.observe(sentinel);
	}

	function getCacheKey() {
		return JSON.stringify({ generation: null, search: searchQuery || '' });
	}

	async function loadMembers(reset = false) {
		const cacheKey = getCacheKey();

		if (reset) {
			// Check cache first
			const cache = get(membersCacheStore);
			if (cache[cacheKey]) {
				memberList = cache[cacheKey].members;
				const cachedPagination = cache[cacheKey].pagination;
				page = cachedPagination.page;
				hasMore = cachedPagination.hasMore;

				// Optional: Highlight value if present
				if (value) {
					const found = memberList.find((m) => m.name === value);
					if (found) selectedMember = found;
				}

				loading = false;
				await tick();
				initObserver();
				return;
			}

			loading = true;
			page = 1;
			hasMore = true;
		} else {
			if (!hasMore || isAppending) return;
			isAppending = true;
		}

		try {
			const res = await members.getAll({
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

			// If value exists, try to find the member object to highlight
			if (value && reset) {
				const found = memberList.find((m) => m.name === value);
				if (found) selectedMember = found;
			}

			// Update Cache
			membersCacheStore.update((store) => ({
				...store,
				[cacheKey]: {
					members: memberList,
					pagination: { page, hasMore }
				}
			}));

			await tick();
			initObserver();
		} catch (e) {
			console.error(e);
			showToast('Failed to load members', 'error');
		} finally {
			loading = false;
			isAppending = false;
		}
	}

	function initObserver() {
		if (observer) observer.disconnect();
		observer = new IntersectionObserver((entries) => {
			if (entries[0].isIntersecting && hasMore && !loading && !isAppending) {
				loadMembers(false);
			}
		});
		if (sentinel) observer.observe(sentinel);
	}

	function handleSearch() {
		clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			loadMembers(true);
		}, 500);
	}

	function selectMember(member: Member) {
		selectedMember = member;
	}

	function confirmSelection() {
		if (selectedMember) {
			value = selectedMember.name;
			dispatch('select', selectedMember);
			close();
		}
	}

	function close() {
		isOpen = false;
		searchQuery = '';
		memberList = [];
	}
</script>

<div class="relative">
	<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
		<User class="w-4 h-4" />
	</div>
	<input
		type="text"
		readonly
		{value}
		on:click={() => (isOpen = true)}
		on:keydown={(e) => e.key === 'Enter' && (isOpen = true)}
		class="w-full pl-9 pr-10 py-3 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-red-500 outline-none text-sm font-medium text-gray-900 dark:text-gray-100 cursor-pointer"
		{placeholder}
	/>
	<div class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
		<Search class="w-4 h-4" />
	</div>
</div>

{#if isOpen}
	<div class="fixed inset-0 z-[100] flex items-center justify-center p-4">
		<!-- Backdrop -->
		<div
			class="absolute inset-0 bg-black/60 backdrop-blur-sm animate-fade-in"
			on:click={close}
			role="presentation"
		></div>

		<!-- Modal Content -->
		<div
			class="relative w-full max-w-2xl bg-white dark:bg-zinc-900 rounded-3xl shadow-2xl overflow-hidden animate-scale-up flex flex-col max-h-[85vh]"
		>
			<!-- Header -->
			<div
				class="p-6 border-b border-gray-100 dark:border-zinc-800 flex justify-between items-center bg-white dark:bg-zinc-900 z-10"
			>
				<div>
					<h3 class="text-xl font-black text-gray-800 dark:text-white">
						{title || $t('profile.oshiModal.title')}
					</h3>
					<p class="text-sm text-gray-500 dark:text-gray-400">
						{subtitle || $t('profile.oshiModal.subtitle')}
					</p>
				</div>
				<button
					type="button"
					on:click={close}
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
						on:input={handleSearch}
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
								type="button"
								class="group relative flex flex-col items-center text-center p-3 rounded-2xl transition-all duration-200 border-2 cursor-pointer
								{selectedMember?.id === member.id
									? 'border-red-500 bg-red-50/50 dark:bg-red-900/20'
									: 'border-transparent hover:bg-gray-50 dark:hover:bg-zinc-800 hover:border-gray-100 dark:hover:border-zinc-700'}"
								on:click={() => selectMember(member)}
							>
								<div class="relative w-20 h-20 mb-3">
									<img
										src={member.img}
										alt={member.name}
										class="w-full h-full rounded-full object-cover shadow-sm group-hover:shadow-md transition-shadow {selectedMember?.id ===
										member.id
											? 'ring-2 ring-red-500 ring-offset-2 dark:ring-offset-zinc-900'
											: ''}"
									/>
									{#if selectedMember?.id === member.id}
										<div
											class="absolute -right-1 -top-1 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center text-white shadow-sm animate-scale-up"
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
				<button
					type="button"
					on:click={close}
					class="px-4 py-2 rounded-xl text-gray-500 hover:text-gray-700 font-bold text-sm transition-colors cursor-pointer"
				>
					{$t('profile.oshiModal.cancel')}
				</button>
				<button
					type="button"
					disabled={!selectedMember}
					on:click={confirmSelection}
					class="idol-gradient text-white px-6 py-2 rounded-xl font-bold text-sm shadow-lg shadow-red-200 hover:shadow-xl hover:scale-105 transition-all disabled:opacity-50 disabled:scale-100 disabled:shadow-none cursor-pointer"
				>
					Confirm Selection
				</button>
			</div>
		</div>
	</div>
{/if}
