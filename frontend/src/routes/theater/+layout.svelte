<script lang="ts">
	import { page } from '$app/stores';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { AudioLines, Users, Calendar, Newspaper, ArrowUpDown, Tv } from 'lucide-svelte';
	import PageHeader from '$lib/components/PageHeader.svelte';
	interface Props {
		children?: import('svelte').Snippet;
	}

	let { children }: Props = $props();

	const { t } = useTranslation();

	let currentPath = $derived($page.url.pathname);

	// Check if on live single detail or multiview page — hide header for immersive player
	let isLiveDetailPage = $derived(/^\/theater\/live\/.+/.test(currentPath));

	// Check if on news detail page
	let isNewsDetailPage = $derived(/^\/theater\/news\/.+/.test(currentPath));

	// Check if on setlist detail page
	let isDetailPage = $derived(
		(() => {
			const parts = currentPath.split('/').filter(Boolean);
			if (parts.length !== 2 || parts[0] !== 'theater') return false;
			return !['news', 'members', 'sorter', 'events', 'live'].includes(parts[1]);
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
			if (currentPath.includes('/theater/sorter')) {
				return {
					title: t('theater.sorter.title'),
					subtitle: t('theater.sorter.subtitle'),
					icon: ArrowUpDown,
					theme: 'rose' as PageTheme
				};
			}
			if (currentPath.includes('/theater/events/history')) {
				return {
					title: t('theater.eventHistory.title') || 'Event History',
					subtitle: t('theater.eventHistory.subtitle') || 'Past events',
					icon: Calendar,
					theme: 'orange' as PageTheme
				};
			}
			if (currentPath.includes('/theater/events')) {
				return {
					title: t('theater.events.title') || 'Events',
					subtitle: t('theater.events.subtitle') || 'Browse theater events',
					icon: Calendar,
					theme: 'blue' as PageTheme
				};
			}
			if (currentPath.includes('/theater/live')) {
				return {
					title: 'JKT48 LIVE',
					subtitle: t('theater.live.subtitle'),
					icon: Tv,
					theme: 'red' as PageTheme
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
</script>

<div
	class="{isLiveDetailPage || isNewsDetailPage || isDetailPage
		? 'max-w-5xl'
		: 'max-w-6xl'} mx-auto {isLiveDetailPage
		? 'pt-0 sm:pt-0 px-1.5 sm:px-4'
		: 'pt-4 sm:pt-6 px-4'} pb-24"
>
	<!-- Unified Page Header (Standard or Background Live Sync) -->
	<PageHeader
		title={isLiveDetailPage ? 'JKT48 LIVE' : pageInfo.title}
		subtitle={isLiveDetailPage ? '' : pageInfo.subtitle}
		icon={isLiveDetailPage ? Tv : pageInfo.icon}
		theme={isLiveDetailPage ? 'red' : pageInfo.theme}
		showBackButton={isLiveDetailPage || isNewsDetailPage || isDetailPage}
		backUrl={isNewsDetailPage
			? '/theater/news'
			: isLiveDetailPage
				? '/theater/live'
				: isDetailPage
					? '/theater'
					: undefined}
		hidden={isLiveDetailPage}
	></PageHeader>
	{#if !isLiveDetailPage}
		<div class="mb-4 sm:mb-6"></div>
	{/if}

	<!-- Page Content -->
	{@render children?.()}
</div>
