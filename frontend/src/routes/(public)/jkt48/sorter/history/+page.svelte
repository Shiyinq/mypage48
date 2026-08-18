<script lang="ts">
	import { onMount } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { publicSorter } from '$lib/stores/sorter.svelte';
	import { sorterNavbarStore } from '$lib/stores/sorterNavbar.svelte';

	import { Calendar, Trash2, Eye, History, Info } from 'lucide-svelte';
	import { fade, fly } from 'svelte/transition';

	const { t, locale } = useTranslation();
	const sorter = publicSorter;

	let deleteConfirmId = $state<string | null>(null);

	function parseUTCDate(dateStr: string) {
		const timePart = dateStr.split('T')[1] || '';
		if (!dateStr.endsWith('Z') && !timePart.includes('+') && !timePart.includes('-')) {
			return new Date(dateStr + 'Z');
		}
		return new Date(dateStr);
	}

	function formatDate(dateStr: string) {
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

	function confirmDelete(id: string) {
		deleteConfirmId = id;
	}

	function cancelDelete() {
		deleteConfirmId = null;
	}

	function executeDelete(id: string) {
		sorter.deleteSavedHistoryLocal(id);
		deleteConfirmId = null;
	}

	onMount(() => {
		sorter.loadSavedHistoriesLocal();
	});

	$effect(() => {
		sorterNavbarStore.update({
			pageType: 'history-list'
		});
		return () => {
			sorterNavbarStore.reset();
		};
	});
</script>

<SEO
	title={`${t('theater.sorter.history') || 'Riwayat Sorter'} - Oshi Sorter`}
	path="/jkt48/sorter/history"
	description={t('theater.sorter.subtitle')}
/>

<div
	class="w-full flex flex-col items-center justify-start min-h-[calc(100svh-64px)] pt-4 md:pt-8 pb-12 overflow-hidden"
>
	<div in:fade={{ duration: 300 }} class="w-full max-w-5xl mx-auto px-4 pb-12">
		<div
			class="mb-6 p-4 rounded-2xl bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-900/30 flex gap-3 items-start"
		>
			<Info class="w-5 h-5 text-amber-600 dark:text-amber-500 shrink-0 mt-0.5" />
			<div class="text-sm font-medium text-amber-800 dark:text-amber-200/80">
				{t('theater.sorter.publicHistoryWarning') ||
					'Riwayat yang tersimpan di sini bersifat lokal pada browser perangkat ini. Kapasitas penyimpanan terbatas dan riwayat ini akan hilang secara permanen jika Anda menghapus data situs atau cache browser.'}
				<span class="font-bold">
					{t('theater.sorter.publicHistoryLoginInstruction') ||
						'Jika ingin menyimpan riwayat secara permanen, silakan login terlebih dahulu.'}
				</span>
			</div>
		</div>

		{#if sorter.savedHistories.length === 0}
			<div
				class="flex flex-col items-center justify-center text-center p-8 sm:p-16 border-2 border-dashed border-zinc-200 dark:border-zinc-800 rounded-3xl bg-white/50 dark:bg-zinc-900/50 backdrop-blur-md"
			>
				<div
					class="w-16 h-16 bg-red-50 dark:bg-red-600/10 rounded-full flex items-center justify-center mb-4"
				>
					<History class="w-8 h-8 text-red-600" />
				</div>
				<h3 class="text-lg font-black text-themed tracking-tight mb-2 uppercase">
					{t('theater.sorter.noHistoryTitle') || 'Belum Ada Riwayat'}
				</h3>
				<p
					class="text-xs font-medium text-zinc-400 dark:text-zinc-500 max-w-sm leading-relaxed mb-6"
				>
					{t('theater.sorter.noHistoryDesc') ||
						'Selesaikan sorter dan simpan hasilnya untuk melihat riwayat peringkat oshi terbaikmu di sini.'}
				</p>
			</div>
		{:else}
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
				{#each sorter.savedHistories as item, i (item._id)}
					<!-- svelte-ignore a11y_click_events_have_key_events -->
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<div
						in:fly={{ y: 20, delay: i * 50, duration: 400 }}
						onclick={() => sorter.viewHistoryDetail(item)}
						class="group relative bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl p-5 hover:border-red-400 dark:hover:border-red-600/50 transition-all hover:scale-[1.01] hover:shadow-xl hover:shadow-red-600/[0.02] flex flex-col justify-between min-h-[190px] cursor-pointer"
					>
						<div class="space-y-3">
							<!-- Top: Date and delete icon -->
							<div
								class="flex items-center justify-between text-[10px] font-bold text-zinc-400 dark:text-zinc-500 uppercase tracking-wider"
							>
								<div class="flex items-center gap-1.5">
									<Calendar size={12} class="text-red-600" />
									<span>{formatDate(item.created_at)}</span>
								</div>

								{#if deleteConfirmId === item._id}
									<div class="flex items-center gap-2" in:fade>
										<button
											onclick={(e) => {
												e.stopPropagation();
												executeDelete(item._id);
											}}
											class="px-2 py-0.5 bg-red-600 hover:bg-red-700 text-white rounded font-black text-[9px] cursor-pointer"
										>
											{t('theater.sorter.confirmYes').toUpperCase()}
										</button>
										<button
											onclick={(e) => {
												e.stopPropagation();
												cancelDelete();
											}}
											class="px-2 py-0.5 bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 rounded font-black text-[9px] cursor-pointer"
										>
											{t('theater.sorter.confirmCancel').toUpperCase()}
										</button>
									</div>
								{:else}
									<button
										onclick={(e) => {
											e.stopPropagation();
											confirmDelete(item._id);
										}}
										class="text-zinc-400 hover:text-red-600 dark:hover:text-red-400 p-1 rounded-lg transition-colors cursor-pointer bg-transparent border-none"
										title={t('theater.sorter.deleteHistory') || 'Hapus Riwayat'}
									>
										<Trash2 size={13} />
									</button>
								{/if}
							</div>

							<!-- Middle: Title & Description -->
							<div class="space-y-1">
								<h4
									class="font-black text-themed text-base group-hover:text-red-600 transition-colors uppercase tracking-tight line-clamp-1 leading-snug"
								>
									{item.title}
								</h4>
								{#if item.description}
									<p
										class="text-xs font-semibold text-zinc-500 dark:text-zinc-400 line-clamp-2 leading-relaxed"
									>
										{item.description}
									</p>
								{/if}
							</div>
						</div>

						<!-- Bottom: Filters & View Button -->
						<div
							class="flex items-end justify-between pt-4 border-t border-zinc-100 dark:border-zinc-800/80 mt-4"
						>
							<!-- Filters pills -->
							<div class="flex flex-wrap gap-1 max-w-[70%]">
								{#each item.filters as gen}
									<span
										class="px-2 py-0.5 rounded-full text-[9px] font-black tracking-wider uppercase bg-red-50/80 dark:bg-red-600/10 border border-red-100/50 dark:border-red-900/30 text-red-600 dark:text-red-400 select-none"
									>
										{t('theater.sorter.genLabel', { gen })}
									</span>
								{/each}
							</div>

							<!-- Action -->
							<button
								onclick={(e) => {
									e.stopPropagation();
									sorter.viewHistoryDetail(item);
								}}
								class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-zinc-50 dark:bg-zinc-800 hover:bg-red-600 hover:text-white border border-zinc-200 dark:border-zinc-700 hover:border-red-600 transition-all font-black text-xs cursor-pointer group-hover:shadow-md group-hover:shadow-red-600/10"
							>
								<Eye size={12} />
								<span>{t('theater.sorter.detail').toUpperCase()}</span>
							</button>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>
