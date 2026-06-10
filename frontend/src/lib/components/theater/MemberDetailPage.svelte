<script lang="ts">
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { pageHeaderStore } from '$lib/stores';
	import { fade } from 'svelte/transition';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { formatDate, locale } from '$lib/i18n';
	import type { Member } from '$lib/apis/members';
	import { events as eventsApi, type MemberEventStats } from '$lib/apis/events';
	import { liveHistoryApi } from '$lib/apis/liveHistory';
	import type { Event } from '$lib/types';
	import type {
		GlobalLiveHistory,
		GlobalSingleMemberLiveHistoryStats
	} from '$lib/types/liveHistory';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import { getMemberFrame, getTeamColors } from '$lib/constants';
	import { OptimizedImage } from '$lib/components/common';
	import { parseIndonesianDate, formatDurationSeconds, formatLiveDate } from '$lib/utils/time';
	import {
		Quote,
		Instagram,
		Smartphone,
		Tv,
		Globe,
		Calendar,
		Music,
		History,
		LoaderCircle,
		Search,
		PanelLeft,
		PanelLeftClose,
		BarChart3,
		Info,
		Activity,
		Users,
		Heart,
		Flame,
		Star,
		Sprout,
		Bot
	} from 'lucide-svelte';

	import SEO from '$lib/components/SEO.svelte';

	interface Props {
		memberId: string | undefined;
		members: Member[];
		basePath: string;
	}

	let { memberId = '', members, basePath }: Props = $props();

	const { t } = useTranslation();

	let innerWidth = $state(0);
	let isSidebarVisible = $state(browser ? window.innerWidth >= 768 : true);

	let currentMember = $derived(members.find((m) => String(m.id) === memberId) || null);

	// Events
	let allEvents = $state<Event[]>([]);
	let initialLoadingEvents = $state(true);
	let loadingMoreEvents = $state(false);
	let eventPage = $state(1);
	let eventHasMore = $state(false);

	// Live History
	let allLiveHistory = $state<GlobalLiveHistory[]>([]);
	let initialLoadingLive = $state(true);
	let loadingMoreLive = $state(false);
	let livePage = $state(1);
	let liveHasMore = $state(false);

	// Stats
	let showStats = $state<MemberEventStats | null>(null);
	let liveStats = $state<GlobalSingleMemberLiveHistoryStats | null>(null);
	let loadingShowStats = $state(true);
	let loadingLiveStats = $state(true);

	let activeTab: 'Member' | 'Trainee' = $state('Member');

	function switchTab(tab: 'Member' | 'Trainee') {
		if (activeTab === tab) return;
		activeTab = tab;
		const firstInTab = members.find((m) => {
			const type = m.member_type?.toLowerCase() || 'member';
			if (tab === 'Trainee') return type === 'trainee';
			return type !== 'trainee';
		});
		if (firstInTab) {
			goto(`${basePath}/${firstInTab.id}`);
		}
	}

	function toggleSidebar() {
		isSidebarVisible = !isSidebarVisible;
	}

	$effect(() => {
		if (currentMember) {
			const type = currentMember.member_type?.toLowerCase() || 'member';
			activeTab = type === 'trainee' ? 'Trainee' : 'Member';
		}
	});

	$effect(() => {
		if (currentMember) {
			pageHeaderStore.set({
				title: currentMember.name,
				subtitle: currentMember.nickname,
				icon: Users,
				theme: 'pink',
				showBackButton: true,
				handleBack: () => goto(basePath)
			});
		}
		return () => {
			pageHeaderStore.reset();
		};
	});

	let displayMembers = $derived(
		members.filter((m) => {
			const type = m.member_type?.toLowerCase() || 'member';
			if (activeTab === 'Trainee') return type === 'trainee';
			return type !== 'trainee';
		})
	);

	let frameImg = $derived(getMemberFrame(currentMember?.member_type));

	function calculateAge(birthdateStr: string): number | string {
		const birthDate = parseIndonesianDate(birthdateStr);
		if (isNaN(birthDate.getTime())) return 'N/A';
		const diffMs = Date.now() - birthDate.getTime();
		const ageDate = new Date(diffMs);
		return Math.abs(ageDate.getUTCFullYear() - 1970);
	}

	function formatDuration(durationSeconds: number): string {
		return formatDurationSeconds(durationSeconds);
	}

	let upcomingEvents = $derived(
		allEvents
			.filter((e) => new Date(e.date) >= new Date())
			.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
	);

	let pastEvents = $derived(
		allEvents
			.filter((e) => new Date(e.date) < new Date())
			.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
	);

	let sortedEvents = $derived([...upcomingEvents, ...pastEvents]);

	const EVENT_PAGE_SIZE = 5;
	const LIVE_PAGE_SIZE = 5;

	function loadMoreEvents() {
		eventPage++;
		loadingMoreEvents = true;
		eventsApi
			.getEventsByMemberId(String(currentMember!.id), eventPage, EVENT_PAGE_SIZE)
			.then((v) => {
				allEvents = [...allEvents, ...v.data];
				eventHasMore = v.meta.next_page !== null;
			})
			.finally(() => (loadingMoreEvents = false));
	}

	function loadMoreLive() {
		livePage++;
		loadingMoreLive = true;
		liveHistoryApi
			.getGlobalMemberHistory(String(currentMember!.id), livePage, LIVE_PAGE_SIZE)
			.then((v) => {
				allLiveHistory = [...allLiveHistory, ...(v.data || [])];
				liveHasMore = v.page < v.total_pages;
			})
			.finally(() => (loadingMoreLive = false));
	}

	let liveTopPlatform = $derived(
		(() => {
			if (!liveStats?.platform_counts) return null;
			const entries = Object.entries(liveStats.platform_counts);
			if (entries.length === 0) return null;
			return entries.reduce((a, b) => (a[1] > b[1] ? a : b))[0];
		})()
	);

	async function fetchData() {
		if (!currentMember) return;

		initialLoadingEvents = true;
		initialLoadingLive = true;
		loadingShowStats = true;
		loadingLiveStats = true;
		eventPage = 1;
		livePage = 1;

		const p1 = eventsApi
			.getEventsByMemberId(String(currentMember.id), 1, EVENT_PAGE_SIZE)
			.then((v) => {
				allEvents = v.data;
				eventHasMore = v.meta.next_page !== null;
			})
			.finally(() => (initialLoadingEvents = false));
		const p2 = liveHistoryApi
			.getGlobalMemberHistory(String(currentMember.id), 1, LIVE_PAGE_SIZE)
			.then((v) => {
				allLiveHistory = v.data || [];
				liveHasMore = v.page < v.total_pages;
			})
			.finally(() => (initialLoadingLive = false));
		const p3 = eventsApi
			.getMemberEventStats(String(currentMember.id))
			.then((v) => (showStats = v))
			.finally(() => (loadingShowStats = false));
		const p4 = liveHistoryApi
			.getGlobalMemberStats(String(currentMember.id))
			.then((v) => (liveStats = v))
			.finally(() => (loadingLiveStats = false));

		await Promise.allSettled([p1, p2, p3, p4]);
	}

	$effect(() => {
		if (memberId) {
			fetchData();
		}
	});

	let mainContentEl: HTMLDivElement | undefined = $state();

	$effect(() => {
		if (memberId) {
			mainContentEl?.scrollTo({ top: 0, behavior: 'smooth' });
		}
	});
</script>

<svelte:window bind:innerWidth />

<SEO
	title={currentMember?.name || t('member.shows')}
	description={currentMember
		? `${currentMember.nickname} · ${currentMember.member_type || t('member.type.member')} · ${t('member.generation')} ${currentMember.generation}`
		: t('member.shows')}
	image={currentMember?.img ? getExternalMediaUrl(currentMember.img) : '/favicon.png'}
	path={currentMember ? `${basePath}/${memberId}` : basePath}
/>

<div
	class="h-[calc(100vh-64px)] flex flex-col bg-slate-50/50 dark:bg-zinc-900/40 overflow-hidden relative"
>
	<div class="flex-1 flex flex-col md:flex-row overflow-hidden relative">
		<!-- Mobile Sidebar Backdrop -->
		{#if isSidebarVisible && innerWidth < 768}
			<button
				onclick={toggleSidebar}
				class="fixed inset-0 bg-black/40 backdrop-blur-sm z-[55] md:hidden transition-opacity"
				aria-label={t('member.closeSidebar')}
				transition:fade={{ duration: 200 }}
			></button>
		{/if}

		<!-- Desktop Content Spacer -->
		{#if innerWidth >= 768 && members.length > 0}
			<div
				class="hidden md:block transition-all duration-300 ease-in-out shrink-0 overflow-hidden"
				style="width: {isSidebarVisible ? '256px' : '0px'}; opacity: {isSidebarVisible
					? '1'
					: '0'};"
			></div>
		{/if}

		<!-- Sidebar Drawer -->
		{#if members.length > 0}
			<div
				class="h-full overflow-hidden border-r border-gray-100 dark:border-white/5 shrink-0
					   fixed md:absolute inset-0 md:inset-y-0 md:left-0 z-[60] bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md
					   transition-transform duration-300 ease-in-out w-full md:w-64 shadow-2xl md:shadow-none
					   {isSidebarVisible ? 'translate-x-0' : '-translate-x-full'}"
			>
				<div class="w-full md:w-64 h-full flex flex-col overflow-hidden">
					<div
						class="p-4 pb-2 flex items-center justify-center relative border-b border-gray-100 dark:border-zinc-800/50 shrink-0"
					>
						<div class="flex items-center gap-2">
							<button
								class="px-4 py-2 text-[10px] font-black uppercase tracking-[0.2em] transition-all duration-300 cursor-pointer {activeTab ===
								'Member'
									? 'text-red-500 border-b-2 border-red-500'
									: 'text-gray-400 dark:text-zinc-500 hover:text-gray-600'}"
								onclick={() => switchTab('Member')}
							>
								{t('member.type.member')}
							</button>
							<button
								class="px-4 py-2 text-[10px] font-black uppercase tracking-[0.2em] transition-all duration-300 cursor-pointer {activeTab ===
								'Trainee'
									? 'text-red-500 border-b-2 border-red-500'
									: 'text-gray-400 dark:text-zinc-500 hover:text-gray-600'}"
								onclick={() => switchTab('Trainee')}
							>
								{t('member.type.trainee')}
							</button>
						</div>
						<button
							onclick={toggleSidebar}
							class="absolute right-3 top-1/2 -translate-y-1/2 p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-zinc-300 rounded-lg hover:bg-gray-100 dark:hover:bg-zinc-800 cursor-pointer"
							title={t('member.closeSidebar')}
						>
							<PanelLeftClose class="w-4 h-4" />
						</button>
					</div>
					<div class="flex-1 overflow-y-auto custom-scrollbar p-3 pt-2">
						<div class="flex flex-col gap-1.5">
							{#each displayMembers as m (m.id)}
								<button
									class="text-left px-4 py-2 rounded-2xl transition-all duration-300 group relative flex items-center justify-between cursor-pointer select-none shrink-0 {String(
										m.id
									) === memberId
										? 'bg-red-500 text-white shadow-lg shadow-red-500/20'
										: 'hover:bg-gray-100 dark:hover:bg-zinc-800/50 text-themed opacity-70 hover:opacity-100'}"
									onclick={() => {
										goto(`${basePath}/${m.id}`);
										if (innerWidth < 768) toggleSidebar();
									}}
								>
									<div class="flex items-center gap-3 whitespace-nowrap">
										{#if String(m.id) === memberId}
											<div class="w-1.5 h-1.5 rounded-full bg-white animate-pulse"></div>
										{/if}
										<span class="text-sm font-bold tracking-tight">{m.name}</span>
									</div>
								</button>
							{/each}
						</div>
					</div>
				</div>
			</div>
		{/if}

		<!-- Main Content -->
		<div class="flex-1 flex flex-col relative overflow-hidden">
			<!-- Floating Toggle Button -->
			{#if !isSidebarVisible}
				<div class="absolute top-3 left-0 z-[20]" transition:fade={{ duration: 200 }}>
					<button
						onclick={toggleSidebar}
						class="flex items-center justify-center w-8 h-10 bg-white dark:bg-zinc-900 border-y border-r border-gray-200 dark:border-white/10 rounded-r-xl shadow-lg text-gray-400 hover:text-red-500 transition-all hover:w-10 active:scale-95 cursor-pointer"
						title={t('member.showSidebar')}
					>
						<PanelLeft class="w-4 h-4 ml-1" />
					</button>
				</div>
			{/if}
			<div
				bind:this={mainContentEl}
				class="flex-1 flex flex-col overflow-y-auto md:overflow-y-auto custom-scrollbar bg-white dark:bg-zinc-900 relative pb-48 md:pb-24"
				style="overscroll-behavior: contain;"
			>
				<!-- Floating Toggle Button -->

				{#if !currentMember}
					<div
						class="flex-1 p-12 flex flex-col items-center justify-center min-h-[400px] text-center"
					>
						<div class="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
							<Search class="w-8 h-8 text-red-500" />
						</div>
						<h3 class="text-xl font-bold text-gray-900 mb-2">{t('member.notFound')}</h3>
						<p class="text-gray-500 max-w-xs mx-auto mb-6">{t('member.notFoundMessage')}</p>
					</div>
				{:else}
					<div class="w-full max-w-6xl mx-auto p-4 md:p-8 space-y-10">
						<!-- Bio Card Section -->
						<div
							class="flex flex-col md:flex-row gap-6 md:gap-8 bg-gray-50/30 dark:bg-zinc-800/20 rounded-3xl p-4 md:p-6 border border-gray-100 dark:border-zinc-800/50"
						>
							<!-- Photo -->
							<div
								class="relative w-full md:w-72 aspect-[4/5] shrink-0 rounded-2xl overflow-hidden border-[4px] border-white dark:border-zinc-800 shadow-xl bg-white dark:bg-zinc-800"
							>
								<OptimizedImage
									src={getExternalMediaUrl(currentMember.img)}
									alt={currentMember.name}
									class="w-full h-full grayscale-[10%] hover:grayscale-0 transition-all duration-700"
								/>
								<img
									src={frameImg}
									alt={t('member.memberFrame')}
									class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10 scale-[1.05]"
								/>
							</div>

							<!-- Details -->
							<div class="flex-1 space-y-5">
								<!-- Name Header -->
								<div class="space-y-1">
									<div class="flex items-center gap-3">
										<span
											class="px-2 py-0.5 rounded-md text-[10px] font-black text-white uppercase tracking-wider"
											style:background-color={getTeamColors(currentMember.member_type).badgeBg}
										>
											{currentMember.member_type || t('member.type.member')}
										</span>
										<span
											class="text-xs font-bold text-gray-400 dark:text-zinc-500 uppercase tracking-widest"
										>
											{t('member.generation')}
											{currentMember.generation}
										</span>
									</div>
									<h2
										class="text-3xl font-black text-themed tracking-tight flex items-center flex-wrap gap-2"
									>
										<span>{currentMember.name}</span>
										<span
											class="flex items-center mt-1"
											style:color={getTeamColors(currentMember.member_type).badgeText}
										>
											{#if currentMember.member_type?.toUpperCase() === 'LOVE'}
												<Heart class="w-6 h-6 fill-current" />
											{:else if currentMember.member_type?.toUpperCase() === 'PASSION'}
												<Flame class="w-6 h-6 fill-current" />
											{:else if currentMember.member_type?.toUpperCase() === 'DREAM'}
												<Star class="w-6 h-6 fill-current" />
											{:else if currentMember.member_type?.toUpperCase() === 'TRAINEE'}
												<Sprout class="w-7 h-7" />
											{:else if currentMember.member_type?.toUpperCase() === 'JKT48_VIRTUAL'}
												<Bot class="w-7 h-7" />
											{:else}
												<Star class="w-6 h-6 fill-current" />
											{/if}
										</span>
									</h2>
									<p class="text-lg font-bold text-gray-500 dark:text-zinc-400">
										({currentMember.nickname})
									</p>
								</div>

								<!-- Jikoshoukai -->
								{#if currentMember.jiko}
									<div
										class="bg-gray-50 dark:bg-zinc-800/30 p-5 rounded-[28px] relative border border-gray-100 dark:border-zinc-800/50"
									>
										<Quote
											class="w-8 h-8 text-red-500/10 dark:text-red-900/20 absolute -top-3 -left-2 transform -scale-x-100"
										/>
										<p
											class="text-sm md:text-base text-gray-700 dark:text-gray-300 italic text-center leading-relaxed font-medium"
										>
											"{currentMember.jiko}"
										</p>
									</div>
								{/if}

								<!-- Stats Grid -->
								<div class="grid grid-cols-2 gap-3">
									<div
										class="bg-gray-50/50 dark:bg-zinc-800/20 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800/50 group hover:border-red-200 dark:hover:border-red-900/30 transition-all duration-300"
									>
										<p
											class="text-[9px] font-black text-gray-400 dark:text-zinc-500 uppercase tracking-widest mb-1.5 group-hover:text-red-500 transition-colors"
										>
											{t('member.birthdate')}
										</p>
										<p class="text-sm font-black text-themed leading-tight">
											{formatDate(parseIndonesianDate(currentMember.birthdate), {
												dateStyle: 'medium'
											})}
											<span
												class="text-[10px] text-gray-500 dark:text-zinc-400 font-bold block mt-1 px-2 py-0.5 bg-gray-200/50 dark:bg-zinc-700/50 w-max rounded-full"
											>
												{calculateAge(currentMember.birthdate)}
												{t('member.yearsOld')}
											</span>
										</p>
									</div>
									<div
										class="bg-gray-50/50 dark:bg-zinc-800/20 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800/50 group hover:border-red-200 dark:hover:border-red-900/30 transition-all duration-300"
									>
										<p
											class="text-[9px] font-black text-gray-400 dark:text-zinc-500 uppercase tracking-widest mb-1.5 group-hover:text-red-500 transition-colors"
										>
											{t('member.horoscope')}
										</p>
										<p class="text-sm font-black text-themed leading-tight">
											{currentMember.horoscope}
										</p>
									</div>
									<div
										class="bg-gray-50/50 dark:bg-zinc-800/20 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800/50 group hover:border-red-200 dark:hover:border-red-900/30 transition-all duration-300"
									>
										<p
											class="text-[9px] font-black text-gray-400 dark:text-zinc-500 uppercase tracking-widest mb-1.5 group-hover:text-red-500 transition-colors"
										>
											{t('member.bloodType')}
										</p>
										<p class="text-sm font-black text-themed leading-tight">
											{currentMember.bloodType}
										</p>
									</div>
									<div
										class="bg-gray-50/50 dark:bg-zinc-800/20 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800/50 group hover:border-red-200 dark:hover:border-red-900/30 transition-all duration-300"
									>
										<p
											class="text-[9px] font-black text-gray-400 dark:text-zinc-500 uppercase tracking-widest mb-1.5 group-hover:text-red-500 transition-colors"
										>
											{t('member.height')}
										</p>
										<p class="text-sm font-black text-themed leading-tight">
											{currentMember.height?.toString().toLowerCase().includes('cm')
												? currentMember.height
												: currentMember.height + t('member.cm')}
										</p>
									</div>
								</div>

								<!-- Social Links -->
								<div class="flex items-center gap-3 flex-wrap">
									{#if currentMember.socials.twitter}
										<a
											href={currentMember.socials.twitter}
											target="_blank"
											rel="noopener noreferrer"
											aria-label={t('member.twitterProfile')}
											class="p-2.5 bg-gray-50 dark:bg-zinc-800 rounded-2xl text-gray-500 dark:text-zinc-400 hover:bg-black hover:text-white transition-all duration-500 hover:-translate-y-1 shadow-sm"
										>
											<svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"
												><path
													d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"
												/></svg
											>
										</a>
									{/if}
									{#if currentMember.socials.instagram}
										<a
											href={currentMember.socials.instagram}
											target="_blank"
											rel="noopener noreferrer"
											class="p-2.5 bg-gray-50 dark:bg-zinc-800 rounded-2xl text-gray-500 dark:text-zinc-400 hover:bg-pink-600 hover:text-white transition-all duration-500 hover:-translate-y-1 shadow-sm"
										>
											<Instagram class="w-4 h-4" />
										</a>
									{/if}
									{#if currentMember.socials.tiktok}
										<a
											href={currentMember.socials.tiktok}
											target="_blank"
											rel="noopener noreferrer"
											aria-label={t('member.tiktokProfile')}
											class="p-2.5 bg-gray-50 dark:bg-zinc-800 rounded-2xl text-gray-500 dark:text-zinc-400 hover:bg-black hover:text-white transition-all duration-500 hover:-translate-y-1 shadow-sm font-bold"
										>
											<svg class="w-4 h-4 fill-current" viewBox="0 0 24 24"
												><path
													d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.06-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.1-3.34-3.12-3.35-5.47-.03-2.43 1.4-4.71 3.61-5.7 1.11-.53 2.33-.78 3.56-.7v4.26c-.15-.05-.31-.07-.46-.09-1.49-.22-3.08.75-3.39 2.22-.2 1.05.21 2.18 1.03 2.87.89.73 2.15.8 3.2.4 1.18-.5 1.88-1.76 1.87-3.01.01-6.19-.01-12.38.01-18.57z"
												/></svg
											>
										</a>
									{/if}
									{#if currentMember.socials.idn_app}
										<a
											href={currentMember.socials.idn_app}
											target="_blank"
											rel="noopener noreferrer"
											class="p-2.5 bg-gray-50 dark:bg-zinc-800 rounded-2xl text-gray-500 dark:text-zinc-400 hover:bg-red-600 hover:text-white transition-all duration-500 hover:-translate-y-1 shadow-sm"
										>
											<Smartphone class="w-4 h-4" />
										</a>
									{/if}
									{#if currentMember.socials.showroom}
										<a
											href={currentMember.socials.showroom}
											target="_blank"
											rel="noopener noreferrer"
											class="p-2.5 bg-gray-50 dark:bg-zinc-800 rounded-2xl text-gray-500 dark:text-zinc-400 hover:bg-blue-600 hover:text-white transition-all duration-500 hover:-translate-y-1 shadow-sm"
										>
											<Tv class="w-4 h-4" />
										</a>
									{/if}
									{#if currentMember.href}
										<a
											href={currentMember.href.startsWith('http')
												? currentMember.href
												: `https://jkt48.com${currentMember.href}`}
											target="_blank"
											rel="noopener noreferrer"
											class="p-2.5 bg-gray-50 dark:bg-zinc-800 rounded-2xl text-gray-500 dark:text-zinc-400 hover:bg-red-700 hover:text-white transition-all duration-500 hover:-translate-y-1 shadow-sm"
											title={t('member.officialProfile')}><Globe class="w-4 h-4" /></a
										>
									{/if}
								</div>
							</div>
						</div>

						<!-- Stats Section -->
						<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
							<!-- Show Stats -->
							<div
								class="bg-white/60 dark:bg-zinc-900/40 rounded-3xl p-6 border border-gray-100 dark:border-zinc-800"
							>
								<div class="flex items-center gap-3 mb-5">
									<div class="h-8 w-1.5 rounded-full bg-gray-300 dark:bg-zinc-600"></div>
									<h2 class="text-lg font-bold text-themed tracking-tight flex items-center gap-2">
										<BarChart3 class="w-5 h-5 text-gray-400" />
										{t('member.showStats.title')}
										<button
											type="button"
											class="relative group flex-shrink-0 focus:outline-none"
											aria-label="Information"
										>
											<Info
												class="w-3 h-3 sm:w-3.5 sm:h-3.5 text-gray-300 cursor-help group-hover:text-red-400 group-focus:text-red-400 transition-colors"
											/>
											<div
												class="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 px-2.5 py-1 bg-gray-800 text-white text-[10px] font-medium rounded-md shadow-lg opacity-0 group-hover:opacity-100 group-focus:opacity-100 transition-all pointer-events-none z-20 w-60 text-center leading-relaxed"
											>
												{t('member.showStats.disclaimer')}
												<div
													class="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-4 border-transparent border-t-gray-800"
												></div>
											</div>
										</button>
									</h2>
								</div>
								{#if loadingShowStats}
									<div class="grid grid-cols-2 gap-3 animate-pulse">
										<div
											class="bg-white/60 dark:bg-zinc-900/40 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800 space-y-2"
										>
											<div class="h-3 bg-gray-200 dark:bg-zinc-700 rounded w-16"></div>
											<div class="h-8 bg-gray-200 dark:bg-zinc-700 rounded w-10"></div>
										</div>
										<div
											class="bg-white/60 dark:bg-zinc-900/40 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800 space-y-2"
										>
											<div class="h-3 bg-gray-200 dark:bg-zinc-700 rounded w-16"></div>
											<div class="h-8 bg-gray-200 dark:bg-zinc-700 rounded w-10"></div>
										</div>
										<div
											class="col-span-2 bg-white/60 dark:bg-zinc-900/40 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800 space-y-2"
										>
											<div class="h-3 bg-gray-200 dark:bg-zinc-700 rounded w-24"></div>
											<div class="h-5 bg-gray-200 dark:bg-zinc-700 rounded w-32"></div>
											<div class="h-4 bg-gray-200 dark:bg-zinc-700 rounded w-16"></div>
										</div>
									</div>
								{:else if showStats}
									<div class="grid grid-cols-2 gap-3">
										<div
											class="bg-white/60 dark:bg-zinc-900/40 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800"
										>
											<p class="text-[9px] font-black text-gray-500 uppercase tracking-widest mb-1">
												{t('member.showStats.totalShows')}
											</p>
											<p class="text-2xl font-black text-themed">{showStats.total_shows}</p>
										</div>
										<div
											class="bg-white/60 dark:bg-zinc-900/40 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800"
										>
											<p class="text-[9px] font-black text-gray-500 uppercase tracking-widest mb-1">
												{t('member.showStats.uniqueSetlists')}
											</p>
											<p class="text-2xl font-black text-themed">{showStats.unique_setlists}</p>
										</div>
										<div
											class="col-span-2 bg-white/60 dark:bg-zinc-900/40 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800"
										>
											<p class="text-[9px] font-black text-gray-500 uppercase tracking-widest mb-1">
												{t('member.showStats.topSetlist')}
											</p>
											<p class="text-sm font-black text-themed truncate">
												{showStats.top_setlist_title || '—'}
											</p>
											<p class="text-[11px] font-bold text-gray-500 mt-0.5">
												{showStats.top_setlist_count ?? 0}{t('member.count')}
											</p>
										</div>
									</div>
								{/if}
							</div>

							<!-- Live Stats -->
							<div
								class="bg-white/60 dark:bg-zinc-900/40 rounded-3xl p-6 border border-gray-100 dark:border-zinc-800"
							>
								<div class="flex items-center gap-3 mb-5">
									<div class="h-8 w-1.5 rounded-full bg-gray-300 dark:bg-zinc-600"></div>
									<h2 class="text-lg font-bold text-themed tracking-tight flex items-center gap-2">
										<Activity class="w-5 h-5 text-gray-400" />
										{t('member.liveStats.title')}
										<button
											type="button"
											class="relative group flex-shrink-0 focus:outline-none"
											aria-label="Information"
										>
											<Info
												class="w-3 h-3 sm:w-3.5 sm:h-3.5 text-gray-300 cursor-help group-hover:text-red-400 group-focus:text-red-400 transition-colors"
											/>
											<div
												class="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 px-2.5 py-1 bg-gray-800 text-white text-[10px] font-medium rounded-md shadow-lg opacity-0 group-hover:opacity-100 group-focus:opacity-100 transition-all pointer-events-none z-20 w-60 text-center leading-relaxed"
											>
												{t('member.liveStats.disclaimer')}
												<div
													class="absolute left-1/2 -translate-x-1/2 top-full w-0 h-0 border-4 border-transparent border-t-gray-800"
												></div>
											</div>
										</button>
									</h2>
								</div>
								{#if loadingLiveStats}
									<div class="grid grid-cols-2 gap-3 animate-pulse">
										<div
											class="bg-white/60 dark:bg-zinc-900/40 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800 space-y-2"
										>
											<div class="h-3 bg-gray-200 dark:bg-zinc-700 rounded w-16"></div>
											<div class="h-8 bg-gray-200 dark:bg-zinc-700 rounded w-10"></div>
										</div>
										<div
											class="bg-white/60 dark:bg-zinc-900/40 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800 space-y-2"
										>
											<div class="h-3 bg-gray-200 dark:bg-zinc-700 rounded w-16"></div>
											<div class="h-5 bg-gray-200 dark:bg-zinc-700 rounded w-20"></div>
										</div>
										<div
											class="bg-white/60 dark:bg-zinc-900/40 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800 space-y-2"
										>
											<div class="h-3 bg-gray-200 dark:bg-zinc-700 rounded w-16"></div>
											<div class="h-5 bg-gray-200 dark:bg-zinc-700 rounded w-12"></div>
										</div>
										<div
											class="bg-white/60 dark:bg-zinc-900/40 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800 space-y-2"
										>
											<div class="h-3 bg-gray-200 dark:bg-zinc-700 rounded w-20"></div>
											<div class="h-5 bg-gray-200 dark:bg-zinc-700 rounded w-24"></div>
										</div>
									</div>
								{:else}
									<div class="grid grid-cols-2 gap-3">
										<div
											class="bg-white/60 dark:bg-zinc-900/40 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800"
										>
											<p class="text-[9px] font-black text-gray-500 uppercase tracking-widest mb-1">
												{t('member.liveStats.totalLives')}
											</p>
											<p class="text-2xl font-black text-themed">{liveStats?.total_lives ?? 0}</p>
										</div>
										<div
											class="bg-white/60 dark:bg-zinc-900/40 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800"
										>
											<p class="text-[9px] font-black text-gray-500 uppercase tracking-widest mb-1">
												{t('member.liveStats.totalDuration')}
											</p>
											<p class="text-2xl font-black text-themed text-sm">
												{formatDuration(liveStats?.total_duration ?? 0)}
											</p>
										</div>
										<div
											class="bg-white/60 dark:bg-zinc-900/40 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800"
										>
											<p class="text-[9px] font-black text-gray-500 uppercase tracking-widest mb-1">
												{t('member.liveStats.topPlatform')}
											</p>
											<p class="text-sm font-black text-themed capitalize">
												{liveTopPlatform || '—'}
											</p>
											{#if liveTopPlatform && liveStats?.platform_counts?.[liveTopPlatform]}
												<p class="text-[11px] font-bold text-gray-500 mt-0.5">
													{liveStats.platform_counts[liveTopPlatform]}{t('member.count')}
												</p>
											{/if}
										</div>
										<div
											class="bg-white/60 dark:bg-zinc-900/40 p-4 rounded-2xl border border-gray-100 dark:border-zinc-800"
										>
											<p class="text-[9px] font-black text-gray-500 uppercase tracking-widest mb-1">
												{t('member.liveStats.longestLive')}
											</p>
											<p class="text-sm font-black text-themed truncate leading-tight">
												{liveStats?.longest_live?.live_title || '—'}
											</p>
											{#if liveStats?.longest_live}
												<p class="text-[11px] font-bold text-gray-500 mt-0.5">
													{formatDuration(liveStats.longest_live.duration)}
													{#if liveStats.longest_live.platform}
														<span class="text-gray-400 font-medium"
															>· {liveStats.longest_live.platform}</span
														>
													{/if}
												</p>
											{/if}
										</div>
									</div>
								{/if}
							</div>
						</div>

						<!-- Shows & Live Grid -->
						<div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
							<!-- Shows Section -->
							<div class="space-y-5">
								<div class="flex items-center gap-3">
									<div class="h-8 w-1.5 rounded-full bg-gray-300 dark:bg-zinc-600"></div>
									<h2 class="text-xl font-bold text-themed tracking-tight flex items-center gap-2">
										<Calendar class="w-5 h-5 text-gray-400" />
										{t('member.shows')}
									</h2>
								</div>

								{#if initialLoadingEvents}
									<div class="space-y-2 animate-pulse">
										{#each [1, 2, 3] as _}
											<div
												class="flex items-center gap-3 p-3 rounded-xl bg-gray-50/30 dark:bg-zinc-800/20 border border-gray-100 dark:border-zinc-800/50"
											>
												<div
													class="w-10 h-10 rounded-xl bg-gray-200 dark:bg-zinc-700 shrink-0"
												></div>
												<div class="flex-1 space-y-2">
													<div class="h-4 bg-gray-200 dark:bg-zinc-700 rounded w-2/3"></div>
													<div class="h-3 bg-gray-200 dark:bg-zinc-700 rounded w-1/3"></div>
												</div>
											</div>
										{/each}
									</div>
								{:else if allEvents.length === 0}
									<div
										class="text-center py-8 text-gray-500 bg-gray-50/50 dark:bg-zinc-800/20 rounded-2xl border border-dashed border-gray-100 dark:border-zinc-800"
									>
										<Music class="w-8 h-8 mx-auto mb-2 opacity-50" />
										<p class="text-sm font-medium">{t('member.eventEmpty')}</p>
									</div>
								{:else}
									<div class="space-y-2">
										{#each sortedEvents as event}
											<div
												class="flex items-center gap-3 p-3 rounded-xl bg-gray-50/30 dark:bg-zinc-800/20 border border-gray-100 dark:border-zinc-800/50 hover:border-gray-300 dark:hover:border-zinc-600 transition-all group"
											>
												<div
													class="w-10 h-10 rounded-xl overflow-hidden bg-gray-200 dark:bg-zinc-700 shrink-0"
												>
													{#if event.imageUrl}
														<img
															src={getExternalMediaUrl(event.imageUrl)}
															alt={event.title}
															class="w-full h-full object-cover"
														/>
													{:else}
														<div
															class="w-full h-full flex items-center justify-center text-gray-400"
														>
															<Music class="w-5 h-5" />
														</div>
													{/if}
												</div>
												<div class="flex-1 min-w-0">
													<p class="text-sm font-bold text-gray-800 dark:text-gray-200 break-words">
														{event.title}
													</p>
													<p class="text-[10px] font-medium text-gray-400">
														{formatDate(new Date(event.date), {
															day: 'numeric',
															month: 'short',
															year: 'numeric',
															hour: '2-digit',
															minute: '2-digit'
														})}
													</p>
												</div>
												{#if new Date(event.date) >= new Date()}
													<span
														class="px-2 py-0.5 rounded-full bg-red-500 text-white text-[9px] font-black uppercase tracking-wider shrink-0"
													>
														{t('member.upcoming')}
													</span>
												{/if}
											</div>
										{/each}
									</div>

									{#if eventHasMore}
										<div class="flex justify-center pt-2">
											<button
												onclick={loadMoreEvents}
												disabled={loadingMoreEvents}
												class="px-6 py-2.5 bg-gray-50 hover:bg-gray-100 dark:bg-zinc-800/30 dark:hover:bg-zinc-700/40 text-gray-600 dark:text-gray-400 rounded-xl font-bold text-sm transition-all active:scale-95 cursor-pointer disabled:cursor-not-allowed disabled:opacity-50 border border-gray-100 dark:border-zinc-800"
											>
												{#if loadingMoreEvents}
													<LoaderCircle class="w-4 h-4 animate-spin inline" />
												{/if}
												{t('member.loadMore')}
											</button>
										</div>
									{/if}
								{/if}
							</div>

							<!-- Live History Section -->
							<div class="space-y-5">
								<div class="flex items-center gap-3">
									<div class="h-8 w-1.5 rounded-full bg-gray-300 dark:bg-zinc-600"></div>
									<h2 class="text-xl font-bold text-themed tracking-tight flex items-center gap-2">
										<Tv class="w-5 h-5 text-gray-400" />
										{t('member.liveTitle')}
									</h2>
								</div>

								{#if initialLoadingLive}
									<div class="space-y-2 animate-pulse">
										{#each [1, 2, 3] as _}
											<div
												class="flex items-center gap-3 p-3 rounded-xl bg-gray-50/50 dark:bg-zinc-800/20 border border-gray-100 dark:border-zinc-800/50"
											>
												<div
													class="w-10 h-10 rounded-xl bg-gray-200 dark:bg-zinc-700 shrink-0"
												></div>
												<div class="flex-1 space-y-2">
													<div class="h-4 bg-gray-200 dark:bg-zinc-700 rounded w-2/3"></div>
													<div class="h-3 bg-gray-200 dark:bg-zinc-700 rounded w-1/2"></div>
												</div>
											</div>
										{/each}
									</div>
								{:else if allLiveHistory.length === 0}
									<div
										class="text-center py-8 text-gray-500 bg-gray-50/50 dark:bg-zinc-800/20 rounded-2xl border border-dashed border-gray-100 dark:border-zinc-800"
									>
										<History class="w-8 h-8 mx-auto mb-2 opacity-50" />
										<p class="text-sm font-medium">{t('member.liveEmpty')}</p>
									</div>
								{:else}
									<div class="space-y-2">
										{#each allLiveHistory as live}
											<div
												class="flex items-center gap-3 p-3 rounded-xl bg-gray-50/50 dark:bg-zinc-800/20 border border-gray-100 dark:border-zinc-800/50 hover:border-gray-300 dark:hover:border-zinc-600 transition-all group"
											>
												<div
													class="w-10 h-10 rounded-xl overflow-hidden bg-gray-200 dark:bg-zinc-700 shrink-0"
												>
													{#if live.image}
														<img
															src={getExternalMediaUrl(live.image)}
															alt={live.title || t('member.liveFallback')}
															class="w-full h-full object-cover"
														/>
													{:else}
														<div
															class="w-full h-full flex items-center justify-center text-gray-400"
														>
															<Tv class="w-5 h-5" />
														</div>
													{/if}
												</div>
												<div class="flex-1 min-w-0">
													<p class="text-sm font-bold text-gray-800 dark:text-gray-200 break-words">
														{live.title || t('member.liveFallback')}
													</p>
													<p
														class="text-[10px] font-medium text-gray-400 flex flex-col md:flex-row md:items-center gap-0.5 md:gap-0"
													>
														<span>{formatLiveDate(live.start_at, locale.value)}</span>
														{#if live.duration}
															<span
																class="md:ml-2 px-1.5 py-0.5 rounded bg-gray-200/50 dark:bg-zinc-700/50 text-[9px] font-bold text-gray-500 dark:text-zinc-400 w-fit"
															>
																{formatDuration(live.duration)}
															</span>
														{/if}
													</p>
												</div>
												<div class="flex flex-col items-end gap-1 shrink-0">
													<span
														class="px-2 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider {live.platform ===
														'showroom'
															? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
															: 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400'}"
													>
														{live.platform}
													</span>
													<span
														class="px-2 py-0.5 rounded-full bg-gray-100 dark:bg-zinc-700/50 text-[9px] font-bold text-gray-500 dark:text-zinc-400"
													>
														{live.view_num}
														{t('member.viewers')}
													</span>
												</div>
											</div>
										{/each}
									</div>

									{#if liveHasMore}
										<div class="flex justify-center pt-2">
											<button
												onclick={loadMoreLive}
												disabled={loadingMoreLive}
												class="px-6 py-2.5 bg-gray-50 hover:bg-gray-100 dark:bg-zinc-800/30 dark:hover:bg-zinc-700/40 text-gray-600 dark:text-gray-400 rounded-xl font-bold text-sm transition-all active:scale-95 cursor-pointer disabled:cursor-not-allowed disabled:opacity-50 border border-gray-100 dark:border-zinc-800"
											>
												{#if loadingMoreLive}
													<LoaderCircle class="w-4 h-4 animate-spin inline" />
												{/if}
												{t('member.loadMore')}
											</button>
										</div>
									{/if}
								{/if}
							</div>
						</div>
					</div>
				{/if}
			</div>
		</div>
	</div>
</div>

<style>
	.custom-scrollbar::-webkit-scrollbar {
		width: 4px;
	}
	.custom-scrollbar::-webkit-scrollbar-track {
		background: transparent;
	}
	.custom-scrollbar::-webkit-scrollbar-thumb {
		background: rgba(0, 0, 0, 0.1);
		border-radius: 10px;
	}
	:global(.dark) .custom-scrollbar::-webkit-scrollbar-thumb {
		background: rgba(255, 255, 255, 0.1);
	}
</style>
