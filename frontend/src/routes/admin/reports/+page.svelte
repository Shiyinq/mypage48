<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import {
		page48Api,
		type AdminReportGroup,
		type BannedUserItem,
		type BanDuration
	} from '$lib/api/page48';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { formatDate } from '$lib/i18n';
	import SEO from '$lib/components/SEO.svelte';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import ErrorState from '$lib/components/ErrorState.svelte';
	import CardSkeleton from '$lib/components/skeletons/CardSkeleton.svelte';
	import { showToast } from '$lib/stores/toast.svelte';
	import { Flag, Image as ImageIcon, LoaderCircle, Ban, Trash2, Check, X } from 'lucide-svelte';

	const { t } = useTranslation();

	type Tab = 'all' | 'post' | 'user' | 'banned';
	const TABS: Tab[] = ['all', 'post', 'user', 'banned'];

	function readTab(): Tab {
		const value = $page.url.searchParams.get('tab') as Tab | null;
		return value && TABS.includes(value) ? value : 'all';
	}
	let tab = $derived(readTab());

	type StatusFilter = 'all' | 'pending' | 'resolved' | 'dismissed';
	const STATUSES: StatusFilter[] = ['all', 'pending', 'resolved', 'dismissed'];

	function readStatus(): StatusFilter {
		const value = $page.url.searchParams.get('status') as StatusFilter | null;
		return value && STATUSES.includes(value) ? value : 'pending';
	}
	// Status defaults to `pending`, so open reports are what an admin sees first.
	let status = $derived(readStatus());

	// The reporter list in a card is capped; the rest is summarised as "+N".
	const REPORTERS_SHOWN = 3;

	let items = $state<AdminReportGroup[]>([]);
	let loading = $state(true);
	let loadingMore = $state(false);
	let error = $state<string | null>(null);
	let hasMore = $state(false);
	let nextCursor = $state<string | null>(null);
	let total = $state(0);
	let totalReports = $state(0);

	// Banned tab
	let banned = $state<BannedUserItem[]>([]);
	let bannedHasMore = $state(false);
	let bannedTotal = $state(0);

	// Ban dialog
	let banTarget = $state<AdminReportGroup | null>(null);
	let banDuration = $state<BanDuration>('permanent');
	let banReason = $state('');
	let banReasons = $state<string[]>([]);
	let banning = $state(false);

	// In-app confirm dialog (replaces window.confirm)
	type ConfirmRequest = {
		message: string;
		confirmLabel: string;
		danger: boolean;
		onConfirm: () => Promise<void>;
	};
	let confirmState = $state<ConfirmRequest | null>(null);
	let confirmBusy = $state(false);

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
				tab === 'all' || tab === 'banned' ? null : tab,
				status === 'all' ? null : status
			);
			items = reset ? response.data : [...items, ...response.data];
			hasMore = response.meta.hasMore;
			nextCursor = response.meta.nextCursor;
			total = response.meta.total;
			totalReports = response.meta.totalReports;
		} catch (err: unknown) {
			const e = err as { message?: string };
			error = e?.message || t('admin.reports.errorDesc');
			if (reset) items = [];
		} finally {
			loading = false;
			loadingMore = false;
		}
	}

	async function loadBanned(reset = false) {
		if (reset) {
			loading = true;
			banned = [];
		} else {
			if (loadingMore || !bannedHasMore) return;
			loadingMore = true;
		}
		error = null;
		try {
			const response = await page48Api.getBannedUsers(20, reset ? 0 : banned.length);
			banned = reset ? response.data : [...banned, ...response.data];
			bannedHasMore = response.meta.hasMore;
			bannedTotal = response.meta.total;
		} catch (err: unknown) {
			const e = err as { message?: string };
			error = e?.message || t('admin.reports.errorDesc');
			if (reset) banned = [];
		} finally {
			loading = false;
			loadingMore = false;
		}
	}

	// Reload whenever the tab or status changes (both driven by the URL query params).
	$effect(() => {
		const currentTab = tab;
		const currentStatus = status;
		void currentTab;
		void currentStatus;
		if (currentTab === 'banned') void loadBanned(true);
		else void load(true);
	});

	function setTab(next: Tab) {
		if (next === tab) return;
		goto(`/admin/reports?tab=${next}&status=${status}`, { keepFocus: true, noScroll: true });
	}

	function setStatus(next: StatusFilter) {
		if (next === status) return;
		goto(`/admin/reports?tab=${tab}&status=${next}`, { keepFocus: true, noScroll: true });
	}

	function getTargetHref(group: AdminReportGroup): string | null {
		if (group.targetType === 'post') return `/page48/post/${group.targetId}`;
		if (group.targetUsername) return `/page48/u/${group.targetUsername}`;
		return null;
	}

	function getTargetAvatar(group: AdminReportGroup): string {
		if (group.targetProfilePicture) return group.targetProfilePicture;
		const name = group.targetDisplayName || group.targetUsername || '?';
		return `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=fca5a5&color=fff`;
	}

	function bannedAvatar(user: BannedUserItem): string {
		if (user.profilePicture) return user.profilePicture;
		const name = user.displayName || user.username || '?';
		return `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=fca5a5&color=fff`;
	}

	function reasonLabel(reason: string): string {
		return t(`page48.report.reason.${reason}`);
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

	const tabs: { key: Tab; label: string }[] = [
		{ key: 'all', label: 'admin.reports.filters.all' },
		{ key: 'post', label: 'admin.reports.filters.post' },
		{ key: 'user', label: 'admin.reports.filters.user' },
		{ key: 'banned', label: 'admin.reports.tabs.banned' }
	];

	const statusOptions: { key: StatusFilter; label: string }[] = [
		{ key: 'all', label: 'admin.reports.filters.all' },
		{ key: 'pending', label: 'admin.reports.status.pending' },
		{ key: 'resolved', label: 'admin.reports.status.resolved' },
		{ key: 'dismissed', label: 'admin.reports.status.dismissed' }
	];

	function dropGroup(group: AdminReportGroup) {
		items = items.filter(
			(i) => !(i.targetType === group.targetType && i.targetId === group.targetId)
		);
		total = Math.max(0, total - 1);
		totalReports = Math.max(0, totalReports - group.reportCount);
	}

	function askConfirm(
		message: string,
		confirmLabel: string,
		danger: boolean,
		onConfirm: () => Promise<void>
	) {
		confirmState = { message, confirmLabel, danger, onConfirm };
	}

	async function runConfirm() {
		const request = confirmState;
		if (!request || confirmBusy) return;
		confirmBusy = true;
		try {
			await request.onConfirm();
			confirmState = null;
		} catch (err: unknown) {
			showToast((err as { message?: string })?.message || t('admin.reports.actionError'), 'error');
		} finally {
			confirmBusy = false;
		}
	}

	function deletePost(group: AdminReportGroup) {
		askConfirm(t('admin.reports.confirmDelete'), t('admin.reports.deletePost'), true, async () => {
			await page48Api.adminDeletePost(group.targetId);
			await page48Api.resolveReportGroup('post', group.targetId, 'resolved');
			dropGroup(group);
			showToast(t('admin.reports.deletedPost'), 'success');
		});
	}

	function dismiss(group: AdminReportGroup) {
		askConfirm(t('admin.reports.confirmDismiss'), t('admin.reports.dismiss'), false, async () => {
			await page48Api.resolveReportGroup(group.targetType, group.targetId, 'dismissed');
			dropGroup(group);
			showToast(t('admin.reports.dismissed'), 'success');
		});
	}

	function unban(user: BannedUserItem) {
		askConfirm(t('admin.reports.confirmUnban'), t('admin.reports.unban'), false, async () => {
			await page48Api.unbanUser(user.userId);
			banned = banned.filter((b) => b.userId !== user.userId);
			bannedTotal = Math.max(0, bannedTotal - 1);
			showToast(t('admin.reports.unbanned'), 'success');
		});
	}

	function openBan(group: AdminReportGroup) {
		banTarget = group;
		banDuration = 'permanent';
		banReasons = group.reasons;
		// Default the reason to the first report reason the reporters chose.
		banReason = group.reasons.length ? reasonLabel(group.reasons[0]) : '';
	}

	async function confirmBan() {
		if (!banTarget || banning) return;
		banning = true;
		try {
			await page48Api.banUser(
				banTarget.targetUserId ?? banTarget.targetId,
				banDuration,
				banReason.trim() || null
			);
			await page48Api.resolveReportGroup(banTarget.targetType, banTarget.targetId, 'resolved');
			dropGroup(banTarget);
			showToast(t('admin.reports.banned'), 'success');
			banTarget = null;
		} catch (err: unknown) {
			showToast((err as { message?: string })?.message || t('admin.reports.actionError'), 'error');
		} finally {
			banning = false;
		}
	}

	const durationOptions: { key: BanDuration; label: string }[] = [
		{ key: 'permanent', label: 'admin.reports.ban.durations.permanent' },
		{ key: '7d', label: 'admin.reports.ban.durations.7d' },
		{ key: '30d', label: 'admin.reports.ban.durations.30d' }
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
				{tab === 'banned'
					? t('admin.reports.bannedTitle', { count: bannedTotal })
					: t('admin.reports.title')}
				{#if tab !== 'banned'}({total}){/if}
			</h2>
			<p
				class="hidden lg:block text-slate-500 dark:text-slate-400 text-sm border-l border-gray-200 dark:border-zinc-700 pl-4 ml-2"
			>
				{tab === 'banned' ? t('admin.reports.bannedSubtitle') : t('admin.reports.subtitle')}
			</p>
		</div>

		<div class="flex flex-col items-start md:items-end gap-2">
			<div class="flex flex-wrap items-center gap-2 sm:gap-4">
				{#each tabs as item (item.key)}
					<button
						class="cursor-pointer px-4 py-2 rounded-xl text-sm font-bold transition-all border {tab ===
						item.key
							? 'bg-rose-50 text-rose-600 border-rose-200 dark:bg-rose-900/20 dark:text-rose-400 dark:border-rose-900/50'
							: 'bg-slate-50 text-slate-600 border-transparent hover:bg-slate-100 dark:bg-zinc-800/50 dark:text-slate-400 dark:hover:bg-zinc-800'}"
						onclick={() => setTab(item.key)}
					>
						{t(item.label)}
					</button>
				{/each}
			</div>
			{#if tab !== 'banned'}
				<div class="flex flex-wrap items-center gap-1.5">
					{#each statusOptions as option (option.key)}
						<button
							class="cursor-pointer px-3 py-1.5 rounded-lg text-xs font-bold transition-all border {status ===
							option.key
								? 'bg-slate-800 text-white border-slate-800 dark:bg-slate-200 dark:text-slate-900 dark:border-slate-200'
								: 'bg-white text-slate-500 border-slate-200 hover:bg-slate-100 dark:bg-zinc-800/50 dark:text-slate-400 dark:border-zinc-700 dark:hover:bg-zinc-800'}"
							onclick={() => setStatus(option.key)}
						>
							{t(option.label)}
						</button>
					{/each}
				</div>
			{/if}
		</div>
	</div>

	{#if loading}
		<div class="grid gap-4">
			{#each Array(5)}
				<CardSkeleton lines={3} />
			{/each}
		</div>
	{:else if error}
		<ErrorState
			title={t('admin.reports.errorTitle')}
			description={error}
			onRetry={() => (tab === 'banned' ? loadBanned(true) : load(true))}
		/>
	{:else if tab === 'banned'}
		{#if banned.length === 0}
			<EmptyState
				icon={Ban}
				title={t('admin.reports.bannedEmptyTitle')}
				description={t('admin.reports.bannedEmptyDesc')}
			/>
		{:else}
			<div class="grid gap-4">
				{#each banned as user (user.userId)}
					<div
						class="p-5 rounded-2xl bg-white dark:bg-zinc-900/50 border border-slate-200 dark:border-zinc-800 flex items-start gap-3"
					>
						<div
							class="w-10 h-10 rounded-full overflow-hidden bg-gray-200 dark:bg-zinc-700 shrink-0"
						>
							<img
								src={bannedAvatar(user)}
								alt={user.username || ''}
								class="w-full h-full object-cover"
							/>
						</div>
						<div class="flex-1 min-w-0">
							<div class="flex flex-wrap items-center gap-x-2 text-sm">
								<span class="font-semibold text-slate-800 dark:text-slate-100 truncate">
									{user.displayName || user.username || '-'}
								</span>
								{#if user.username}
									<span class="text-slate-400 text-xs">@{user.username}</span>
								{/if}
							</div>
							<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">
								{user.bannedUntil
									? t('admin.reports.bannedUntil', {
											date: formatDate(user.bannedUntil, {
												year: 'numeric',
												month: 'short',
												day: 'numeric'
											})
										})
									: t('admin.reports.bannedPermanent')}
								{#if user.bannedByUsername}
									· {t('admin.reports.bannedBy', { username: user.bannedByUsername })}
								{/if}
							</p>
							{#if user.reason}
								<p class="mt-1 text-sm text-slate-600 dark:text-slate-300 break-words">
									{user.reason}
								</p>
							{/if}
						</div>
						<button
							class="shrink-0 inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-emerald-50 text-emerald-600 border border-emerald-200 hover:bg-emerald-100 dark:bg-emerald-900/20 dark:text-emerald-400 dark:border-emerald-900/50 cursor-pointer transition-colors"
							onclick={() => unban(user)}
						>
							<Check size={14} />
							{t('admin.reports.unban')}
						</button>
					</div>
				{/each}
			</div>

			{#if bannedHasMore}
				<div class="flex justify-center pt-2">
					<button
						class="px-5 py-2.5 rounded-full bg-slate-800 text-white dark:bg-slate-200 dark:text-slate-900 text-sm font-bold hover:bg-slate-700 dark:hover:bg-slate-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer inline-flex items-center gap-2"
						onclick={() => loadBanned(false)}
						disabled={loadingMore}
					>
						{#if loadingMore}<LoaderCircle size={16} class="animate-spin" />{/if}
						{t('admin.reports.loadMore')}
					</button>
				</div>
			{/if}
		{/if}
	{:else if items.length === 0}
		<EmptyState
			icon={Flag}
			title={t('admin.reports.emptyTitle')}
			description={t('admin.reports.emptyDesc')}
		/>
	{:else}
		<div class="grid gap-4">
			{#each items as group (group.targetType + ':' + group.targetId)}
				{@const href = getTargetHref(group)}
				{@const shown = group.reporters.slice(0, REPORTERS_SHOWN)}
				{@const extra = group.reporters.length - shown.length}
				<div
					class="p-5 rounded-2xl bg-white dark:bg-zinc-900/50 border border-slate-200 dark:border-zinc-800"
				>
					<div class="flex flex-wrap items-center justify-between gap-2 mb-3">
						<div class="flex flex-wrap items-center gap-2">
							<span
								class="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider border {group.targetType ===
								'post'
									? 'bg-rose-50 text-rose-600 border-rose-200 dark:bg-rose-900/30 dark:text-rose-400 dark:border-rose-800/50'
									: 'bg-indigo-50 text-indigo-600 border-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-400 dark:border-indigo-800/50'}"
							>
								{group.targetType === 'post'
									? t('admin.reports.filters.post')
									: t('admin.reports.filters.user')}
							</span>
							<span
								class="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider border {getStatusStyle(
									group.status
								)}"
							>
								{t(`admin.reports.status.${group.status}`)}
							</span>
							<span
								class="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider border bg-rose-50 text-rose-600 border-rose-200 dark:bg-rose-900/30 dark:text-rose-400 dark:border-rose-800/50"
							>
								{t('admin.reports.reportCount', { count: group.reportCount })}
							</span>
							{#each group.reasons as reason (reason)}
								<span class="text-xs font-semibold text-slate-500 dark:text-slate-400">
									{reasonLabel(reason)}
								</span>
							{/each}
						</div>
						<span class="text-xs text-slate-400 font-medium whitespace-nowrap">
							{formatDate(group.latestAt, { year: 'numeric', month: 'short', day: 'numeric' })}
						</span>
					</div>

					<!-- Reporters (capped) -->
					<div class="flex flex-wrap items-center gap-1.5 mb-3">
						<span class="text-xs text-slate-400">{t('admin.reports.reportedByLabel')}</span>
						{#each shown as reporter (reporter.userId)}
							<span
								class="inline-flex items-center rounded-full bg-slate-100 dark:bg-zinc-800 px-2 py-0.5 text-xs font-semibold text-slate-600 dark:text-slate-300"
							>
								@{reporter.username || reporter.userId}
							</span>
						{/each}
						{#if extra > 0}
							<span
								class="inline-flex items-center rounded-full bg-slate-200 dark:bg-zinc-700 px-2 py-0.5 text-xs font-semibold text-slate-600 dark:text-slate-300"
								title={group.reporters.map((r) => '@' + (r.username ?? r.userId)).join(', ')}
							>
								+{extra}
							</span>
						{/if}
					</div>

					<div
						class="rounded-xl border border-slate-100 dark:border-zinc-800 bg-slate-50/60 dark:bg-zinc-800/30 p-3"
					>
						{#if !group.targetExists}
							<p class="text-sm italic text-slate-400 dark:text-slate-500">
								{t('admin.reports.deletedTarget')}
							</p>
						{:else}
							<div class="flex items-start gap-3">
								<div
									class="w-9 h-9 rounded-full overflow-hidden bg-gray-200 dark:bg-zinc-700 shrink-0"
								>
									<img
										src={getTargetAvatar(group)}
										alt={group.targetUsername || ''}
										class="w-full h-full object-cover"
									/>
								</div>
								<div class="flex-1 min-w-0">
									<div class="flex flex-wrap items-center gap-x-2 text-sm">
										<span class="font-semibold text-slate-800 dark:text-slate-100 truncate">
											{group.targetDisplayName || group.targetUsername || '-'}
										</span>
										{#if group.targetUsername}
											<span class="text-slate-400 text-xs">@{group.targetUsername}</span>
										{/if}
									</div>
									{#if group.targetContent}
										<p
											class="text-sm text-slate-600 dark:text-slate-300 mt-1 line-clamp-3 whitespace-pre-wrap break-words"
										>
											{group.targetContent}
										</p>
									{/if}
									<div class="flex items-center gap-3 mt-2">
										{#if group.targetImageCount > 0}
											<span class="inline-flex items-center gap-1 text-xs text-slate-400">
												<ImageIcon size={13} />
												{t('admin.reports.imageCount', { count: group.targetImageCount })}
											</span>
										{/if}
										{#if href}
											<a
												{href}
												target="_blank"
												rel="noopener noreferrer"
												class="text-xs font-bold text-rose-600 dark:text-rose-400 hover:underline"
											>
												{group.targetType === 'post'
													? t('admin.reports.viewPost')
													: t('admin.reports.viewUser')}
											</a>
										{/if}
									</div>
								</div>
							</div>
						{/if}
					</div>

					<!-- Admin actions -->
					<div class="mt-3 flex flex-wrap items-center gap-2">
						{#if group.targetType === 'post' && group.targetExists}
							<button
								class="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-rose-50 text-rose-600 border border-rose-200 hover:bg-rose-100 dark:bg-rose-900/20 dark:text-rose-400 dark:border-rose-900/50 cursor-pointer transition-colors"
								onclick={() => deletePost(group)}
							>
								<Trash2 size={14} />
								{t('admin.reports.deletePost')}
							</button>
						{/if}
						{#if group.targetExists}
							<button
								class="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-orange-50 text-orange-600 border border-orange-200 hover:bg-orange-100 dark:bg-orange-900/20 dark:text-orange-400 dark:border-orange-900/50 cursor-pointer transition-colors"
								onclick={() => openBan(group)}
							>
								<Ban size={14} />
								{t('admin.reports.banUser')}
							</button>
						{/if}
						<button
							class="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-slate-100 text-slate-600 border border-slate-200 hover:bg-slate-200 dark:bg-zinc-800 dark:text-slate-300 dark:border-zinc-700 cursor-pointer transition-colors"
							onclick={() => dismiss(group)}
						>
							{t('admin.reports.dismiss')}
						</button>
					</div>
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
					{#if loadingMore}<LoaderCircle size={16} class="animate-spin" />{/if}
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

<!-- Ban dialog -->
{#if banTarget}
	<div
		class="fixed inset-0 z-[1000] flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
	>
		<div
			class="w-full max-w-md rounded-3xl bg-white dark:bg-zinc-900 p-6 shadow-2xl border border-slate-100 dark:border-zinc-800"
		>
			<div class="flex items-center justify-between mb-4">
				<h3 class="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
					<Ban class="w-5 h-5 text-orange-500" />
					{t('admin.reports.ban.title')}
				</h3>
				<button
					class="p-1.5 rounded-full hover:bg-slate-100 dark:hover:bg-zinc-800 cursor-pointer"
					onclick={() => (banTarget = null)}
					aria-label={t('common.cancel')}
				>
					<X size={18} class="text-slate-500" />
				</button>
			</div>

			<p class="text-sm text-slate-500 dark:text-slate-400 mb-4">
				{t('admin.reports.ban.target', {
					username: banTarget.targetUsername || banTarget.targetDisplayName || '-'
				})}
			</p>

			<div class="mb-4">
				<span class="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
					{t('admin.reports.ban.duration')}
				</span>
				<div class="flex flex-wrap gap-2">
					{#each durationOptions as option (option.key)}
						<button
							class="px-3 py-2 rounded-xl text-sm font-bold border transition-colors cursor-pointer {banDuration ===
							option.key
								? 'bg-orange-50 text-orange-600 border-orange-300 dark:bg-orange-900/20 dark:text-orange-400 dark:border-orange-900/50'
								: 'bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100 dark:bg-zinc-800/50 dark:text-slate-400 dark:border-zinc-700'}"
							onclick={() => (banDuration = option.key)}
						>
							{t(option.label)}
						</button>
					{/each}
				</div>
			</div>

			<div class="mb-4">
				<span class="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
					{t('admin.reports.ban.reason')}
				</span>
				{#if banReasons.length > 0}
					<div class="flex flex-wrap gap-2 mb-2">
						{#each banReasons as reason (reason)}
							<button
								class="px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-zinc-800 dark:text-slate-300 cursor-pointer"
								onclick={() => (banReason = reasonLabel(reason))}
							>
								{reasonLabel(reason)}
							</button>
						{/each}
					</div>
				{/if}
				<textarea
					bind:value={banReason}
					rows="3"
					maxlength="500"
					placeholder={t('admin.reports.ban.reasonPlaceholder')}
					class="w-full px-3 py-2 rounded-xl border border-slate-200 dark:border-zinc-700 bg-slate-50 dark:bg-zinc-800 text-sm text-gray-900 dark:text-white outline-none focus:ring-2 focus:ring-orange-500 resize-none"
				></textarea>
			</div>

			<div class="flex items-center justify-end gap-2">
				<button
					class="px-4 py-2 rounded-xl text-sm font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-zinc-800 cursor-pointer"
					onclick={() => (banTarget = null)}
					disabled={banning}
				>
					{t('common.cancel')}
				</button>
				<button
					class="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-bold bg-orange-500 text-white hover:bg-orange-600 disabled:opacity-50 cursor-pointer"
					onclick={confirmBan}
					disabled={banning}
				>
					{#if banning}<LoaderCircle size={15} class="animate-spin" />{/if}
					{t('admin.reports.ban.confirm')}
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- Confirm dialog (replaces window.confirm) -->
{#if confirmState}
	<div
		class="fixed inset-0 z-[1000] flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm"
	>
		<div
			class="w-full max-w-sm rounded-3xl bg-white dark:bg-zinc-900 p-6 shadow-2xl border border-slate-100 dark:border-zinc-800"
		>
			<p class="text-sm text-gray-800 dark:text-gray-100 whitespace-pre-wrap break-words">
				{confirmState.message}
			</p>
			<div class="mt-5 flex items-center justify-end gap-2">
				<button
					class="px-4 py-2 rounded-xl text-sm font-bold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-zinc-800 cursor-pointer"
					onclick={() => (confirmState = null)}
					disabled={confirmBusy}
				>
					{t('common.cancel')}
				</button>
				<button
					class="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-bold text-white disabled:opacity-50 cursor-pointer {confirmState.danger
						? 'bg-rose-600 hover:bg-rose-700'
						: 'bg-slate-800 hover:bg-slate-700 dark:bg-slate-200 dark:text-slate-900 dark:hover:bg-slate-300'}"
					onclick={runConfirm}
					disabled={confirmBusy}
				>
					{#if confirmBusy}<LoaderCircle size={15} class="animate-spin" />{/if}
					{confirmState.confirmLabel}
				</button>
			</div>
		</div>
	</div>
{/if}
