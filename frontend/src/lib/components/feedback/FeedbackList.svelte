<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { feedbackStore } from '$lib/stores/feedback.svelte';
	import { onMount } from 'svelte';
	import { MessageSquare, Calendar, Trash2, X, LoaderCircle } from 'lucide-svelte';
	import { formatDate } from '$lib/i18n';
	import { showToast } from '$lib/stores';
	import { fade } from 'svelte/transition';

	const { t } = useTranslation();

	let isLoading = $state(!feedbackStore.isLoaded);
	let itemToDelete: string | null = $state(null);
	let isDeleting = $state(false);

	onMount(async () => {
		try {
			await feedbackStore.loadMy(1, 50); // Load initial feedback
		} finally {
			isLoading = false;
		}
	});

	async function confirmDelete() {
		if (!itemToDelete || isDeleting) return;
		isDeleting = true;
		try {
			await feedbackStore.deleteFeedback(itemToDelete);
			showToast(t('feedback.delete.success'), 'success');
		} catch (error) {
			console.error(error);
			showToast(t('feedback.delete.error'), 'error');
		} finally {
			isDeleting = false;
			itemToDelete = null;
		}
	}

	function getStatusColor(status: string) {
		switch (status) {
			case 'pending':
				return 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-zinc-800 dark:text-slate-300 dark:border-zinc-700';
			case 'noted':
				return 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800/50';
			case 'in_progress':
				return 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-900/30 dark:text-amber-300 dark:border-amber-800/50';
			case 'implemented':
				return 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-800/50';
			case 'rejected':
				return 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-300 dark:border-red-800/50';
			case 'spam':
				return 'bg-slate-200 text-slate-500 border-slate-300 dark:bg-zinc-800/50 dark:text-zinc-500 dark:border-zinc-700';
			default:
				return 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-zinc-800 dark:text-slate-300 dark:border-zinc-700';
		}
	}
</script>

<div class="space-y-6">
	{#if isLoading}
		<div class="space-y-4">
			{#each [1, 2, 3] as _}
				<div
					class="bg-white dark:bg-zinc-900 rounded-3xl p-6 shadow-sm border border-slate-100 dark:border-zinc-800 animate-pulse"
				>
					<div class="flex flex-wrap items-start justify-between gap-4 mb-4">
						<div class="flex items-center gap-3">
							<!-- Type Badge Skeleton -->
							<div class="h-6 w-24 bg-slate-200 dark:bg-zinc-800 rounded-lg"></div>
							<!-- Date Skeleton -->
							<div class="h-4 w-20 bg-slate-200 dark:bg-zinc-800 rounded-md"></div>
						</div>
						<!-- Status Badge Skeleton -->
						<div class="h-6 w-32 bg-slate-200 dark:bg-zinc-800 rounded-full"></div>
					</div>
					<!-- Message Skeleton -->
					<div class="space-y-2 mt-2">
						<div class="h-4 w-full bg-slate-200 dark:bg-zinc-800 rounded-md"></div>
						<div class="h-4 w-3/4 bg-slate-200 dark:bg-zinc-800 rounded-md"></div>
					</div>
				</div>
			{/each}
		</div>
	{:else if feedbackStore.data.length === 0}
		<div
			class="bg-white dark:bg-zinc-900 rounded-[2rem] p-10 text-center border border-slate-100 dark:border-zinc-800"
		>
			<div
				class="w-16 h-16 bg-slate-50 dark:bg-zinc-800 rounded-full flex items-center justify-center mx-auto mb-4"
			>
				<MessageSquare class="w-8 h-8 text-slate-400 dark:text-slate-500" />
			</div>
			<h3 class="text-lg font-bold text-slate-900 dark:text-white mb-2">
				{t('feedback.empty.title')}
			</h3>
			<p class="text-slate-500 dark:text-slate-400">
				{t('feedback.empty.description')}
			</p>
		</div>
	{:else}
		<div class="space-y-4">
			{#each feedbackStore.data as item}
				<div
					class="bg-white dark:bg-zinc-900 rounded-3xl p-6 shadow-sm border border-slate-100 dark:border-zinc-800 transition-all hover:shadow-md"
				>
					<div class="flex flex-wrap items-start justify-between gap-4 mb-4">
						<div class="flex items-center gap-3">
							<span
								class="px-3 py-1 text-xs font-bold uppercase tracking-wider rounded-lg border {item.type ===
								'issue'
									? 'bg-red-50 text-red-600 border-red-200 dark:bg-red-900/20 dark:text-red-400 dark:border-red-900/50'
									: item.type === 'suggestion'
										? 'bg-blue-50 text-blue-600 border-blue-200 dark:bg-blue-900/20 dark:text-blue-400 dark:border-blue-900/50'
										: 'bg-amber-50 text-amber-600 border-amber-200 dark:bg-amber-900/20 dark:text-amber-400 dark:border-amber-900/50'}"
							>
								{t(`feedback.form.type.${item.type}`)}
							</span>
							<div class="flex items-center text-xs text-slate-500 dark:text-slate-400 font-medium">
								<Calendar class="w-3.5 h-3.5 mr-1" />
								{formatDate(item.created_at)}
							</div>
						</div>
						<div class="flex items-center">
							<span
								class="px-3 py-1 text-[11px] font-bold rounded-full uppercase tracking-wider {getStatusColor(
									item.status
								)}"
							>
								{t(`feedback.status.${item.status}`)}
							</span>
							<button
								class="p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-full transition-colors cursor-pointer"
								onclick={() => (itemToDelete = item.id)}
								title={t('feedback.delete.button')}
							>
								<Trash2 size={16} />
							</button>
						</div>
					</div>

					<p
						class="text-slate-700 dark:text-slate-300 text-sm leading-relaxed whitespace-pre-wrap font-medium"
					>
						{item.message}
					</p>

					{#if item.admin_notes}
						<div class="mt-4 pt-4 border-t border-slate-100 dark:border-zinc-800">
							<div class="bg-slate-50 dark:bg-zinc-800/50 rounded-2xl p-4">
								<p
									class="text-xs font-bold text-slate-500 dark:text-slate-400 mb-1 uppercase tracking-wider"
								>
									{t('admin.feedback.modal.notesLabel')}
								</p>
								<p class="text-sm text-slate-700 dark:text-slate-300 whitespace-pre-wrap">
									{item.admin_notes}
								</p>
							</div>
						</div>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>

<!-- Delete Confirmation Modal -->
{#if itemToDelete}
	<div class="fixed inset-0 z-[9999] flex items-center justify-center p-4">
		<!-- Backdrop -->
		<!-- svelte-ignore a11y_click_events_have_key_events -->
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div
			class="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity duration-300"
			onclick={() => (itemToDelete = null)}
			transition:fade
		></div>

		<!-- Modal Content -->
		<div
			class="bg-white dark:bg-zinc-900 w-full max-w-sm rounded-3xl shadow-2xl relative z-50 pointer-events-auto overflow-hidden border border-slate-100 dark:border-zinc-800"
			transition:fade={{ duration: 200 }}
		>
			<div class="p-6">
				<!-- Header -->
				<div class="flex items-start justify-between mb-4">
					<div
						class="w-12 h-12 rounded-2xl bg-red-50 dark:bg-red-900/20 text-red-500 dark:text-red-400 flex items-center justify-center shrink-0 border border-red-100 dark:border-red-900/30"
					>
						<Trash2 class="w-6 h-6" />
					</div>
					<button
						onclick={() => (itemToDelete = null)}
						class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors cursor-pointer"
					>
						<X class="w-5 h-5" />
					</button>
				</div>

				<!-- Content -->
				<h3 class="text-xl font-bold text-slate-900 dark:text-white mb-2">
					{t('feedback.delete.confirmTitle')}
				</h3>
				<p class="text-slate-500 dark:text-slate-400 text-sm leading-relaxed mb-8">
					{t('feedback.delete.confirmMessage')}
				</p>

				<!-- Actions -->
				<div class="flex gap-3">
					<button
						class="flex-1 px-4 py-2.5 rounded-xl text-sm font-bold text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-zinc-800 hover:bg-slate-200 dark:hover:bg-zinc-700 transition-colors cursor-pointer"
						onclick={() => (itemToDelete = null)}
						disabled={isDeleting}
					>
						{t('common.cancel')}
					</button>
					<button
						class="flex-1 px-4 py-2.5 rounded-xl text-sm font-bold text-white bg-red-500 hover:bg-red-600 shadow-lg shadow-red-500/20 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
						onclick={confirmDelete}
						disabled={isDeleting}
					>
						{#if isDeleting}
							<LoaderCircle class="w-4 h-4 animate-spin" />
						{:else}
							{t('feedback.delete.button')}
						{/if}
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}
