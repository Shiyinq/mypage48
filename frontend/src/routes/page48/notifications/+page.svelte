<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { fade } from 'svelte/transition';
	import { BellOff, ChevronRight } from 'lucide-svelte';
	import {
		page48Api,
		type Page48Notification,
		type Page48NotificationOverview,
		type Page48NotificationTab
	} from '$lib/api/page48';
	import NotificationRow from '$lib/components/page48/NotificationRow.svelte';
	import Page48Spinner from '$lib/components/page48/Page48Spinner.svelte';
	import {
		NOTIFICATION_ACTION_KEYS,
		NOTIFICATION_TAB_ICONS
	} from '$lib/components/page48/notificationMeta';
	import ErrorState from '$lib/components/ErrorState.svelte';
	import SEO from '$lib/components/SEO.svelte';
	import {
		applyPage48Counts,
		page48NavbarStore,
		page48Reads,
		page48UnreadStore,
		refreshPage48Unread
	} from '$lib/stores/page48.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	const PAGE_SIZE = 20;
	const TABS: Page48NotificationTab[] = ['replies', 'mentions', 'likes', 'reposts', 'follows'];

	onMount(() => {
		page48NavbarStore.pageType = 'notifications';
	});

	/** No `?tab=` means the overview; a tab means the notification list. */
	let tabParam = $derived($page.url.searchParams.get('tab'));

	let activeTab = $derived.by<Page48NotificationTab>(() =>
		(TABS as string[]).includes(tabParam ?? '') ? (tabParam as Page48NotificationTab) : 'replies'
	);

	let overview = $state<Page48NotificationOverview | null>(null);
	let overviewLoading = $state(true);
	let overviewFailed = $state(false);

	let items = $state<Page48Notification[]>([]);
	let cursor = $state<string | null>(null);
	let hasMore = $state(false);
	let loading = $state(false);
	let loadingMore = $state(false);
	let failed = $state(false);

	// The URL decides everything, so back and forward work as expected.
	$effect(() => {
		const tab = tabParam;
		if (!tab) {
			void loadOverview();
			return;
		}
		void load(activeTab, true);
	});

	async function loadOverview() {
		overviewLoading = true;
		overviewFailed = false;
		try {
			const response = await page48Reads.getNotificationOverview();
			overview = response;
			// The overview already carries the counts, so the bell can use them
			// instead of asking for the same numbers again.
			applyPage48Counts({
				total: response.total,
				replies: countsFor(response, 'replies'),
				mentions: countsFor(response, 'mentions'),
				likes: countsFor(response, 'likes'),
				reposts: countsFor(response, 'reposts'),
				follows: countsFor(response, 'follows')
			});
		} catch {
			overviewFailed = true;
		} finally {
			overviewLoading = false;
		}
	}

	function countsFor(response: Page48NotificationOverview, tab: Page48NotificationTab): number {
		return response.tabs.find((section) => section.tab === tab)?.count ?? 0;
	}

	async function load(tab: Page48NotificationTab, reset: boolean) {
		if (reset) {
			loading = true;
			failed = false;
			items = [];
			cursor = null;
			hasMore = false;
		}

		const requestCursor = reset ? null : cursor;
		try {
			const response = await page48Reads.getNotifications(tab, PAGE_SIZE, requestCursor);
			items = reset ? response.data : [...items, ...response.data];
			cursor = response.meta.nextCursor;
			hasMore = response.meta.hasMore;
			if (reset) void markTabRead(tab);
		} catch {
			if (reset) failed = true;
		} finally {
			loading = false;
			loadingMore = false;
		}
	}

	function loadMore() {
		if (loading || loadingMore || !hasMore) return;
		loadingMore = true;
		void load(activeTab, false);
	}

	function handleScroll() {
		const scrollY = window.scrollY;
		const innerHeight = window.innerHeight;
		const offsetHeight = document.body.offsetHeight;

		if (scrollY + innerHeight >= offsetHeight - 500) {
			loadMore();
		}
	}

	/**
	 * Opening a tab marks that tab read, so the other tabs keep their unread count
	 * until they are opened too. The rows keep the dot from this fetch.
	 */
	async function markTabRead(tab: Page48NotificationTab) {
		try {
			await page48Api.markNotificationsRead(tab);
			await refreshPage48Unread(true);
		} catch {
			// The counts simply keep their last values.
		}
	}

	function tabHref(tab: Page48NotificationTab): string {
		return `/page48/notifications?tab=${tab}`;
	}
</script>

<svelte:window onscroll={handleScroll} />

<SEO
	title={t('page48.notifications.title')}
	path="/page48/notifications"
	description={t('page48.seo.postDesc')}
/>

<div
	class="max-w-[620px] mx-auto w-full min-h-screen bg-white/70 dark:bg-zinc-950/70 backdrop-blur-3xl sm:border-x border-gray-200/60 dark:border-white/10 pb-24 shadow-sm shadow-black/5 dark:shadow-none transition-all"
>
	{#if !tabParam}
		<!-- Overview: one row per tab, with its count and a preview -->
		{#if overviewLoading}
			<div class="flex flex-col divide-y divide-gray-100 dark:divide-white/5">
				{#each TABS as _}
					<div class="flex animate-pulse items-center gap-3 px-5 py-4 sm:px-6">
						<div class="h-9 w-9 shrink-0 rounded-full bg-gray-200/80 dark:bg-zinc-800"></div>
						<div class="flex-1 space-y-2">
							<div class="h-4 w-1/3 rounded bg-gray-200 dark:bg-zinc-800"></div>
							<div class="h-3.5 w-2/3 rounded bg-gray-200 dark:bg-zinc-800"></div>
						</div>
					</div>
				{/each}
			</div>
		{:else if overviewFailed}
			<div class="p-6">
				<ErrorState
					title={t('page48.notifications.loadError')}
					description={t('page48.notifications.loadErrorText')}
					onRetry={loadOverview}
				/>
			</div>
		{:else if overview}
			<div class="flex flex-col divide-y divide-gray-100 dark:divide-white/5">
				{#each overview.tabs as section (section.tab)}
					{@const Icon = NOTIFICATION_TAB_ICONS[section.tab]}
					<a
						href={tabHref(section.tab)}
						class="flex items-center gap-3 px-5 py-4 transition-colors hover:bg-gray-50 dark:hover:bg-white/5 sm:px-6"
					>
						<span
							class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-red-50 text-red-600 dark:bg-red-950/30 dark:text-red-400"
						>
							<Icon size={17} />
						</span>

						<div class="min-w-0 flex-1">
							<div class="flex items-center gap-2">
								<span class="text-[14px] font-semibold text-gray-900 dark:text-gray-100">
									{t(`page48.notifications.tab.${section.tab}`)}
								</span>
								{#if section.count > 0}
									<span
										class="inline-flex h-4 min-w-[16px] items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-bold leading-none tabular-nums text-white"
									>
										{section.count > 99 ? '99+' : section.count}
									</span>
								{/if}
							</div>

							<div class="mt-0.5 space-y-0.5">
								{#each section.previews as preview (preview.notificationId)}
									<p class="truncate text-[13px] text-gray-500 dark:text-gray-400">
										<span class="font-medium text-gray-700 dark:text-gray-300">
											{preview.actor.name}
										</span>
										{t(NOTIFICATION_ACTION_KEYS[preview.type])}
									</p>
								{/each}
							</div>
						</div>

						<ChevronRight size={18} class="shrink-0 text-gray-400" />
					</a>
				{/each}
			</div>
		{/if}
	{:else}
		<!-- One tab: the notification list, with the tabs to switch between them -->
		<div class="flex border-b border-gray-200/60 pt-3 dark:border-white/10" role="tablist">
			{#each TABS as tab (tab)}
				<button
					role="tab"
					aria-selected={activeTab === tab}
					onclick={() => goto(tabHref(tab), { keepFocus: true, noScroll: true })}
					class={`-mb-px flex-1 cursor-pointer whitespace-nowrap border-b-2 px-1.5 py-3 text-[12px] font-semibold transition-colors sm:px-2 sm:text-[13px] ${
						activeTab === tab
							? 'border-red-600 text-red-600 dark:border-red-400 dark:text-red-400'
							: 'border-transparent text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200'
					}`}
				>
					{t(`page48.notifications.tab.${tab}`)}
					{#if page48UnreadStore[tab] > 0}
						<span
							class="ml-1 inline-flex h-4 min-w-[16px] items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-bold leading-none tabular-nums text-white"
						>
							{page48UnreadStore[tab] > 99 ? '99+' : page48UnreadStore[tab]}
						</span>
					{/if}
				</button>
			{/each}
		</div>

		{#if loading}
			<div class="divide-y divide-gray-100 dark:divide-white/5">
				{#each Array(6) as _}
					<div class="flex animate-pulse gap-3 px-5 py-3.5 sm:px-6">
						<div class="h-10 w-10 shrink-0 rounded-full bg-gray-200/80 dark:bg-zinc-800"></div>
						<div class="flex-1 space-y-2 py-0.5">
							<div class="h-4 w-1/3 rounded bg-gray-200 dark:bg-zinc-800"></div>
							<div class="h-3.5 w-2/3 rounded bg-gray-200 dark:bg-zinc-800"></div>
						</div>
					</div>
				{/each}
			</div>
		{:else if failed}
			<div class="p-6">
				<ErrorState
					title={t('page48.notifications.loadError')}
					description={t('page48.notifications.loadErrorText')}
					onRetry={() => load(activeTab, true)}
				/>
			</div>
		{:else if items.length === 0}
			<div
				class="flex flex-col items-center gap-3 p-12 text-center text-gray-500 dark:text-gray-400"
			>
				<BellOff size={28} />
				<p class="text-[14px]">{t('page48.notifications.empty')}</p>
			</div>
		{:else}
			<div
				class="flex flex-col divide-y divide-gray-100 dark:divide-white/5"
				in:fade={{ duration: 200 }}
			>
				{#each items as item (item.notificationId)}
					<NotificationRow
						notification={item}
						onResolved={(id) => (items = items.filter((n) => n.notificationId !== id))}
					/>
				{/each}
			</div>

			{#if loadingMore}
				<div class="p-4 flex justify-center">
					<Page48Spinner />
				</div>
			{/if}
		{/if}
	{/if}
</div>
