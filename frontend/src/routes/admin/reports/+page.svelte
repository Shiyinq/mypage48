<script lang="ts">
	import { page48Api, type AdminReportItem } from '$lib/api/page48';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { formatDate } from '$lib/i18n';
	import SEO from '$lib/components/SEO.svelte';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import ErrorState from '$lib/components/ErrorState.svelte';
	import CardSkeleton from '$lib/components/skeletons/CardSkeleton.svelte';
	import { Flag, Image as ImageIcon, LoaderCircle } from 'lucide-svelte';

	const { t } = useTranslation();

	type FilterType = 'all' | 'post' | 'user';

	let filter = $state<FilterType>('all');
	let items = $state<AdminReportItem[]>([]);
	let loading = $state(true);
	let loadingMore = $state(false);
	let error = $state<string | null>(null);
	let hasMore = $state(false);
	let nextCursor = $state<string | null>(null);
	let total = $state(0);

	async function load(reset = false) {
		if (reset) {
			loading = true;
			items = [];
			nextCursor = null;
		} else {
			if (loadingMore || !hasMore || !nextCursor) return;
			loadingMore = true;
		}
		error = null;
		try {
			const response = await page48Api.getAdminReports(
				20,
				reset ? null : nextCursor,
				filter === 'all' ? null : filter
			);
			items = reset ? response.data : [...items, ...response.data];
			hasMore = response.meta.hasMore;
			nextCursor = response.meta.nextCursor;
			total = response.meta.total;
		} catch (err: unknown) {
			const e = err as { message?: string };
			error = e?.message || t('admin.reports.errorDesc');
			if (reset) items = [];
		} finally {
			loading = false;
			loadingMore = false;
		}
	}

	// Reload whenever the filter changes (and on mount).
	$effect(() => {
		void filter;
		load(true);
	});

	function setFilter(value: FilterType) {
		if (filter === value) return;
		filter = value;
	}

	function getTargetHref(item: AdminReportItem): string | null {
		if (item.targetType === 'post') return `/page48/post/${item.targetId}`;
		if (item.targetUsername) return `/page48/u/${item.targetUsername}`;
		return null;
	}

	function getTargetAvatar(item: AdminReportItem): string {
		if (item.targetProfilePicture) return item.targetProfilePicture;
		const name = item.targetDisplayName || item.targetUsername || '?';
		return `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=fca5a5&color=fff`;
	}

	const statusStyles: Record<string, string> = {
		pending:
			'bg-amber-50 text-amber-600 border-amber-200 dark:bg-amber-900/30 dark:text-amber-400 dark:border-amber-800/50',
		reviewed:
			'bg-blue-50 text-blue-600 border-blue-200 dark:bg-blue-900/30 dark:text-blue-400 dark:border-blue-800/50',
		resolved:
			'bg-emerald-50 text-emerald-600 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-400 dark:border-emerald-800/50',
		dismissed:
			'bg-slate-100 text-slate-500 border-slate-200 dark:bg-zinc-800 dark:text-slate-400 dark:border-zinc-700'
	};

	function getStatusStyle(status: string): string {
		return (
			statusStyles[status] ||
			'bg-slate-100 text-slate-600 border-slate-200 dark:bg-zinc-800 dark:text-slate-400 dark:border-zinc-700'
		);
	}

	const filters: { key: FilterType; label: string }[] = [
		{ key: 'all', label: 'admin.reports.filters.all' },
		{ key: 'post', label: 'admin.reports.filters.post' },
		{ key: 'user', label: 'admin.reports.filters.user' }
	];
</script>

<SEO title={t('admin.reports.title')} />

<div class="space-y-6">
	<div
		class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-2 bg-white dark:bg-zinc-800 p-4 rounded-3xl shadow-sm border border-slate-100 dark:border-zinc-700"
	>
		<div class="flex items-center gap-4">
			<h2 class="text-xl font-bold text-gray-800 dark:text-white flex items-center gap-2 min-w-fit">
				<Flag class="w-5 h-5 text-rose-600 dark:text-rose-400" />
				{t('admin.reports.title')} ({total})
			</h2>
			<p
				class="hidden lg:block text-slate-500 dark:text-slate-400 text-sm border-l border-gray-200 dark:border-zinc-700 pl-4 ml-2"
			>
				{t('admin.reports.subtitle')}
			</p>
		</div>

		<div class="flex flex-wrap items-center gap-2 sm:gap-4">
			{#each filters as item (item.key)}
				<button
					class="cursor-pointer px-4 py-2 rounded-xl text-sm font-bold transition-all border {filter ===
					item.key
						? 'bg-rose-50 text-rose-600 border-rose-200 dark:bg-rose-900/20 dark:text-rose-400 dark:border-rose-900/50'
						: 'bg-slate-50 text-slate-600 border-transparent hover:bg-slate-100 dark:bg-zinc-800/50 dark:text-slate-400 dark:hover:bg-zinc-800'}"
					onclick={() => setFilter(item.key)}
				>
					{t(item.label)}
				</button>
			{/each}
		</div>
	</div>

	{#if loading && items.length === 0}
		<div class="grid gap-4">
			{#each Array(5)}
				<CardSkeleton lines={3} />
			{/each}
		</div>
	{:else if error}
		<ErrorState
			title={t('admin.reports.errorTitle')}
			description={error}
			onRetry={() => load(true)}
		/>
	{:else if items.length === 0}
		<EmptyState
			icon={Flag}
			title={t('admin.reports.emptyTitle')}
			description={t('admin.reports.emptyDesc')}
		/>
	{:else}
		<div class="grid gap-4">
			{#each items as item (item.reportId)}
				{@const href = getTargetHref(item)}
				<div
					class="p-5 rounded-2xl bg-white dark:bg-zinc-900/50 border border-slate-200 dark:border-zinc-800"
				>
					<div class="flex flex-wrap items-center justify-between gap-2 mb-3">
						<div class="flex flex-wrap items-center gap-2">
							<span
								class="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider border {item.targetType ===
								'post'
									? 'bg-rose-50 text-rose-600 border-rose-200 dark:bg-rose-900/30 dark:text-rose-400 dark:border-rose-800/50'
									: 'bg-indigo-50 text-indigo-600 border-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-400 dark:border-indigo-800/50'}"
							>
								{item.targetType === 'post'
									? t('admin.reports.filters.post')
									: t('admin.reports.filters.user')}
							</span>
							<span
								class="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider border {getStatusStyle(
									item.status
								)}"
							>
								{t(`admin.reports.status.${item.status}`)}
							</span>
							<span class="text-xs font-semibold text-slate-500 dark:text-slate-400">
								{t(`page48.report.reason.${item.reason}`)}
							</span>
						</div>
						<span class="text-xs text-slate-400 font-medium whitespace-nowrap">
							{formatDate(item.createdAt, { year: 'numeric', month: 'short', day: 'numeric' })}
						</span>
					</div>

					<p class="text-xs text-slate-400 mb-3">
						{t('admin.reports.reportedBy', {
							username: item.reporterUsername || item.reporterUserId || '-'
						})}
					</p>

					<div
						class="rounded-xl border border-slate-100 dark:border-zinc-800 bg-slate-50/60 dark:bg-zinc-800/30 p-3"
					>
						{#if !item.targetExists}
							<p class="text-sm italic text-slate-400 dark:text-slate-500">
								{t('admin.reports.deletedTarget')}
							</p>
						{:else if item.targetType === 'post'}
							<div class="flex items-start gap-3">
								<div
									class="w-9 h-9 rounded-full overflow-hidden bg-gray-200 dark:bg-zinc-700 shrink-0"
								>
									<img
										src={getTargetAvatar(item)}
										alt={item.targetUsername || ''}
										class="w-full h-full object-cover"
									/>
								</div>
								<div class="flex-1 min-w-0">
									<div class="flex flex-wrap items-center gap-x-2 text-sm">
										<span class="font-semibold text-slate-800 dark:text-slate-100 truncate">
											{item.targetDisplayName || item.targetUsername || '-'}
										</span>
										{#if item.targetUsername}
											<span class="text-slate-400 text-xs">@{item.targetUsername}</span>
										{/if}
									</div>
									{#if item.targetContent}
										<p
											class="text-sm text-slate-600 dark:text-slate-300 mt-1 line-clamp-3 whitespace-pre-wrap break-words"
										>
											{item.targetContent}
										</p>
									{/if}
									<div class="flex items-center gap-3 mt-2">
										{#if item.targetImageCount > 0}
											<span class="inline-flex items-center gap-1 text-xs text-slate-400">
												<ImageIcon size={13} />
												{t('admin.reports.imageCount', { count: item.targetImageCount })}
											</span>
										{/if}
										{#if href}
											<a
												{href}
												class="text-xs font-bold text-rose-600 dark:text-rose-400 hover:underline"
											>
												{t('admin.reports.viewPost')}
											</a>
										{/if}
									</div>
								</div>
							</div>
						{:else}
							<div class="flex items-center gap-3">
								<div
									class="w-9 h-9 rounded-full overflow-hidden bg-gray-200 dark:bg-zinc-700 shrink-0"
								>
									<img
										src={getTargetAvatar(item)}
										alt={item.targetUsername || ''}
										class="w-full h-full object-cover"
									/>
								</div>
								<div class="flex-1 min-w-0">
									<div class="flex flex-wrap items-center gap-x-2 text-sm">
										<span class="font-semibold text-slate-800 dark:text-slate-100 truncate">
											{item.targetDisplayName || item.targetUsername || '-'}
										</span>
										{#if item.targetUsername}
											<span class="text-slate-400 text-xs">@{item.targetUsername}</span>
										{/if}
									</div>
									{#if href}
										<a
											{href}
											class="inline-block mt-1 text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:underline"
										>
											{t('admin.reports.viewUser')}
										</a>
									{/if}
								</div>
							</div>
						{/if}
					</div>

					{#if item.note}
						<p
							class="mt-3 text-sm text-slate-600 dark:text-slate-300 whitespace-pre-wrap break-words border-l-2 border-slate-200 dark:border-zinc-700 pl-3"
						>
							{item.note}
						</p>
					{/if}
				</div>
			{/each}
		</div>

		{#if hasMore}
			<div class="flex justify-center pt-2">
				<button
					class="px-5 py-2.5 rounded-full bg-slate-800 text-white dark:bg-slate-200 dark:text-slate-900 text-sm font-bold hover:bg-slate-700 dark:hover:bg-slate-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer inline-flex items-center gap-2"
					onclick={() => load(false)}
					disabled={loadingMore}
				>
					{#if loadingMore}
						<LoaderCircle size={16} class="animate-spin" />
					{/if}
					{t('admin.reports.loadMore')}
				</button>
			</div>
		{:else}
			<div class="pb-12 pt-6 text-center text-gray-400 text-sm">
				{t('admin.reports.noMore')}
			</div>
		{/if}
	{/if}
</div>
