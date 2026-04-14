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

	const { t } = useTranslation();

	let error: string | null = $state(null);

	const loadData = async (page = 1) => {
		error = null;
		try {
			await loadFeedback(page);
		} catch {
			error = $t('admin.feedback.errorDesc');
			showToast($t('admin.feedback.errorTitle'), 'error');
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
</script>

<SEO title={$t('admin.feedback.title')} />

<div class="space-y-6">
	<div
		class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6 bg-white dark:bg-zinc-800 p-4 rounded-3xl shadow-sm"
	>
		<div class="flex items-center gap-4 flex-1">
			<h2 class="text-xl font-bold text-gray-800 dark:text-white flex items-center gap-2 min-w-fit">
				<MessageSquare class="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
				{$t('admin.feedback.title')} ({feedbackStore.total})
			</h2>
			<p
				class="hidden md:block text-slate-500 dark:text-slate-400 text-sm border-l border-gray-200 dark:border-zinc-700 pl-4 ml-2"
			>
				{$t('admin.feedback.subtitle')}
			</p>
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
			title={$t('admin.feedback.errorTitle') || 'Failed to load feedback'}
			description={error || ''}
			onRetry={() => loadData(1)}
		/>
	{:else if feedbackStore.data.length === 0}
		<EmptyState
			icon={MessageSquare}
			title={$t('admin.feedback.emptyTitle')}
			description={$t('admin.feedback.emptyDesc')}
		/>
	{:else}
		<div class="grid gap-4">
			{#each feedbackStore.data as item}
				{@const SvelteComponent = getIcon(item.type)}
				<div
					class="p-5 rounded-2xl bg-white dark:bg-zinc-900/50 border border-slate-200 dark:border-zinc-800 hover:border-red-200 dark:hover:border-red-900/30 transition-all group"
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
							<div class="flex items-center justify-between mb-1">
								<span
									class="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider {getColor(
										item.type
									)}"
								>
									{item.type}
								</span>
								<span class="text-xs text-slate-400 font-medium">
									{$formatDate(item.created_at, {
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
							{#if item.email || item.name}
								<div class="mt-3 flex items-center gap-3 text-xs text-slate-400">
									{#if item.name}
										<span class="font-bold text-slate-500 dark:text-slate-400">
											{item.name}
										</span>
									{/if}
									{#if item.email}
										<span>{item.email}</span>
									{/if}
								</div>
							{/if}
						</div>
					</div>
				</div>
			{/each}
		</div>

		<!-- Pagination -->
		{#if feedbackStore.total > feedbackStore.limit}
			<div
				class="flex items-center justify-center gap-4 mt-8 pt-6 border-t border-slate-100 dark:border-zinc-800"
			>
				<button
					class="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
					disabled={feedbackStore.page === 1}
					onclick={() => loadData(feedbackStore.page - 1)}
				>
					<ChevronLeft size={20} />
				</button>
				<span class="text-sm text-slate-500 font-medium">
					Page {feedbackStore.page} of {Math.ceil(feedbackStore.total / feedbackStore.limit)}
				</span>
				<button
					class="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-zinc-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
					disabled={!feedbackStore.has_more &&
						feedbackStore.page * feedbackStore.limit >= feedbackStore.total}
					onclick={() => loadData(feedbackStore.page + 1)}
				>
					<ChevronRight size={20} />
				</button>
			</div>
		{/if}

		{#if !feedbackStore.has_more && feedbackStore.data.length > 0}
			<div class="pb-12 pt-6 text-center text-gray-400 text-sm">
				{$t('admin.feedback.noMoreFeedback')}
			</div>
		{/if}
	{/if}
</div>
