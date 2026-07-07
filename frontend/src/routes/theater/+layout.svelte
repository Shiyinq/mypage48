<script lang="ts">
	import { page } from '$app/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { AudioLines, Users, Newspaper } from 'lucide-svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	import { isImmersive } from '$lib/stores';
	import { newsStore } from '$lib/stores/news.svelte';

	interface Props {
		children?: import('svelte').Snippet;
	}

	let { children }: Props = $props();

	const { t } = useTranslation();

	let currentPath = $derived($page.url.pathname);
	let isTheaterRoot = $derived(currentPath === '/theater');

	// Check if on news detail page
	let isNewsDetailPage = $derived(/^\/theater\/news\/.+/.test(currentPath));

	// Check if on news listing page
	let isNewsListingPage = $derived(currentPath === '/theater/news');

	// Check if on events listing page
	let isEventsListingPage = $derived(currentPath === '/theater/events');

	// Check if on events history page
	let isEventsHistoryPage = $derived(currentPath === '/theater/events/history');

	// Check if on members page
	let isMembersPage = $derived(currentPath === '/theater/members');

	// Check if on member detail page
	let isMembersDetailPage = $derived(
		currentPath.startsWith('/theater/members/') && !isNewsListingPage && !isMembersPage
	);

	// Check if on event detail page
	let isEventDetailPage = $derived(
		currentPath.startsWith('/theater/events/') &&
			!isEventsHistoryPage &&
			currentPath !== '/theater/events/calendar' &&
			currentPath !== '/theater/events'
	);

	// Check if on setlist detail page
	let isDetailPage = $derived(
		(() => {
			const parts = currentPath.split('/').filter(Boolean);
			if (parts.length !== 2 || parts[0] !== 'theater') return false;
			return !['news', 'members', 'events'].includes(parts[1]);
		})()
	);

	type PageTheme =
		| 'red'
		| 'blue'
		| 'green'
		| 'purple'
		| 'pink'
		| 'amber'
		| 'yellow'
		| 'orange'
		| 'rose'
		| 'indigo';

	// Dynamic Title, Subtitle & Theme
	let pageInfo = $derived(
		(() => {
			if (currentPath.includes('/theater/news')) {
				return {
					title: t('theater.news.title') || 'News',
					subtitle: t('theater.news.subtitle') || 'Latest updates and announcements',
					icon: Newspaper,
					theme: 'red' as PageTheme
				};
			}
			if (currentPath.includes('/theater/members')) {
				return {
					title: t('theater.members.title'),
					subtitle: t('theater.members.subtitle'),
					icon: Users,
					theme: 'pink' as PageTheme
				};
			}
			return {
				title: t('theater.title'),
				subtitle: t('theater.subtitle'),
				icon: AudioLines,
				theme: 'purple' as PageTheme
			};
		})()
	);

	let actionItems = $derived([]);
	let isHeaderHidden = $derived(
		isImmersive.value ||
			isTheaterRoot ||
			isDetailPage ||
			isEventsHistoryPage ||
			isEventsListingPage ||
			isNewsListingPage ||
			isMembersPage ||
			isMembersDetailPage ||
			isEventDetailPage ||
			isNewsDetailPage
	);
</script>

<div
	class="{isImmersive.value ||
	isMembersDetailPage ||
	isEventDetailPage ||
	isDetailPage ||
	isNewsDetailPage
		? 'max-w-none w-full'
		: 'max-w-6xl'} mx-auto {isImmersive.value ||
	isMembersDetailPage ||
	isEventDetailPage ||
	isDetailPage ||
	isNewsDetailPage
		? 'pt-0 sm:pt-0 px-0'
		: 'pt-4 sm:pt-6 px-4'} {isImmersive.value
		? 'pb-0'
		: isMembersDetailPage || isEventDetailPage || isDetailPage || isNewsDetailPage
			? 'pb-0'
			: 'pb-24'}"
>
	<!-- Unified Page Header (Standard or Background Live Sync) -->
	<PageHeader
		title={pageInfo.title}
		subtitle={pageInfo.subtitle}
		icon={pageInfo.icon}
		theme={pageInfo.theme}
		{actionItems}
		showBackButton={isNewsDetailPage || isDetailPage}
		backUrl={isNewsDetailPage
			? `/theater/news${newsStore.pagination.current_page > 1 ? `?page=${newsStore.pagination.current_page}` : ''}`
			: isDetailPage
				? '/theater'
				: undefined}
		hidden={isHeaderHidden}
	></PageHeader>
	{#if !isHeaderHidden}
		<div class="mb-0 sm:mb-6"></div>
	{/if}

	<!-- Page Content -->
	{@render children?.()}
</div>
