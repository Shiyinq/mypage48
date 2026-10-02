<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { fade } from 'svelte/transition';
	import { BellOff } from 'lucide-svelte';
	import { page48Api, type Page48Notification, type Page48NotificationTab } from '$lib/api/page48';
	import NotificationRow from '$lib/components/page48/NotificationRow.svelte';
	import Page48Spinner from '$lib/components/page48/Page48Spinner.svelte';
	import { ErrorState } from '$lib/components';
	import SEO from '$lib/components/SEO.svelte';
	import {
		page48NavbarStore,
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

	// The active tab lives in the URL, so a shared link opens the same tab.
	let activeTab = $derived.by<Page48NotificationTab>(() => {
		const raw = $page.url.searchParams.get('tab');
		return (TABS as string[]).includes(raw ?? '') ? (raw as Page48NotificationTab) : 'replies';
	});

	let items = $state<Page48Notification[]>([]);
	let cursor = $state<string | null>(null);
	let hasMore = $state(false);
	let loading = $state(true);
	let loadingMore = $state(false);
	let failed = $state(false);

	// Reload from the top whenever the tab changes (it is read from the URL).
	$effect(() => {
		void activeTab;
		void load(true);
	});

	async function load(reset: boolean) {
		if (reset) {
			loading = true;
			failed = false;
			items = [];
			cursor = null;
			hasMore = false;
		}

		const requestCursor = reset ? null : cursor;
		try {
			const response = await page48Api.getNotifications(activeTab, PAGE_SIZE, requestCursor);
			items = reset ? response.data : [...items, ...response.data];
			cursor = response.meta.nextCursor;
			hasMore = response.meta.hasMore;
			if (reset) void markTabRead(activeTab);
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
		void load(false);
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
			await refreshPage48Unread();
		} catch {
			// The counts simply keep their last values.
		}
	}

	function selectTab(tab: Page48NotificationTab) {
		if (tab === activeTab) return;
		const url = tab === 'replies' ? '/page48/notifications' : `/page48/notifications?tab=${tab}`;
		void goto(url, { keepFocus: true, noScroll: true });
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
	<div class="flex border-b border-gray-200/60 dark:border-white/10" role="tablist">
		{#each TABS as tab (tab)}
			<button
				role="tab"
				aria-selected={activeTab === tab}
				onclick={() => selectTab(tab)}
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
				onRetry={() => load(true)}
			/>
		</div>
	{:else if items.length === 0}
		<div class="flex flex-col items-center gap-3 p-12 text-center text-gray-500 dark:text-gray-400">
			<BellOff size={28} />
			<p class="text-[14px]">{t('page48.notifications.empty')}</p>
		</div>
	{:else}
		<div
			class="flex flex-col divide-y divide-gray-100 dark:divide-white/5"
			in:fade={{ duration: 200 }}
		>
			{#each items as item (item.notificationId)}
				<NotificationRow notification={item} />
			{/each}
		</div>

		{#if loadingMore}
			<div class="p-4 flex justify-center">
				<Page48Spinner />
			</div>
		{/if}
	{/if}
</div>
