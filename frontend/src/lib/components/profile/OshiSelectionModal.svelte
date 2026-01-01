<script lang="ts">
	import { Search, X, Check } from 'lucide-svelte';
	import Button from '$lib/components/Button.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { Member } from '$lib/apis/members';
	import { fade, scale } from 'svelte/transition';

	export let show: boolean = false;
	export let members: Member[] = [];
	export let loading: boolean = false;
	export let saving: boolean = false;
	export let onClose: () => void;
	export let onSave: (memberId: number) => void;

	const { t } = useTranslation();

	let searchQuery = '';
	let selectedOshiId: number | null = null;
	let filteredMembers: Member[] = [];

	// Reset state when modal opens/closes or members change
	$: if (show) {
		filteredMembers = members;
		// If we wanted to persist selection we could, but typical flow resets it
		// selectedOshiId = null; // Optional: keep or reset? Parent resets it in original code.
		// Use internal state initialization if needed.
	} else {
		searchQuery = '';
		selectedOshiId = null;
	}

	$: {
		if (!searchQuery.trim()) {
			filteredMembers = members;
		} else {
			const q = searchQuery.toLowerCase();
			filteredMembers = members.filter(
				(m) =>
					m.name.toLowerCase().includes(q) ||
					m.nickname.toLowerCase().includes(q) ||
					m.generation.toLowerCase().includes(q)
			);
		}
	}

	function handleSave() {
		if (selectedOshiId) {
			onSave(selectedOshiId);
		}
	}
</script>

{#if show}
	<div class="fixed inset-0 z-[100] flex items-center justify-center p-4">
		<!-- Backdrop -->
		<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
		<div
			class="absolute inset-0 bg-black/60 backdrop-blur-sm"
			transition:fade={{ duration: 200 }}
			on:click={onClose}
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
					on:click={onClose}
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
						placeholder={$t('profile.oshiModal.searchPlaceholder')}
						class="w-full pl-10 pr-4 py-2 rounded-xl border border-gray-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-gray-900 dark:text-white focus:outline-none focus:border-red-300 focus:ring-4 focus:ring-red-50 dark:focus:ring-red-900/30 transition-all font-medium text-sm"
					/>
				</div>
			</div>

			<!-- Member Grid -->
			<div class="flex-1 overflow-y-auto p-6 scrollbar-hide">
				{#if loading}
					<div class="flex flex-col items-center justify-center py-12">
						<div
							class="w-10 h-10 border-4 border-red-100 border-t-red-500 rounded-full animate-spin mb-4"
						></div>
						<p class="text-sm text-gray-500">{$t('profile.oshiModal.loading')}</p>
					</div>
				{:else if filteredMembers.length === 0}
					<div class="text-center py-12">
						<Search class="w-12 h-12 text-gray-200 mx-auto mb-3" />
						<p class="text-gray-500">
							{$t('profile.oshiModal.noMembers', { query: searchQuery })}
						</p>
					</div>
				{:else}
					<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
						{#each filteredMembers as member}
							<button
								class="group relative flex flex-col items-center text-center p-3 rounded-2xl transition-all duration-200 border-2 cursor-pointer
								{selectedOshiId === member.id
									? 'border-red-500 bg-red-50/50 dark:bg-red-900/20'
									: 'border-transparent hover:bg-gray-50 dark:hover:bg-zinc-800 hover:border-gray-100 dark:hover:border-zinc-700'}"
								on:click={() => (selectedOshiId = member.id)}
							>
								<div class="relative w-20 h-20 mb-3">
									<img
										src={member.img}
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
				{/if}
			</div>

			<!-- Footer Action -->
			<div
				class="p-6 border-t border-gray-100 dark:border-zinc-800 bg-white dark:bg-zinc-900 flex justify-end gap-3 z-10"
			>
				<Button variant="outline" on:click={onClose} class="cursor-pointer"
					>{$t('profile.oshiModal.cancel')}</Button
				>
				<Button
					variant="primary"
					disabled={!selectedOshiId || saving}
					loading={saving}
					on:click={handleSave}
					class="cursor-pointer"
				>
					{$t('profile.oshiModal.save')}
				</Button>
			</div>
		</div>
	</div>
{/if}
