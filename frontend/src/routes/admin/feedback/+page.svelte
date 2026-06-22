<script lang="ts">
	import { onMount } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { showToast } from '$lib/stores';
	import SEO from '$lib/components/SEO.svelte';
	import {
		MessageSquare,
		AlertCircle,
		Lightbulb,
		HelpCircle,
		ChevronLeft,
		ChevronRight
	} from 'lucide-svelte';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import ErrorState from '$lib/components/ErrorState.svelte';
	import CardSkeleton from '$lib/components/skeletons/CardSkeleton.svelte';
	import { formatDate } from '$lib/i18n';
	import { feedbackStore, loadFeedback, isFeedbackLoading } from '$lib/stores/feedback.svelte';

	import AdminFeedbackModal from '$lib/components/admin/AdminFeedbackModal.svelte';
	import type { FeedbackMessage } from '$lib/types/feedback';

	const { t } = useTranslation();

	let error: string | null = $state(null);
	let selectedFeedback: FeedbackMessage | null = $state(null);
	let isModalOpen = $state(false);
	let isSubmitting = $state(false);

	type FilterType = 'ongoing' | 'done' | 'all' | 'specific';
	let currentFilter: FilterType = $state('ongoing');
	let specificStatus: string = $state('pending');

	const getStatuses = (): string[] => {
		switch (currentFilter) {
			case 'ongoing':
				return ['pending', 'in_progress'];
			case 'done':
				return ['noted', 'implemented', 'rejected', 'spam'];
			case 'all':
				return [];
			case 'specific':
				return [specificStatus];
			default:
				return [];
		}
	};

	const loadData = async (page = 1) => {
		error = null;
		try {
			await loadFeedback(page, 20, getStatuses());
		} catch {
			error = t('admin.feedback.errorDesc');
			showToast(t('admin.feedback.errorTitle'), 'error');
		}
	};

	onMount(() => {
		loadData(1);
	});

	const getIcon = (type: string) => {
		switch (type) {
			case 'issue':
				return AlertCircle;
			case 'suggestion':
				return Lightbulb;
			default:
				return HelpCircle;
		}
	};

	const getColor = (type: string) => {
		switch (type) {
			case 'issue':
				return 'text-red-600 bg-red-100 dark:bg-red-900/20 dark:text-red-400';
			case 'suggestion':
				return 'text-blue-600 bg-blue-100 dark:bg-blue-900/20 dark:text-blue-400';
			default:
				return 'text-slate-600 bg-slate-100 dark:bg-slate-800 dark:text-slate-400';
		}
	};

	const getStatusColor = (status: string) => {
		switch (status) {
			case 'pending':
				return 'bg-slate-100 text-slate-600 border-slate-200 dark:bg-zinc-800 dark:text-slate-400 dark:border-zinc-700';
			case 'noted':
				return 'bg-blue-50 text-blue-600 border-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-800/50';
			case 'in_progress':
				return 'bg-amber-50 text-amber-600 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800/50';
			case 'implemented':
				return 'bg-emerald-50 text-emerald-600 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-400 dark:border-emerald-800/50';
			case 'rejected':
				return 'bg-red-50 text-red-600 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-800/50';
			case 'spam':
				return 'bg-slate-200 text-slate-500 border-slate-300 dark:bg-zinc-800/50 dark:text-zinc-500 dark:border-zinc-700';
			default:
				return 'bg-slate-100 text-slate-600 border-slate-200 dark:bg-zinc-800 dark:text-slate-400 dark:border-zinc-700';
		}
	};

	function openModal(item: FeedbackMessage) {
		selectedFeedback = item;
		isModalOpen = true;
	}

	async function handleUpdateStatus(data: { status: string; admin_notes: string }) {
		if (!selectedFeedback) return;
		isSubmitting = true;
		try {
			await feedbackStore.updateStatus(selectedFeedback.id, data.status, data.admin_notes);
			showToast('Feedback status updated successfully', 'success');
			isModalOpen = false;
		} catch (error) {
			console.error(error);
			showToast('Failed to update feedback status', 'error');
		} finally {
			isSubmitting = false;
		}
	}
</script>

<SEO title={t('admin.feedback.title')} />

<div class="space-y-6">
	<div
		class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 bg-white dark:bg-zinc-800 p-4 rounded-3xl shadow-sm border border-slate-100 dark:border-zinc-700"
	>
		<div class="flex items-center gap-4">
			<h2 class="text-xl font-bold text-gray-800 dark:text-white flex items-center gap-2 min-w-fit">
				<MessageSquare class="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
				{t('admin.feedback.title')} ({feedbackStore.meta.total_data})
			</h2>
			<p
				class="hidden lg:block text-slate-500 dark:text-slate-400 text-sm border-l border-gray-200 dark:border-zinc-700 pl-4 ml-2"
			>
				{t('admin.feedback.subtitle')}
			</p>
		</div>

		<!-- Filter Controls -->
		<div class="flex flex-wrap items-center gap-2 sm:gap-4">
			<button
				class="cursor-pointer px-4 py-2 rounded-xl text-sm font-bold transition-all border {currentFilter ===
				'ongoing'
					? 'bg-cyan-50 text-cyan-600 border-cyan-200 dark:bg-cyan-900/20 dark:text-cyan-400 dark:border-cyan-900/50'
					: 'bg-slate-50 text-slate-600 border-transparent hover:bg-slate-100 dark:bg-zinc-800/50 dark:text-slate-400 dark:hover:bg-zinc-800'}"
				onclick={() => {
					currentFilter = 'ongoing';
					loadData(1);
				}}
			>
				{t('feedback.filter.ongoing')}
			</button>
			<button
				class="cursor-pointer px-4 py-2 rounded-xl text-sm font-bold transition-all border {currentFilter ===
				'done'
					? 'bg-emerald-50 text-emerald-600 border-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-400 dark:border-emerald-900/50'
					: 'bg-slate-50 text-slate-600 border-transparent hover:bg-slate-100 dark:bg-zinc-800/50 dark:text-slate-400 dark:hover:bg-zinc-800'}"
				onclick={() => {
					currentFilter = 'done';
					loadData(1);
				}}
			>
				{t('feedback.filter.done')}
			</button>
			<button
				class="cursor-pointer px-4 py-2 rounded-xl text-sm font-bold transition-all border {currentFilter ===
				'all'
					? 'bg-slate-800 text-white border-slate-700 dark:bg-slate-200 dark:text-slate-900 dark:border-slate-300'
					: 'bg-slate-50 text-slate-600 border-transparent hover:bg-slate-100 dark:bg-zinc-800/50 dark:text-slate-400 dark:hover:bg-zinc-800'}"
				onclick={() => {
					currentFilter = 'all';
					loadData(1);
				}}
			>
				{t('feedback.filter.all')}
			</button>

			<div class="h-6 w-px bg-slate-200 dark:bg-zinc-700 hidden sm:block"></div>

			<div class="w-full sm:w-auto flex items-center gap-2 mt-1 sm:mt-0">
				<select
					bind:value={specificStatus}
					onchange={() => {
						currentFilter = 'specific';
						loadData(1);
					}}
					class="w-full px-4 py-2 rounded-xl text-sm font-bold bg-slate-50 dark:bg-zinc-800/50 border {currentFilter ===
					'specific'
						? 'border-purple-200 text-purple-600 dark:border-purple-900/50 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/20'
						: 'border-transparent text-slate-600 dark:text-slate-400'} outline-none focus:ring-2 focus:ring-purple-500 transition-all cursor-pointer"
				>
					<option value="pending">{t('feedback.status.pending') || 'Pending'}</option>
					<option value="in_progress">{t('feedback.status.in_progress') || 'In Progress'}</option>
					<option value="noted">{t('feedback.status.noted') || 'Noted'}</option>
					<option value="implemented">{t('feedback.status.implemented') || 'Implemented'}</option>
					<option value="rejected">{t('feedback.status.rejected') || 'Rejected'}</option>
					<option value="spam">{t('feedback.status.spam') || 'Spam'}</option>
				</select>
			</div>
		</div>
	</div>

	{#if isFeedbackLoading.value && feedbackStore.data.length === 0}
		<div class="grid gap-4">
			{#each Array(5)}
				<CardSkeleton lines={3} />
			{/each}
		</div>
	{:else if error}
		<ErrorState
			title={t('admin.feedback.errorTitle') || 'Failed to load feedback'}
			description={error || ''}
			onRetry={() => loadData(1)}
		/>
	{:else if feedbackStore.data.length === 0}
		<EmptyState
			icon={MessageSquare}
			title={t('admin.feedback.emptyTitle')}
			description={t('admin.feedback.emptyDesc')}
		/>
	{:else}
		<div class="grid gap-4">
			{#each feedbackStore.data as item}
				{@const SvelteComponent = getIcon(item.type)}
				<!-- svelte-ignore a11y_click_events_have_key_events -->
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<div
					class="p-5 rounded-2xl bg-white dark:bg-zinc-900/50 border border-slate-200 dark:border-zinc-800 hover:border-cyan-200 dark:hover:border-cyan-900/30 transition-all group cursor-pointer"
					onclick={() => openModal(item)}
				>
					<div class="flex items-start gap-4">
						<div
							class="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 {getColor(
								item.type
							)}"
						>
							<SvelteComponent size={20} />
						</div>
						<div class="flex-1 min-w-0">
							<div class="flex flex-wrap items-start justify-between gap-2 mb-2">
								<div class="flex flex-wrap items-center gap-2">
									<span
										class="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider {getColor(
											item.type
										)}"
									>
										{item.type}
									</span>
									<span
										class="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider border {getStatusColor(
											item.status || 'pending'
										)}"
									>
										{t(`feedback.status.${item.status || 'pending'}`)}
									</span>
								</div>
								<span class="text-xs text-slate-400 font-medium whitespace-nowrap">
									{formatDate(item.created_at, {
										year: 'numeric',
										month: 'short',
										day: 'numeric'
									})}
								</span>
							</div>
							<p
								class="text-slate-900 dark:text-slate-200 leading-relaxed whitespace-pre-wrap break-words break-all"
							>
								{item.message}
							</p>
							{#if item.name}
								<div class="mt-3 flex items-center justify-between">
									<div class="flex items-center gap-3 text-xs text-slate-400">
										<span class="font-bold text-slate-500 dark:text-slate-400">
											{item.name}
										</span>
									</div>
								</div>
							{/if}
						</div>
					</div>
				</div>
			{/each}
		</div>

		<!-- Pagination -->
		{#if feedbackStore.meta.total_data > feedbackStore.meta.per_page}
			<div
				class="flex items-center justify-center gap-4 mt-8 pt-6 border-t border-slate-100 dark:border-zinc-800"
			>
				<button
					class="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
					disabled={feedbackStore.meta.current_page === 1}
					onclick={() => loadData(feedbackStore.meta.current_page - 1)}
				>
					<ChevronLeft size={20} />
				</button>
				<span class="text-sm text-slate-500 font-medium">
					Page {feedbackStore.meta.current_page} of {feedbackStore.meta.last_page}
				</span>
				<button
					class="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
					disabled={feedbackStore.meta.next_page === null}
					onclick={() => loadData(feedbackStore.meta.current_page + 1)}
				>
					<ChevronRight size={20} />
				</button>
			</div>
		{/if}

		{#if feedbackStore.meta.next_page === null && feedbackStore.data.length > 0}
			<div class="pb-12 pt-6 text-center text-gray-400 text-sm">
				{t('admin.feedback.noMoreFeedback')}
			</div>
		{/if}
	{/if}
</div>

<AdminFeedbackModal
	bind:show={isModalOpen}
	feedback={selectedFeedback}
	{isSubmitting}
	onsubmit={handleUpdateStatus}
/>
