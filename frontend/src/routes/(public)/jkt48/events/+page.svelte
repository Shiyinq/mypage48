<script lang="ts">
	import { onMount } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { Calendar, Clock, Cake, ArrowRight, GraduationCap, Users } from 'lucide-svelte';
	import { EmptyState, ErrorState, PublicEventFilter } from '$lib/components';
	import { scale } from 'svelte/transition';
	import { getExternalMediaUrl } from '$lib/utils/media';
	import { HorizontalEventCardSkeleton } from '$lib/components/skeletons';
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
	import { OptimizedImage, PromoBanner } from '$lib/components/common';
	import { parseIndonesianDate } from '$lib/utils/time';
	import { MemberDetailModal } from '$lib/components/profile';
	import type { Member } from '$lib/apis/members';
	import { getTeamColors } from '$lib/constants/teamColors';

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

	let showMemberDetail = $state(false);
	let selectedMember: Member | null = $state(null);
	let selectedLabels = $state<string[]>([]);

	let mounted = $state(false);
	onMount(async () => {
		await Promise.all([
			eventsStore.loadUpcoming(),
			membersStore.loadBirthdays(),
			membersStore.load() // Load full members data for the modal
		]);
		mounted = true;
	});

	let eventsList = $derived(
		upcomingEvents.value.filter((e) => {
			if (selectedLabels.length === 0) return true;
			const l = e.label?.toUpperCase() || '';
			const t = e.type?.toUpperCase() || '';
			return selectedLabels.includes(l) || selectedLabels.includes(t);
		})
	);
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

	<PromoBanner
		title={t('theater.events.promoTitle')}
		desc={t('theater.events.promoDesc')}
		actionText={t('theater.events.promoAction')}
	/>

	<div class="space-y-8">
		<div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
			<div class="flex items-center gap-4 group/header">
				<div class="h-10 w-2 bg-red-600 rounded-full shadow-lg shadow-red-500/20"></div>
				<h2
					class="text-2xl font-black text-slate-900 dark:text-white tracking-tight uppercase flex items-center gap-3"
				>
					{t('theater.upcomingEvents.title') || 'Upcoming Shows'}
					{#if mounted && !loading}
						<span
							class="px-3 py-1 rounded-full bg-white dark:bg-zinc-900 text-xs font-black text-gray-500 dark:text-gray-400 border border-gray-100 dark:border-zinc-800 shadow-sm transition-all"
						>
							{eventsList.length}
						</span>
					{/if}
				</h2>
			</div>

			<div class="flex items-center gap-2 w-full sm:w-auto">
				<PublicEventFilter bind:selectedLabels />

				<a
					href="/jkt48/event-history"
					class="flex w-full sm:w-auto flex-1 sm:flex-none h-[46px] sm:h-[50px] items-center justify-center gap-2 px-4 sm:px-6 rounded-full bg-white/80 dark:bg-zinc-900/80 backdrop-blur-md border border-gray-100 dark:border-zinc-800 text-slate-700 dark:text-slate-200 font-bold text-[13px] sm:text-sm shadow-sm hover:bg-white dark:hover:bg-zinc-900 hover:border-red-200 hover:text-red-600 transition-all cursor-pointer group"
				>
					{t('theater.eventHistory.title') || 'Event History'}
					<ArrowRight size={14} class="group-hover:translate-x-1 transition-transform" />
				</a>
			</div>
		</div>

		{#if (!mounted || loading) && eventsList.length === 0}
			<div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 lg:gap-5">
				{#each Array(8) as _}
					<HorizontalEventCardSkeleton />
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
			<div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 lg:gap-5">
				{#each eventsList as event (event.id)}
					<a
						href={`/jkt48/events/${event.id}`}
						class="group relative flex flex-row h-32 sm:h-36 lg:h-40 bg-white dark:bg-zinc-900 shadow-sm hover:shadow-xl rounded-[20px] sm:rounded-2xl transition-all duration-300 overflow-hidden border border-gray-100 dark:border-white/5 {isToday(
							event.date
						)
							? 'ring-2 ring-red-500/50'
							: ''}"
						in:scale={{ duration: 300, start: 0.95 }}
					>
						{#if isToday(event.date)}
							<!-- Premium Pulse Glow Overlay -->
							<div
								class="absolute inset-0 z-0 rounded-[20px] sm:rounded-2xl ring-4 ring-red-500/40 animate-pulse pointer-events-none shadow-[0_0_20px_rgba(239,68,68,0.3)]"
							></div>
						{/if}

						<!-- Image / Placeholder (Left side) -->
						<div
							class="relative w-1/3 sm:w-2/5 shrink-0 overflow-hidden bg-gray-50 dark:bg-zinc-800 z-10"
						>
							{#if event.imageUrl}
								<OptimizedImage
									src={event.imageUrl}
									srcMedium={event.imageUrl_medium}
									srcSmall={event.imageUrl_small}
									blurHash={event.blurHash}
									alt={event.title}
									sizes="(max-width: 640px) 40vw, (max-width: 1024px) 30vw, 20vw"
									class="w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
								/>
								<div
									class="absolute inset-0 bg-gradient-to-r from-black/20 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity"
								></div>
							{:else}
								<div
									class="absolute inset-0 bg-gradient-to-br from-red-500 to-red-700 flex items-center justify-center"
								>
									<Calendar class="w-8 h-8 text-white/50" />
								</div>
							{/if}

							<!-- Today Badge -->
							{#if isToday(event.date)}
								<div class="absolute bottom-2 left-2 z-20">
									<span
										class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] sm:text-xs font-bold text-white bg-red-500 shadow-lg shadow-red-500/30 backdrop-blur-sm today-badge"
									>
										{t('theater.events.today')}
									</span>
								</div>
							{/if}
						</div>

						<!-- Details (Right side) -->
						<div class="relative flex-1 p-3 sm:p-4 flex flex-col z-10 min-w-0">
							<!-- Top Metadata Row -->
							<div class="flex flex-wrap items-center gap-2 mb-1.5 sm:mb-2">
								{#if event.label}
									{@const labelColors = getTeamColors(event.label)}
									<div
										class="px-2 py-0.5 text-[10px] font-bold rounded-md uppercase tracking-wider border shadow-sm"
										style="background-color: {labelColors.badgeBg}20; color: {labelColors.badgeText}; border-color: {labelColors.badgeBorder}40;"
									>
										{event.label}
									</div>
								{/if}
								{#if event.type && event.type !== event.label}
									{@const typeColors = getTeamColors(event.type)}
									<div
										class="px-2 py-0.5 text-[10px] font-bold rounded-md uppercase tracking-wider shadow-sm border"
										style="background-color: {typeColors.badgeBg}20; color: {typeColors.badgeText}; border-color: {typeColors.badgeBorder}40;"
									>
										{event.type}
									</div>
								{/if}
							</div>

							<!-- Text Content -->
							<h3
								class="font-bold text-sm sm:text-base leading-snug mb-1 group-hover:text-red-600 dark:group-hover:text-red-400 transition-colors line-clamp-2 text-gray-900 dark:text-gray-100"
								title={event.title}
							>
								{event.title}
							</h3>

							{#if (event.seitansaiMembers?.length ?? 0) > 0}
								<div
									class="flex items-center gap-1.5 text-[11px] sm:text-xs text-pink-500 font-medium mb-1 w-fit"
								>
									<Cake class="w-3.5 h-3.5 text-pink-500" />
									<span class="line-clamp-1">{event.seitansaiMembers?.join(', ')}</span>
								</div>
							{/if}

							{#if (event.graduationMembers?.length ?? 0) > 0}
								<div
									class="flex items-center gap-1.5 text-[11px] sm:text-xs text-indigo-500 font-medium mb-1 w-fit"
								>
									<GraduationCap class="w-3.5 h-3.5 text-indigo-500" />
									<span class="line-clamp-1">{event.graduationMembers?.join(', ')}</span>
								</div>
							{/if}

							<!-- Metadata Grid -->
							<div class="flex flex-col gap-0.5 sm:gap-1 mt-auto">
								<!-- Date & Time -->
								<div
									class="flex items-center flex-wrap gap-x-2 gap-y-0.5 text-[10px] sm:text-[11px] font-medium text-gray-500 dark:text-gray-400"
								>
									<div class="flex items-center gap-1">
										<Calendar class="w-3 h-3 text-gray-400" />
										<span>
											{formatDate(event.date, {
												weekday: 'short',
												day: 'numeric',
												month: 'short',
												year: 'numeric'
											})}
										</span>
									</div>

									{#if event.setlistId}
										<div
											class="flex items-center gap-1 border-l border-gray-200 dark:border-zinc-700 pl-2"
										>
											<Clock class="w-3 h-3 text-gray-400" />
											<span>{formatTime(event.date, { hour: '2-digit', minute: '2-digit' })}</span>
										</div>
									{/if}
								</div>

								<!-- Members -->
								{#if event.totalMembers > 1}
									<div
										class="flex items-center gap-1 text-[10px] sm:text-[11px] font-medium text-gray-500 dark:text-gray-400"
									>
										<Users class="w-3 h-3 text-gray-400" />
										<span>{event.totalMembers} {t('theater.events.members')}</span>
									</div>
								{/if}
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
			<h2
				class="text-2xl font-black text-slate-900 dark:text-white tracking-tight uppercase flex items-center gap-3"
			>
				{t('theater.birthdays.title') || 'Upcoming Birthdays'}
				{#if mounted && !birthdaysLoading}
					<span
						class="px-3 py-1 rounded-full bg-white dark:bg-zinc-900 text-xs font-black text-gray-500 dark:text-gray-400 border border-gray-100 dark:border-zinc-800 shadow-sm transition-all"
					>
						{birthdays.length}
					</span>
				{/if}
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
					<button
						type="button"
						class="flex-none w-44 snap-start text-left cursor-pointer"
						onclick={() => {
							selectedMember = member as unknown as Member;
							showMemberDetail = true;
						}}
					>
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
					</button>
				{/each}
			</div>
		{/if}
	</div>
</div>

<MemberDetailModal
	show={showMemberDetail}
	member={selectedMember}
	members={membersStore.list.filter((m) => birthdays.some((b) => String(b.id) === String(m.id)))}
	onClose={() => {
		showMemberDetail = false;
		selectedMember = null;
	}}
/>

<style>
	.ring-red-500\/40 {
		--tw-shadow: 0 0 30px rgba(239, 68, 68, 0.4);
	}
</style>
