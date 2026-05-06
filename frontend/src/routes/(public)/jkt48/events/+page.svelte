<script lang="ts">
	import { onMount } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { Calendar, Clock, Cake, ArrowRight } from 'lucide-svelte';
	import { EmptyState, ErrorState } from '$lib/components';
	import { scale } from 'svelte/transition';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import { EventCardSkeleton } from '$lib/components/skeletons';
	import {
		eventsStore,
		upcomingEvents,
		isUpcomingEventsLoading,
		upcomingError
	} from '$lib/stores/events.svelte';
	import { membersStore } from '$lib/stores/theater.svelte';
	import MemberCardSkeleton from '$lib/components/theater/MemberCardSkeleton.svelte';
	import { formatDate, formatTime } from '$lib/i18n';
	import SEO from '$lib/components/SEO.svelte';
	import { getMemberFrame } from '$lib/constants';
	import { OptimizedImage } from '$lib/components/common';
	import { parseIndonesianDate } from '$lib/utils/time';

	const { t, locale } = useTranslation();

	function isToday(dateStr: string): boolean {
		const eventDate = new Date(dateStr);
		const today = new Date();
		return (
			eventDate.getDate() === today.getDate() &&
			eventDate.getMonth() === today.getMonth() &&
			eventDate.getFullYear() === today.getFullYear()
		);
	}

	let mounted = $state(false);
	onMount(async () => {
		await eventsStore.loadUpcoming();
		await membersStore.loadBirthdays();
		mounted = true;
	});

	let eventsList = $derived(upcomingEvents.value);
	let loading = $derived(isUpcomingEventsLoading.value);
	let error = $derived(upcomingError.value);
	let birthdays = $derived(membersStore.birthdays || []);
	let birthdaysLoading = $derived(membersStore.isBirthdaysLoading);

	function getBirthdayText(
		daysUntil: number,
		t: (key: string, values?: Record<string, string | number>) => string
	): string {
		if (daysUntil === 0) return t('common.today');
		if (daysUntil === 1) return t('common.tomorrow');
		return t('theater.birthdays.daysLeft', { days: daysUntil });
	}
</script>

<SEO
	title={t('theater.events.title')}
	path="/jkt48/events"
	description={t('seo.events')}
	events={eventsList}
/>

<div class="space-y-16 pt-4 md:pt-6 pb-12">
	<div class="text-center space-y-4 mb-8">
		<h1
			class="text-3xl md:text-5xl font-black text-slate-900 dark:text-white tracking-tighter uppercase mb-3"
		>
			{t('theater.events.title')}
		</h1>
		<p
			class="text-base md:text-lg text-slate-500 dark:text-slate-400 font-medium max-w-2xl mx-auto uppercase tracking-widest"
		>
			{t('theater.events.subtitle')}
		</p>
	</div>

	<div class="space-y-8">
		<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
			<div class="flex items-center gap-4 group/header">
				<div class="h-10 w-2 bg-red-600 rounded-full shadow-lg shadow-red-500/20"></div>
				<h2 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight uppercase">
					{t('theater.upcomingEvents.title') || 'Upcoming Shows'}
				</h2>
			</div>

			<a
				href="/jkt48/event-history"
				class="inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-full bg-slate-100 dark:bg-zinc-800 text-slate-900 dark:text-white font-black text-[10px] uppercase tracking-[0.2em] shadow-sm hover:bg-slate-200 dark:hover:bg-zinc-700 transition-all group"
			>
				{t('theater.eventHistory.title') || 'Event History'}
				<ArrowRight size={14} class="group-hover:translate-x-1 transition-transform" />
			</a>
		</div>

		{#if loading && eventsList.length === 0}
			<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
				{#each Array(8) as _}
					<EventCardSkeleton />
				{/each}
			</div>
		{:else if error}
			<ErrorState
				title={t('theater.upcomingEvents.errorTitle') || 'Failed to load events'}
				description={t('theater.upcomingEvents.errorDesc') || error || ''}
				onRetry={() => eventsStore.loadUpcoming(true)}
			/>
		{:else if eventsList.length === 0}
			<EmptyState
				icon={Calendar}
				title={t('theater.upcomingEvents.emptyTitle')}
				description={t('theater.upcomingEvents.empty')}
			/>
		{:else}
			<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
				{#each eventsList as event (event.id)}
					<a
						href={`https://jkt48.com${event.url}`}
						target="_blank"
						class="group relative block transition-all duration-500 flex flex-row sm:block h-[10rem] sm:h-auto sm:aspect-[2/3] shadow-sm hover:shadow-2xl hover:-translate-y-1 rounded-[2rem] {isToday(
							event.date
						)
							? 'ring-4 ring-red-500/40 z-10'
							: 'border border-gray-100 dark:border-white/5'}"
						in:scale={{ duration: 300, start: 0.95 }}
					>
						{#if isToday(event.date)}
							<div
								class="absolute inset-0 rounded-[2rem] animate-pulse pointer-events-none shadow-[0_0_30px_rgba(239,68,68,0.4)] z-0"
							></div>
						{/if}

						<!-- Content Container -->
						<div
							class="relative z-10 flex flex-row sm:block w-full h-full overflow-hidden rounded-[2rem] bg-white dark:bg-zinc-900"
						>
							<!-- Image / Placeholder -->
							<div
								class="relative w-[40%] sm:w-full sm:h-full shrink-0 overflow-hidden bg-slate-50 dark:bg-zinc-800"
							>
								{#if event.imageUrl}
									<OptimizedImage
										src={event.imageUrl}
										srcMedium={event.imageUrl_medium}
										srcSmall={event.imageUrl_small}
										blurHash={event.blurHash}
										alt={event.title}
										class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
										sizes="(max-width: 640px) 40vw, (max-width: 1024px) 50vw, (max-width: 1280px) 33vw, 25vw"
									/>
									<div
										class="absolute inset-0 sm:hidden bg-gradient-to-r from-black/10 via-transparent to-black/5"
									></div>
									<div
										class="absolute inset-0 hidden sm:block bg-gradient-to-t from-black/95 via-black/40 to-transparent"
									></div>
								{:else}
									<div
										class="absolute inset-0 bg-gradient-to-br from-red-600 to-red-800 flex items-center justify-center opacity-20"
									>
										<Calendar class="w-12 h-12 text-white" />
									</div>
								{/if}

								<!-- Today Badge -->
								{#if isToday(event.date)}
									<div class="absolute top-4 left-4 z-20">
										<span
											class="inline-flex items-center px-3 py-1 rounded-full text-[10px] font-black text-white bg-red-600 shadow-xl shadow-red-500/30 ring-2 ring-white/20"
										>
											{t('theater.events.today')}
										</span>
									</div>
								{/if}
							</div>

							<!-- Details -->
							<div
								class="relative flex-1 p-5 flex flex-col justify-between sm:justify-end sm:absolute sm:inset-0 z-10"
							>
								<!-- Types/Labels -->
								<div class="flex items-center gap-2 mb-2">
									{#if event.label}
										<div
											class="px-2 py-0.5 text-[9px] font-black rounded-md uppercase tracking-wider {event.label ===
												'JKT48' ||
											event.label === 'GENERAL' ||
											event.label === 'EXCLUSIVE'
												? 'bg-red-600 text-white'
												: event.label === 'LOVE'
													? 'bg-pink-600 text-white'
													: event.label === 'DREAM'
														? 'bg-cyan-600 text-white'
														: event.label === 'PASSION'
															? 'bg-orange-600 text-white'
															: 'bg-zinc-800 text-white'}"
										>
											{event.label}
										</div>
									{/if}
									{#if event.type && event.type !== event.label}
										<div
											class="px-2 py-0.5 text-[9px] font-black rounded-md uppercase tracking-wider {event.type ===
											'EVENT'
												? 'bg-rose-600 text-white'
												: event.type === 'SHOW'
													? 'bg-blue-600 text-white'
													: event.type === 'GENERAL' || event.type === 'EXCLUSIVE'
														? 'bg-red-600 text-white'
														: 'bg-slate-700 text-white'}"
										>
											{event.type}
										</div>
									{/if}
								</div>

								<!-- Text Content -->
								<div>
									<h3
										class="font-black text-base sm:text-lg leading-tight mb-2 group-hover:text-red-600 sm:text-white transition-colors line-clamp-2 sm:line-clamp-none text-slate-900 dark:text-white"
									>
										{event.title}
									</h3>

									<div class="space-y-1.5">
										{#if (event.seitansaiMembers?.length ?? 0) > 0}
											<div
												class="flex items-center gap-2 text-[10px] sm:text-xs text-pink-600 sm:text-pink-300 font-black uppercase tracking-wider"
											>
												<Cake class="w-3.5 h-3.5" />
												<span class="line-clamp-1">{event.seitansaiMembers?.join(', ')}</span>
											</div>
										{/if}

										<!-- Date/Time Meta -->
										<div class="flex flex-col gap-1 sm:text-white/80">
											<div
												class="flex items-center gap-2 text-[10px] sm:text-xs font-bold uppercase tracking-widest"
											>
												<Calendar class="w-3.5 h-3.5" />
												<span
													>{formatDate(event.date, {
														day: 'numeric',
														month: 'short',
														year: 'numeric'
													})}</span
												>
											</div>
											{#if event.setlistId}
												<div
													class="flex items-center gap-2 text-[10px] sm:text-xs font-bold uppercase tracking-widest"
												>
													<Clock class="w-3.5 h-3.5" />
													<span
														>{formatTime(event.date, { hour: '2-digit', minute: '2-digit' })}</span
													>
												</div>
											{/if}
										</div>
									</div>
								</div>
							</div>
						</div>
					</a>
				{/each}
			</div>
		{/if}
	</div>

	<!-- Birthdays Section -->
	<div class="space-y-8">
		<div class="flex items-center gap-4 mb-8 group/header">
			<div class="h-10 w-2 bg-red-600 rounded-full shadow-lg shadow-red-500/20"></div>
			<h2 class="text-2xl font-black text-slate-900 dark:text-white tracking-tight uppercase">
				{t('theater.birthdays.title') || 'Upcoming Birthdays'}
			</h2>
		</div>

		{#if !mounted || (birthdaysLoading && birthdays.length === 0)}
			<div class="flex gap-6 overflow-x-auto pb-6 scrollbar-hide">
				{#each Array(6) as _}
					<div class="flex-none w-44 snap-start">
						<MemberCardSkeleton />
					</div>
				{/each}
			</div>
		{:else if birthdays.length === 0}
			<div
				class="p-12 rounded-[2.5rem] bg-slate-50 dark:bg-zinc-900/50 border-2 border-dashed border-slate-200 dark:border-zinc-800 text-center text-slate-400 font-bold uppercase tracking-widest text-sm"
			>
				{t('theater.birthdays.empty') || 'No upcoming birthdays'}
			</div>
		{:else}
			<div class="flex gap-6 overflow-x-auto pb-6 scrollbar-hide snap-x snap-mandatory">
				{#each birthdays as member}
					<div class="flex-none w-44 snap-start">
						<div
							class="relative group aspect-[3/4] rounded-xl overflow-hidden bg-white dark:bg-zinc-900 shadow-sm hover:shadow-md transition-all duration-300"
						>
							{#if member.img}
								<OptimizedImage
									src={getExternalMediaUrl(member.img)}
									srcMedium={getExternalMediaUrl(member.img_medium)}
									srcSmall={getExternalMediaUrl(member.img_small)}
									blurHash={member.blurHash}
									alt={member.name}
									class="w-full h-full object-cover transition-transform duration-1000 group-hover:scale-110"
									sizes="(max-width: 640px) 44vw, 176px"
								/>
							{:else}
								<div
									class="w-full h-full flex items-center justify-center bg-slate-100 text-slate-300"
								>
									<Cake class="w-12 h-12" />
								</div>
							{/if}

							<div
								class="absolute inset-0 bg-gradient-to-t from-black/90 via-black/20 to-transparent z-20"
							></div>

							<img
								src={getMemberFrame(member.member_type)}
								alt="member frame"
								class="absolute inset-0 w-full h-full object-fill pointer-events-none z-10"
							/>

							<!-- Countdown -->
							<div class="absolute top-4 left-0 right-0 flex justify-center z-30">
								<span
									class="px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest shadow-xl backdrop-blur-md border border-white/20 {member.days_until ===
									0
										? 'bg-red-600 text-white animate-pulse'
										: 'bg-black/60 text-white'}"
								>
									{getBirthdayText(member.days_until, t)}
								</span>
							</div>

							<div class="absolute bottom-6 left-5 right-5 z-30 text-left">
								<div
									class="text-white font-black text-sm leading-tight mb-1 truncate drop-shadow-md"
								>
									{member.name}
								</div>
								<div class="text-white/70 text-[10px] font-bold drop-shadow-md">
									{parseIndonesianDate(member.birthdate).getDate()}
									{parseIndonesianDate(member.birthdate).toLocaleString(locale.value, {
										month: 'short'
									})}
									•
									{member.age}
									{t('member.yearsOld')}
								</div>
							</div>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>

<style>
	.ring-red-500\/40 {
		--tw-shadow: 0 0 30px rgba(239, 68, 68, 0.4);
	}
</style>
