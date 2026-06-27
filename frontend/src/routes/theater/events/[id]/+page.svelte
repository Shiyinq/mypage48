<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { pageHeaderStore } from '$lib/stores';
	import { browser } from '$app/environment';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { OptimizedImage, ImageLightbox } from '$lib/components/common';
	import { formatDate } from '$lib/i18n';
	import { fade } from 'svelte/transition';
	import {
		Calendar,
		Clock,
		Users,
		Ticket,
		ExternalLink,
		Cake,
		GraduationCap,
		PanelLeft,
		PanelLeftClose,
		Heart,
		Star,
		Flame,
		Sprout,
		ZoomIn
	} from 'lucide-svelte';
	import { getMemberFrame } from '$lib/constants';
	import { getTeamColors } from '$lib/constants/teamColors';
	import { eventsStore, upcomingEvents, isUpcomingEventsLoading } from '$lib/stores/events.svelte';

	const { t } = useTranslation();

	function getTeamIcon(label: string) {
		if (!label) return null;
		const l = label.toUpperCase();
		if (l === 'LOVE') return Heart;
		if (l === 'DREAM') return Star;
		if (l === 'PASSION' || l === 'SESSION') return Flame;
		if (l === 'TRAINEE') return Sprout;
		return null;
	}

	let eventId = $derived($page.params.id || '');
	let event = $derived(eventsStore.detailCache[eventId]);
	let isLightboxOpen = $state(false);

	let heroImageUrl = $derived.by(() => {
		if (!event) return null;
		if (event.imageUrl) return event.imageUrl;
		if (event.type === 'EXCLUSIVE' && event.raw_data?.detail?.thumbnail_image) {
			return `/proxy/image?url=${encodeURIComponent(event.raw_data.detail.thumbnail_image)}`;
		}
		return null;
	});

	let innerWidth = $state(0);
	let isSidebarVisible = $state(browser ? window.innerWidth >= 768 : true);

	// Fetch Data
	$effect(() => {
		if (eventId) {
			eventsStore.loadDetail(eventId);
			eventsStore.loadUpcoming();
		}
	});

	$effect(() => {
		if (event) {
			pageHeaderStore.set({
				title: event.title,
				subtitle: formatDate(event.date, {
					weekday: 'long',
					day: 'numeric',
					month: 'long',
					year: 'numeric'
				}),
				icon: Calendar,
				theme: 'pink',
				showBackButton: true,
				handleBack: () => goto('/theater/events')
			});
		} else {
			pageHeaderStore.set({
				title: t('theater.events.title') || 'Theater Events',
				icon: Calendar,
				theme: 'pink',
				showBackButton: true,
				handleBack: () => goto('/theater/events')
			});
		}
		return () => pageHeaderStore.reset();
	});

	// Mobile behavior
	$effect(() => {
		if (innerWidth < 768) {
			isSidebarVisible = false;
		} else {
			isSidebarVisible = true;
		}
	});

	function toggleSidebar() {
		isSidebarVisible = !isSidebarVisible;
	}

	let hasSales = $derived(
		event?.raw_data?.detail?.sales_period && event.raw_data.detail.sales_period.length > 0
	);
	let contentBody = $derived(
		event?.raw_data?.detail?.content_body || event?.raw_data?.short?.content_body
	);

	let mainContentEl: HTMLElement | undefined = $state();

	$effect(() => {
		if (eventId) {
			mainContentEl?.scrollTo({ top: 0, behavior: 'smooth' });
		}
	});
</script>

<svelte:window bind:innerWidth />

{#if event}
	<SEO title={event.title} path={`/theater/events/${event.id}`} description={event.title} />
{:else}
	<SEO title="Loading..." path={`/theater/events/${eventId}`} description="Loading Event" />
{/if}

<div
	class="h-[calc(100vh-64px)] flex flex-col bg-slate-50/50 dark:bg-zinc-900/40 overflow-hidden relative"
>
	<div class="flex-1 flex flex-col md:flex-row overflow-hidden relative">
		<!-- Mobile Sidebar Backdrop -->
		{#if isSidebarVisible && innerWidth < 768}
			<button
				onclick={toggleSidebar}
				class="fixed inset-0 bg-black/40 backdrop-blur-sm z-[55] md:hidden transition-opacity"
				aria-label="Close Sidebar"
				transition:fade={{ duration: 200 }}
			></button>
		{/if}

		<!-- Desktop Content Spacer -->
		{#if innerWidth >= 768}
			<div
				class="hidden md:block transition-all duration-300 ease-in-out shrink-0 overflow-hidden"
				style="width: {isSidebarVisible ? '256px' : '0px'}; opacity: {isSidebarVisible
					? '1'
					: '0'};"
			></div>
		{/if}

		<!-- Sidebar Container -->
		<aside
			class="fixed md:absolute top-0 bottom-0 left-0 z-[60] md:z-10 bg-white md:bg-white/80 dark:bg-zinc-900 md:dark:bg-zinc-900/80 backdrop-blur-md border-r border-gray-100 dark:border-white/5 shadow-2xl md:shadow-none w-full md:w-64 transition-transform duration-300 ease-in-out flex flex-col"
			class:-translate-x-full={!isSidebarVisible}
			class:translate-x-0={isSidebarVisible}
		>
			<!-- Sidebar Header -->
			<div
				class="relative p-4 border-b border-gray-100 dark:border-zinc-800/50 shrink-0 bg-white/95 dark:bg-zinc-900/95 backdrop-blur z-10"
			>
				<div class="flex items-center justify-between">
					<h2 class="font-bold text-gray-900 dark:text-white flex items-center gap-2">
						<div class="w-1.5 h-4 bg-red-500 rounded-full"></div>
						{t('theater.upcomingEvents.title')}
					</h2>
					<button
						onclick={toggleSidebar}
						class="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-zinc-300 rounded-lg hover:bg-gray-100 dark:hover:bg-zinc-800 cursor-pointer"
						title={t('theater.closeSidebar') || 'Close sidebar'}
					>
						<PanelLeftClose class="w-4 h-4" />
					</button>
				</div>
			</div>

			<!-- Event List -->
			<div
				class="flex-1 overflow-y-auto custom-scrollbar p-3 pt-2 pb-28"
				style="overscroll-behavior: contain;"
			>
				{#if isUpcomingEventsLoading.value}
					<div class="space-y-3">
						{#each Array(5)}
							<div class="w-full h-20 rounded-xl bg-gray-100 dark:bg-zinc-800 animate-pulse"></div>
						{/each}
					</div>
				{:else}
					<div class="space-y-2">
						{#each upcomingEvents.value as e}
							{@const isActive = eventId === String(e.id)}
							<a
								href={`/theater/events/${e.id}`}
								class="w-full cursor-pointer group flex items-start p-2.5 rounded-xl transition-all duration-200 border {isActive
									? 'bg-red-50 dark:bg-red-500/10 border-red-200 dark:border-red-500/30'
									: 'border-transparent hover:bg-slate-100 dark:hover:bg-zinc-800/50'}"
								onclick={() => {
									if (innerWidth < 768) isSidebarVisible = false;
								}}
							>
								<div class="flex-1 text-left">
									<h3
										class="font-semibold text-sm line-clamp-2 {isActive
											? 'text-red-700 dark:text-red-400'
											: 'text-gray-900 dark:text-gray-200 group-hover:text-red-600 dark:group-hover:text-red-400'}"
									>
										{e.title}
									</h3>
									<div
										class="flex items-center gap-1 mt-1 text-xs text-gray-500 dark:text-gray-400"
									>
										<Calendar class="w-3 h-3" />
										<span>{formatDate(e.date, { day: 'numeric', month: 'short' })}</span>
									</div>
								</div>
							</a>
						{/each}
					</div>
				{/if}
			</div>
		</aside>

		<!-- Floating Toggle Sidebar Button -->
		{#if !isSidebarVisible}
			<div
				class="absolute top-3 left-0 z-30 transition-all duration-300"
				transition:fade={{ duration: 200 }}
			>
				<button
					onclick={toggleSidebar}
					class="flex items-center justify-center w-8 h-10 bg-white/90 dark:bg-zinc-900/90 backdrop-blur-md shadow-lg border-y border-r border-gray-200 dark:border-white/10 rounded-r-xl text-gray-400 hover:text-red-500 transition-all hover:w-10 active:scale-95 cursor-pointer"
					title={t('common.openSidebar')}
				>
					<PanelLeft class="w-4 h-4 ml-1" />
				</button>
			</div>
		{/if}

		<!-- Main Content Area -->
		<main
			bind:this={mainContentEl}
			class="flex-1 overflow-y-auto relative h-full custom-scrollbar bg-white dark:bg-zinc-900"
			style="overscroll-behavior: contain;"
		>
			<!-- Event Detail Content -->
			<div class="pb-12 max-w-none w-full mx-auto">
				{#if event}
					<!-- Unified Card Container -->
					<div class="bg-white dark:bg-zinc-900 overflow-hidden">
						{#snippet heroContent({ isDarkText = false }: { isDarkText?: boolean })}
							<div class="flex flex-wrap gap-2 mb-3">
								{#if event.label}
									{@const colors = getTeamColors(event.label)}
									{@const Icon = getTeamIcon(event.label)}
									<span
										class="px-3 py-1.5 text-[11px] font-black rounded-lg uppercase tracking-widest flex items-center gap-1.5 shadow-sm"
										style="background-color: {colors.badgeBg}20; color: {colors.badgeText}; border: 1px solid {colors.badgeBorder}40;"
									>
										{#if Icon}
											<Icon class="w-3.5 h-3.5" strokeWidth={3} />
										{/if}
										{event.label}
									</span>
								{/if}
								{#if event.type && event.type !== event.label}
									<span
										class="px-3 py-1.5 text-[11px] font-black rounded-lg uppercase tracking-widest bg-red-500 text-white shadow-sm"
									>
										{event.type}
									</span>
								{/if}
							</div>
							<h1
								class="text-2xl sm:text-4xl md:text-5xl font-black leading-tight mb-4 {isDarkText
									? 'text-gray-900 dark:text-white'
									: 'text-white drop-shadow-md'}"
							>
								{event.title}
							</h1>
							<div
								class="flex flex-row w-full sm:w-auto gap-2 sm:gap-4 font-medium text-xs sm:text-sm md:text-base {isDarkText
									? 'text-gray-600 dark:text-gray-300'
									: 'text-white'}"
							>
								<div
									class="flex-1 sm:flex-none flex items-center justify-center sm:justify-start gap-1.5 sm:gap-2 px-2 sm:px-4 py-2 rounded-xl border {isDarkText
										? 'bg-gray-50 dark:bg-zinc-800/80 border-gray-100 dark:border-zinc-700/50'
										: 'bg-black/40 backdrop-blur-md border-white/20 shadow-sm'} overflow-hidden"
								>
									<Calendar
										class="w-3.5 h-3.5 sm:w-4 sm:h-4 shrink-0 {isDarkText
											? 'text-red-500 dark:text-red-400'
											: 'text-red-400'}"
									/>
									<span class="hidden sm:inline whitespace-nowrap"
										>{formatDate(event.date, {
											weekday: 'long',
											day: 'numeric',
											month: 'long',
											year: 'numeric'
										})}</span
									>
									<span class="inline sm:hidden truncate"
										>{formatDate(event.date, {
											weekday: 'short',
											day: 'numeric',
											month: 'short',
											year: '2-digit'
										})}</span
									>
								</div>
								{#if event.raw_data?.detail?.start_time || event.raw_data?.short?.start_time}
									<div
										class="flex-1 sm:flex-none flex items-center justify-center sm:justify-start gap-1.5 sm:gap-2 px-2 sm:px-4 py-2 rounded-xl border {isDarkText
											? 'bg-gray-50 dark:bg-zinc-800/80 border-gray-100 dark:border-zinc-700/50'
											: 'bg-black/40 backdrop-blur-md border-white/20 shadow-sm'} overflow-hidden"
									>
										<Clock
											class="w-3.5 h-3.5 sm:w-4 sm:h-4 shrink-0 {isDarkText
												? 'text-red-500 dark:text-red-400'
												: 'text-red-400'}"
										/>
										<span class="truncate">
											{event.raw_data?.detail?.start_time?.slice(0, 5) ||
												event.raw_data?.short?.start_time?.slice(0, 5)}
											{#if event.raw_data?.detail?.end_time || event.raw_data?.short?.end_time}
												- {event.raw_data?.detail?.end_time?.slice(0, 5) ||
													event.raw_data?.short?.end_time?.slice(0, 5)}
											{/if}
											<span class="hidden sm:inline"> WIB</span>
										</span>
									</div>
								{/if}
							</div>
						{/snippet}

						<!-- Hero Section -->
						<div class="relative w-full flex flex-col">
							{#if heroImageUrl}
								<div
									class="relative w-full min-h-[280px] sm:min-h-[350px] flex flex-col justify-end"
								>
									<!-- Clickable Image Background -->
									<button
										onclick={() => (isLightboxOpen = true)}
										class="absolute inset-0 w-full h-full overflow-hidden bg-gray-100 dark:bg-zinc-800 group cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-red-500"
										aria-label="View full image"
									>
										<OptimizedImage
											src={heroImageUrl}
											srcMedium={event.imageUrl_medium}
											srcSmall={event.imageUrl_small}
											blurHash={event.blurHash}
											alt={event.title}
											class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
										/>
										<div
											class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors duration-300 z-10 hidden md:flex items-center justify-center pb-24 sm:pb-32"
										>
											<ZoomIn
												class="w-16 h-16 text-white opacity-0 group-hover:opacity-100 transition-opacity duration-300 drop-shadow-lg"
											/>
										</div>
									</button>

									<!-- Hero Content Overlay with seamless fade to background color -->
									<div
										class="relative z-20 px-6 sm:px-10 pt-[150px] sm:pt-[200px] pb-6 sm:pb-10 flex flex-col justify-end w-full bg-gradient-to-t from-white via-white/95 to-transparent dark:from-zinc-900 dark:via-zinc-900/95 pointer-events-none"
									>
										<div class="pointer-events-auto w-fit">
											{@render heroContent({ isDarkText: true })}
										</div>
									</div>
								</div>

								<ImageLightbox
									src={heroImageUrl}
									alt={event.title}
									isOpen={isLightboxOpen}
									onClose={() => (isLightboxOpen = false)}
								/>
							{:else}
								<!-- Hero without Image -->
								<div
									class="relative w-full min-h-[280px] sm:min-h-[350px] flex flex-col justify-end"
								>
									<div
										class="absolute inset-0 bg-gradient-to-br from-red-500/10 to-rose-700/10 dark:from-red-500/5 dark:to-rose-700/5 overflow-hidden pointer-events-none"
									>
										<div class="absolute -top-12 -right-12 text-red-500/5 dark:text-red-500/10">
											<Calendar class="w-64 h-64 -rotate-12" />
										</div>
									</div>
									<!-- Hero Content Overlay with seamless fade to background color -->
									<div
										class="relative z-10 px-6 sm:px-10 pt-[150px] sm:pt-[200px] pb-6 sm:pb-10 flex flex-col justify-end w-full bg-gradient-to-t from-white via-white/95 to-transparent dark:from-zinc-900 dark:via-zinc-900/95 pointer-events-none"
									>
										<div class="pointer-events-auto w-fit">
											{@render heroContent({ isDarkText: true })}
										</div>
									</div>
								</div>
							{/if}
						</div>

						<!-- Content Layout inside unified card -->
						<div
							class="grid grid-cols-1 xl:grid-cols-3 gap-8 xl:gap-12 p-6 sm:p-8 lg:p-10 max-w-5xl mx-auto"
						>
							<!-- Main Content -->
							<div class="xl:col-span-2 space-y-12">
								{#if contentBody}
									<div>
										<h2
											class="text-xl font-bold text-gray-900 dark:text-white mb-6 flex items-center gap-3"
										>
											<div class="h-6 w-1.5 bg-red-500 rounded-full"></div>
											{t('theater.events.eventInfo')}
										</h2>
										<div
											class="prose prose-sm sm:prose-base dark:prose-invert max-w-none text-gray-700 dark:text-gray-300"
										>
											<!-- eslint-disable-next-line svelte/no-at-html-tags -->
											{@html contentBody}
										</div>
									</div>
								{/if}

								{#if (event.members && event.members.length > 0) || event.setlistId}
									<div>
										<div class="flex items-center justify-between mb-6">
											<h2
												class="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-3"
											>
												<div class="h-6 w-1.5 bg-red-500 rounded-full"></div>
												{t('theater.events.performingMembers')}
											</h2>
											<div
												class="flex items-center gap-1.5 sm:gap-2 text-xs sm:text-sm font-medium text-gray-500 bg-gray-100 dark:bg-zinc-800 px-3 py-1.5 rounded-full shrink-0 whitespace-nowrap"
											>
												<Users class="w-3.5 h-3.5 sm:w-4 sm:h-4" />
												{event.members && event.members.length > 0 ? event.members.length : '?'}
												{t('theater.events.members')}
											</div>
										</div>

										<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
											{#if event.members && event.members.length > 0}
												{#each event.members as member}
													{@const isSeitansai = event.seitansaiMembers?.includes(member.name)}
													{@const isGrad = event.graduationMembers?.includes(member.name)}
													<a
														href={`/theater/members/${member.id}`}
														class="group relative bg-white dark:bg-zinc-800 rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-all block text-left"
													>
														{#if isSeitansai}
															<div
																class="absolute top-2 left-2 z-20 bg-pink-500 text-white p-1.5 rounded-full shadow-lg shadow-pink-500/30"
															>
																<Cake class="w-3.5 h-3.5" />
															</div>
														{/if}
														{#if isGrad}
															<div
																class="absolute top-2 right-2 z-20 bg-indigo-500 text-white p-1.5 rounded-full shadow-lg shadow-indigo-500/30"
															>
																<GraduationCap class="w-3.5 h-3.5" />
															</div>
														{/if}
														<div
															class="relative aspect-[3/4] overflow-hidden bg-gray-200 dark:bg-zinc-700"
														>
															{#if member.img}
																<OptimizedImage
																	src={member.img}
																	srcMedium={member.img_medium}
																	srcSmall={member.img_small}
																	blurHash={member.blurHash}
																	alt={member.name}
																	class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
																	sizes="(max-width: 640px) 50vw, (max-width: 768px) 33vw, 25vw"
																/>
															{:else}
																<div
																	class="w-full h-full bg-gradient-to-br from-pink-100 to-purple-100 dark:from-pink-900/30 dark:to-purple-900/30 flex items-center justify-center"
																>
																	<span class="text-4xl font-bold text-pink-400">
																		{member.nickname?.charAt(0) || member.name?.charAt(0)}
																	</span>
																</div>
															{/if}

															<!-- Frame Image Overlay -->
															<img
																src={getMemberFrame(member.member_type || 'JKT48')}
																alt="member frame"
																class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10"
															/>

															<!-- Gradient Overlay -->
															<div
																class="absolute inset-0 bg-gradient-to-t from-black/95 via-black/20 to-transparent z-20"
															></div>

															<!-- Content Area (Overlay) -->
															<div
																class="absolute bottom-0 left-0 right-0 p-3 flex flex-col justify-end z-30"
															>
																<h3
																	class="font-bold text-white text-base leading-tight drop-shadow-sm"
																>
																	{member.nickname || member.name}
																</h3>
																<p
																	class="text-[10px] text-gray-300 font-bold uppercase tracking-wider mt-0.5"
																>
																	{member.member_type || 'JKT48'}
																</p>
															</div>
														</div>
													</a>
												{/each}
											{:else}
												{#each Array(16) as _, _i}
													<div
														class="group relative bg-white dark:bg-zinc-800 rounded-xl overflow-hidden shadow-sm block text-left opacity-80"
													>
														<div
															class="relative aspect-[3/4] overflow-hidden bg-gray-200 dark:bg-zinc-700/50"
														>
															<div
																class="w-full h-full bg-gradient-to-br from-gray-200 to-gray-300 dark:from-zinc-800 dark:to-zinc-900 flex items-center justify-center"
															>
																<Users class="w-12 h-12 text-gray-400 dark:text-zinc-600" />
															</div>

															<!-- Frame Image Overlay (Standard) -->
															<img
																src={getMemberFrame('JKT48')}
																alt="member frame"
																class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10 grayscale opacity-40"
															/>

															<!-- Gradient Overlay -->
															<div
																class="absolute inset-0 bg-gradient-to-t from-black/80 via-black/10 to-transparent z-20"
															></div>

															<!-- Content Area (Overlay) -->
															<div
																class="absolute bottom-0 left-0 right-0 p-3 flex flex-col justify-end z-30"
															>
																<h3
																	class="font-bold text-white/70 text-base leading-tight drop-shadow-sm"
																>
																	???
																</h3>
																<p
																	class="text-[10px] text-gray-400 font-bold uppercase tracking-wider mt-0.5"
																>
																	TBA
																</p>
															</div>
														</div>
													</div>
												{/each}
											{/if}
										</div>
									</div>
								{/if}

								<!-- Exclusive Sessions -->
								{#if event.type === 'EXCLUSIVE' && event.raw_data?.detail?.session && event.raw_data.detail.session.length > 0}
									<div>
										<div
											class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4 sm:mb-6"
										>
											<h3
												class="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2"
											>
												<Users class="w-6 h-6 text-red-500" />
												{t('theater.events.sessionsAndQuotas')}
											</h3>
											{#if event.raw_data.detail.default_price !== undefined || event.raw_data.detail.total_quota !== undefined}
												<div
													class="flex items-center gap-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 px-4 py-2 rounded-xl text-sm font-bold w-fit"
												>
													{#if event.raw_data.detail.default_price !== undefined}
														<span
															>Rp {event.raw_data.detail.default_price.toLocaleString(
																'id-ID'
															)}</span
														>
													{/if}
													{#if event.raw_data.detail.default_price !== undefined && event.raw_data.detail.total_quota !== undefined}
														<span class="w-1 h-1 rounded-full bg-red-300 dark:bg-red-800"></span>
													{/if}
													{#if event.raw_data.detail.total_quota !== undefined}
														<span
															>{t('theater.events.quota') || 'Quota'}
															{event.raw_data.detail.total_quota}</span
														>
													{/if}
												</div>
											{/if}
										</div>

										<div class="space-y-4">
											{#each event.raw_data.detail.session as session, i}
												<details
													class="group bg-gray-50 dark:bg-zinc-800/50 rounded-2xl border border-gray-100 dark:border-zinc-700/50 overflow-hidden"
													open={i === 0}
												>
													<summary
														class="p-4 sm:p-5 flex items-center justify-between cursor-pointer list-none select-none hover:bg-gray-100 dark:hover:bg-zinc-700/50 transition-colors [&::-webkit-details-marker]:hidden"
													>
														<div>
															<h4 class="font-bold text-gray-900 dark:text-white">
																{session.label.replace('Sesi', t('theater.events.sessionName'))}
															</h4>
															<p class="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
																{formatDate(session.date, { day: 'numeric', month: 'short' })} • {session.start_time.substring(
																	0,
																	5
																)} - {session.end_time.substring(0, 5)}
															</p>
														</div>
														<div
															class="w-8 h-8 flex items-center justify-center rounded-full bg-white dark:bg-zinc-900 shadow-sm border border-gray-100 dark:border-zinc-700 group-open:-rotate-180 transition-transform duration-300 text-gray-500 shrink-0"
														>
															<svg
																xmlns="http://www.w3.org/2000/svg"
																width="16"
																height="16"
																viewBox="0 0 24 24"
																fill="none"
																stroke="currentColor"
																stroke-width="2"
																stroke-linecap="round"
																stroke-linejoin="round"><path d="m6 9 6 6 6-6" /></svg
															>
														</div>
													</summary>

													<div
														class="p-4 sm:p-5 border-t border-gray-100 dark:border-zinc-700/50 bg-white dark:bg-zinc-900/30"
													>
														<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
															{#each session.session_detail as detail}
																<div
																	class="flex items-center justify-between p-3 rounded-xl border border-gray-100 dark:border-zinc-800 bg-gray-50/50 dark:bg-zinc-800/20"
																>
																	<div class="min-w-0 pr-2">
																		<div
																			class="text-xs font-bold text-gray-500 dark:text-gray-400 mb-0.5"
																		>
																			{detail.label.replace('Jalur', t('theater.events.lane'))}
																		</div>
																		<div
																			class="font-bold text-sm text-gray-900 dark:text-white truncate"
																		>
																			{detail.jkt48_member_name}
																		</div>
																	</div>
																	<div class="text-right flex flex-col items-end shrink-0">
																		{#if detail.available_quota > 0}
																			<span
																				class="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 text-[10px] font-bold rounded uppercase"
																			>
																				{detail.available_quota}
																				{t('theater.events.available')}
																			</span>
																		{:else}
																			<span
																				class="px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-[10px] font-bold rounded uppercase"
																			>
																				{t('theater.events.soldOut')}
																			</span>
																		{/if}
																		<div class="text-[10px] text-gray-500 dark:text-gray-400 mt-1">
																			{detail.tickets_sold}
																			{t('theater.events.sold')}
																		</div>
																	</div>
																</div>
															{/each}
														</div>
													</div>
												</details>
											{/each}
										</div>
									</div>
								{/if}
							</div>

							<!-- Sidebar / Action Area -->
							<div class="space-y-10">
								<!-- Ticket Information -->
								{#if hasSales}
									<div>
										<h3
											class="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2"
										>
											<Ticket class="w-5 h-5 text-red-500" />
											{t('theater.events.ticketInfo')}
										</h3>

										<div class="space-y-4">
											{#each event.raw_data.detail.sales_period as sale}
												<div
													class="bg-gray-50 dark:bg-zinc-800/50 rounded-2xl p-4 border border-gray-100 dark:border-zinc-700/50"
												>
													<div class="flex justify-between items-start mb-3">
														<div>
															<h4 class="font-bold text-sm text-gray-900 dark:text-white">
																{sale.label}
															</h4>
															<p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
																{sale.sales_method}
															</p>
														</div>
														<span
															class="px-2 py-1 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 text-[10px] font-bold rounded uppercase"
														>
															{sale.sales_method === 'RAFFLE'
																? t('theater.events.raffle')
																: t('theater.events.firstCome')}
														</span>
													</div>

													<div class="space-y-2 mb-3">
														<div
															class="flex flex-col gap-0.5 text-xs text-gray-600 dark:text-gray-300"
														>
															<span class="text-gray-400 dark:text-gray-500"
																>{t('theater.events.salesPeriod')}</span
															>
															<span
																>{formatDate(sale.start_date, {
																	day: 'numeric',
																	month: 'short',
																	hour: '2-digit',
																	minute: '2-digit'
																})} - {formatDate(sale.end_date, {
																	day: 'numeric',
																	month: 'short',
																	hour: '2-digit',
																	minute: '2-digit'
																})}</span
															>
														</div>
													</div>

													{#if sale.pricing && sale.pricing.length > 0}
														<div
															class="space-y-2 border-t border-gray-200 dark:border-zinc-700 pt-3"
														>
															{#each sale.pricing as price}
																<div class="flex justify-between items-center">
																	<span class="text-xs font-medium text-gray-600 dark:text-gray-400"
																		>{price.label}</span
																	>
																	<div class="text-right">
																		<div class="text-sm font-bold text-gray-900 dark:text-white">
																			Rp {price.price.toLocaleString('id-ID')}
																		</div>
																		<div class="text-[10px] text-gray-500">
																			{t('theater.events.quota')}
																			{price.quota}
																		</div>
																	</div>
																</div>
															{/each}
														</div>
													{/if}
												</div>
											{/each}
										</div>
									</div>
								{/if}

								<!-- Action Card -->
								<div
									class="bg-gradient-to-br from-red-500 to-rose-600 rounded-3xl p-6 text-white shadow-xl shadow-red-500/20"
								>
									<h3 class="font-bold text-lg mb-2">{t('theater.events.interested')}</h3>
									<p class="text-sm text-red-100 mb-6">
										{t('theater.events.interestedDesc')}
									</p>
									<a
										href={`https://jkt48.com${event.url}`}
										target="_blank"
										class="w-full flex items-center justify-center gap-2 bg-white text-red-600 font-bold py-3 px-4 rounded-xl hover:bg-red-50 transition-colors shadow-sm"
									>
										<span>{t('theater.events.viewOnJkt48')}</span>
										<ExternalLink class="w-4 h-4" />
									</a>
								</div>
							</div>
						</div>
					</div>
				{:else}
					<!-- Loading Skeleton exactly mimicking the unified card structure -->
					<div class="bg-white dark:bg-zinc-900 overflow-hidden animate-pulse">
						<!-- Hero Skeleton -->
						<div class="relative w-full flex flex-col">
							<div
								class="relative w-full aspect-[21/9] sm:aspect-[3/1] bg-slate-200 dark:bg-zinc-800"
								style="-webkit-mask-image: linear-gradient(to top, transparent, black 60%); mask-image: linear-gradient(to top, transparent, black 60%);"
							></div>
							<div
								class="relative z-10 px-6 sm:px-10 pb-6 sm:pb-10 -mt-20 sm:-mt-28 flex flex-col justify-end w-full"
							>
								<div class="flex flex-wrap gap-2 mb-3">
									<div class="w-16 h-6 bg-slate-200 dark:bg-zinc-800 rounded-lg"></div>
									<div class="w-20 h-6 bg-slate-200 dark:bg-zinc-800 rounded-lg"></div>
								</div>
								<div
									class="w-3/4 max-w-lg h-10 sm:h-12 bg-slate-200 dark:bg-zinc-800 rounded-lg mb-4"
								></div>
								<div class="flex flex-row w-full sm:w-auto gap-2 sm:gap-4">
									<div
										class="flex-1 sm:flex-none w-32 h-10 bg-slate-200 dark:bg-zinc-800 rounded-xl"
									></div>
									<div
										class="flex-1 sm:flex-none w-40 h-10 bg-slate-200 dark:bg-zinc-800 rounded-xl"
									></div>
								</div>
							</div>
						</div>
						<!-- Content Skeleton -->
						<div
							class="grid grid-cols-1 xl:grid-cols-3 gap-8 xl:gap-12 p-6 sm:p-8 lg:p-10 max-w-5xl mx-auto"
						>
							<div class="xl:col-span-2 space-y-8">
								<div class="h-8 bg-gray-200 dark:bg-zinc-800 rounded w-1/3"></div>
								<div class="space-y-3">
									<div class="h-4 bg-gray-200 dark:bg-zinc-800 rounded w-full"></div>
									<div class="h-4 bg-gray-200 dark:bg-zinc-800 rounded w-5/6"></div>
									<div class="h-4 bg-gray-200 dark:bg-zinc-800 rounded w-4/6"></div>
								</div>
								<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 pt-6">
									{#each Array(8)}
										<div class="aspect-[3/4] bg-gray-200 dark:bg-zinc-800 rounded-xl"></div>
									{/each}
								</div>
							</div>
							<div class="space-y-6">
								<div class="h-8 bg-gray-200 dark:bg-zinc-800 rounded w-1/2"></div>
								<div class="h-32 bg-gray-200 dark:bg-zinc-800 rounded-2xl"></div>
								<div class="h-40 bg-gray-200 dark:bg-zinc-800 rounded-3xl mt-10"></div>
							</div>
						</div>
					</div>
				{/if}
			</div>
		</main>
	</div>
</div>

<style>
	/* Custom scrollbar for sidebar */
	.custom-scrollbar::-webkit-scrollbar {
		width: 4px;
	}
	.custom-scrollbar::-webkit-scrollbar-track {
		background: transparent;
	}
	.custom-scrollbar::-webkit-scrollbar-thumb {
		background: rgba(156, 163, 175, 0.3);
		border-radius: 4px;
	}
	:global(.dark) .custom-scrollbar::-webkit-scrollbar-thumb {
		background: rgba(75, 85, 99, 0.4);
	}
	.custom-scrollbar::-webkit-scrollbar-thumb:hover {
		background: rgba(156, 163, 175, 0.5);
	}
</style>
