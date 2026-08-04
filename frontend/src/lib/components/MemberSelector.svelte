<script lang="ts">
	import { tick } from 'svelte';
	import { type Member } from '$lib/apis/members';
	import { selectorMembersStore } from '$lib/stores/theater.svelte';
	import { User, Search, X, Check } from 'lucide-svelte';
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
		onselect?: (member: Member) => void;
	}

	let {
		value = $bindable(''),
		placeholder = '',
		title = '',
		subtitle = '',
		id = '',
		name = '',
		onselect
	}: Props = $props();

	const { t } = useTranslation();

	// Modal State
	let isOpen = $state(false);
	let loading = $state(false);
	let memberList: Member[] = $state([]);
	let searchQuery = $state('');
	let selectedMember: Member | null = $state(null);
	let hasMore = true;
	let isAppending = $state(false);
	let searchTimeout: ReturnType<typeof setTimeout>;

	let observer: IntersectionObserver | undefined = $state();
	let sentinel: HTMLElement | undefined = $state();

	async function loadMembers(reset = false) {
		if (reset) {
			loading = true;
			hasMore = true;
		} else {
			if (!hasMore || isAppending || loading) return;
			isAppending = true;
		}

		try {
			await selectorMembersStore.load(
				{
					search: searchQuery || undefined,
					include_inactive: true,
					limit: 20
				},
				reset
			);

			memberList = selectorMembersStore.list;
			hasMore = selectorMembersStore.pagination.hasMore;

			// If value exists, try to find the member object to highlight
			if (value && reset) {
				const found = memberList.find((m) => m.name === value);
				if (found) selectedMember = found;
			}

			await tick();
			initObserver();
		} catch (e) {
			logger.error('Failed to load members', e, { context: 'MemberSelector' });
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
			onselect?.(selectedMember);
			close();
		}
	}

	function close() {
		isOpen = false;
		searchQuery = '';
		memberList = [];
	}
	// Load members only when opened (handled in onclick/onkeydown)
	$effect(() => {
		if (isOpen && sentinel && observer) {
			observer.observe(sentinel);
		}
	});
</script>

<div class="relative">
	<div class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
		<User class="w-4 h-4" />
	</div>
	<input
		{id}
		{name}
		type="text"
		readonly
		{value}
		onclick={() => {
			isOpen = true;
			if (memberList.length === 0) loadMembers(true);
		}}
		onkeydown={(e) => {
			if (e.key === 'Enter') {
				isOpen = true;
				if (memberList.length === 0) loadMembers(true);
			}
		}}
		class="w-full pl-9 pr-10 py-3 bg-white dark:bg-zinc-900 border border-gray-200 dark:border-zinc-700 rounded-xl focus:ring-red-500 outline-none text-sm font-medium text-gray-900 dark:text-gray-100 cursor-pointer"
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
						{title || t('profile.oshiModal.title')}
					</h3>
					<p class="text-sm text-gray-500 dark:text-gray-400">
						{subtitle || t('profile.oshiModal.subtitle')}
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
						id="member-search"
						name="member-search"
						type="text"
						bind:value={searchQuery}
						oninput={handleSearch}
						placeholder={t('profile.oshiModal.searchPlaceholder')}
						class="w-full pl-10 pr-4 py-2 rounded-xl border border-gray-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-gray-900 dark:text-white focus:outline-none focus:border-red-300 focus:ring-4 focus:ring-red-50 dark:focus:ring-red-900/30 transition-all font-medium text-sm"
					/>
				</div>
			</div>

			<!-- Member Grid -->
			<div class="flex-1 overflow-y-auto p-6 scrollbar-hide overscroll-contain">
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
					<div class="grid grid-cols-3 sm:grid-cols-3 md:grid-cols-4 gap-2 md:gap-4">
						{#each memberList as member (member.id)}
							<button
								type="button"
								class="group relative flex flex-col items-center text-center p-2 md:p-3 rounded-2xl transition-all duration-200 border-2 cursor-pointer
								{selectedMember?.id === member.id
									? 'border-red-500 bg-red-50/50 dark:bg-red-900/20'
									: 'border-transparent hover:bg-gray-50 dark:hover:bg-zinc-800 hover:border-gray-100 dark:hover:border-zinc-700'}"
								onclick={() => selectMember(member)}
							>
								<div class="relative w-14 h-14 md:w-20 md:h-20 mb-2 md:mb-3">
									{#if member.img}
										<OptimizedImage
											src={getExternalMediaUrl(member.img)}
											srcMedium={getExternalMediaUrl(member.img_medium)}
											srcSmall={getExternalMediaUrl(member.img_small)}
											blurHash={member.blurHash}
											alt={member.name}
											class="w-full h-full rounded-full object-cover shadow-sm group-hover:shadow-md transition-shadow {selectedMember?.id ===
											member.id
												? 'ring-2 ring-red-500 ring-offset-2 dark:ring-offset-zinc-900'
												: ''}"
											sizes="56px 80px"
										/>
									{:else}
										<div
											class="w-full h-full rounded-full bg-gradient-to-br from-gray-100 to-gray-200 dark:from-zinc-800 dark:to-zinc-700 flex items-center justify-center shadow-sm group-hover:shadow-md transition-shadow {selectedMember?.id ===
											member.id
												? 'ring-2 ring-red-500 ring-offset-2 dark:ring-offset-zinc-900'
												: ''}"
										>
											<User class="w-7 h-7 md:w-10 md:h-10 text-gray-400 dark:text-zinc-400" />
										</div>
									{/if}
									{#if selectedMember?.id === member.id}
										<div
											class="absolute -right-0.5 -top-0.5 w-5 h-5 md:w-6 md:h-6 bg-red-500 rounded-full flex items-center justify-center text-white shadow-sm animate-scale-up"
										>
											<Check class="w-3 h-3 md:w-3.5 md:h-3.5" />
										</div>
									{/if}
								</div>
								<div class="h-7 md:h-8 flex items-center justify-center w-full mb-1">
									<h4
										class="font-bold text-gray-800 dark:text-white text-[11px] md:text-xs leading-snug line-clamp-2 overflow-hidden text-center w-full"
									>
										{member.name}
									</h4>
								</div>
								<div class="flex items-center gap-1 flex-wrap justify-center">
									{#if member.generation && member.generation !== '-'}
										<span
											class="text-[9px] md:text-[10px] font-bold text-gray-400 dark:text-gray-500 uppercase tracking-wide bg-gray-100 dark:bg-zinc-800 px-1.5 md:px-2 py-0.5 rounded-full group-hover:bg-white dark:group-hover:bg-zinc-700 transition-colors"
										>
											{t('profile.oshiModal.generation', { gen: member.generation })}
										</span>
									{/if}
									{#if !member.active}
										<span
											class="text-[9px] md:text-[10px] font-bold text-amber-600 dark:text-amber-400 uppercase tracking-wide bg-amber-50 dark:bg-amber-900/30 px-1.5 md:px-2 py-0.5 rounded-full"
										>
											{member.member_type || 'EX-MEMBER'}
										</span>
									{/if}
								</div>
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
					onclick={close}
					class="px-4 py-2 rounded-xl text-gray-500 hover:text-gray-700 font-bold text-sm transition-colors cursor-pointer"
				>
					{t('profile.oshiModal.cancel')}
				</button>
				<button
					type="button"
					disabled={!selectedMember}
					onclick={confirmSelection}
					class="idol-gradient text-white px-6 py-2 rounded-xl font-bold text-sm shadow-lg shadow-red-200 hover:shadow-xl hover:scale-105 transition-all disabled:opacity-50 disabled:scale-100 disabled:shadow-none cursor-pointer"
				>
					{t('common.confirmSelection')}
				</button>
			</div>
		</div>
	</div>
{/if}
