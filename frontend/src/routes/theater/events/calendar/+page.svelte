<script lang="ts">
	import { stopPropagation } from 'svelte/legacy';

	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { ChevronLeft, ChevronRight, Cake, GraduationCap } from 'lucide-svelte';
	import { calendarEvents, calendarLoading, eventsStore } from '$lib/stores/events';
	import DayEventsModal from '$lib/components/calendar/DayEventsModal.svelte';
	import type { CalendarEvent } from '$lib/types/events';

	import { formatDate, formatTime } from '$lib/i18n';
	const { t } = useTranslation();

	// Default initialization
	const now = new Date();
	let year: number = $state(now.getFullYear());
	let month: number = $state(now.getMonth() + 1); // 1-12
	let calendarDays: { date: Date; isCurrentMonth: boolean }[] = $state([]);

	// Date Picker State
	let isDatePickerOpen = $state(false);
	let pickerYear = $state(now.getFullYear());

	// Modal State
	let isModalOpen = $state(false);
	let modalDate = $state(new Date());
	let modalEvents: CalendarEvent[] = $state([]);

	function openDayModal(date: Date, events: CalendarEvent[]) {
		modalDate = date;
		modalEvents = events;
		isModalOpen = true;
	}

	// Constants
	const MAX_VISIBLE_EVENTS = 3;

	function updateCalendar(y: number, m: number) {
		const days: { date: Date; isCurrentMonth: boolean }[] = [];

		// 1. Calculate Start Date (Sunday before 1st)
		const firstDayOfMonth = new Date(y, m - 1, 1);
		const startDayOfWeek = firstDayOfMonth.getDay(); // 0(Sun) - 6(Sat)
		// Days to subtract to get to Sunday: dayOfWeek
		const startDate = new Date(firstDayOfMonth);
		startDate.setDate(startDate.getDate() - startDayOfWeek);

		const totalDays = 42;

		let currentDate = new Date(startDate);

		for (let i = 0; i < totalDays; i++) {
			days.push({
				date: new Date(currentDate),
				isCurrentMonth: currentDate.getMonth() === m - 1
			});
			currentDate.setDate(currentDate.getDate() + 1);
		}

		calendarDays = days;

		// Load data
		eventsStore.loadCalendar(y, m);
	}

	function changeMonth(offset: number) {
		let newMonth = month + offset;
		let newYear = year;

		if (newMonth > 12) {
			newMonth = 1;
			newYear++;
		} else if (newMonth < 1) {
			newMonth = 12;
			newYear--;
		}

		goto(`?year=${newYear}&month=${newMonth}`, { replaceState: true });
	}

	function isToday(date: Date): boolean {
		const today = new Date();
		return (
			date.getDate() === today.getDate() &&
			date.getMonth() === today.getMonth() &&
			date.getFullYear() === today.getFullYear()
		);
	}

	function getEventsForDay(date: Date) {
		return $calendarEvents.filter((e) => {
			const eDate = new Date(e.date);
			return (
				eDate.getDate() === date.getDate() &&
				eDate.getMonth() === date.getMonth() &&
				eDate.getFullYear() === date.getFullYear()
			);
		});
	}

	const weekDays = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'];

	// Initialize with today or query params
	$effect(() => {
		const qYear = $page.url.searchParams.get('year');
		const qMonth = $page.url.searchParams.get('month');

		// If query params exist, override the local state
		// Otherwise, keep the default initialized values (current date)
		if (qYear) year = parseInt(qYear);
		if (qMonth) month = parseInt(qMonth);

		updateCalendar(year, month);

		// Removed auto-selection of 1st day when changing months
	});

	$effect(() => {
		if (isDatePickerOpen) {
			pickerYear = year;
		}
	});
	let currentMonthEvents = $derived(
		$calendarEvents.filter((e) => {
			const d = new Date(e.date);
			return d.getMonth() === month - 1 && d.getFullYear() === year;
		})
	);
</script>

<SEO
	title={`${$t('theater.events.title')} - Calendar`}
	path="/theater/events/calendar"
	description="Theater schedule calendar"
/>

<div class="space-y-6">
	<!-- Main Calendar Container -->
	<div
		class="h-[calc(100vh-250px)] md:h-[calc(100vh-100px)] flex flex-col bg-white dark:bg-zinc-900 rounded-xl shadow-sm border border-gray-200 dark:border-zinc-800 overflow-hidden"
	>
		<!-- Header -->
		<!-- Header -->
		<div
			class="flex items-center justify-between px-4 md:px-6 py-3 border-b border-gray-200 dark:border-zinc-800"
		>
			<!-- Left: Month Title / Picker Toggle -->
			<div class="relative">
				<button
					class="text-lg md:text-xl font-bold text-gray-800 dark:text-gray-100 cursor-pointer hover:bg-gray-100 dark:hover:bg-zinc-800 px-2 py-1 rounded-lg transition-colors flex items-center gap-1 md:gap-2"
					onclick={() => (isDatePickerOpen = !isDatePickerOpen)}
				>
					{$formatDate(new Date(year, month - 1), {
						month: 'long',
						year: 'numeric'
					})}
					<ChevronRight
						class="w-4 h-4 rotate-90 opacity-50 transition-transform {isDatePickerOpen
							? '-rotate-90'
							: ''}"
					/>
				</button>

				{#if isDatePickerOpen}
					<!-- Backdrop -->
					<div
						class="fixed inset-0 z-10"
						onclick={() => (isDatePickerOpen = false)}
						role="button"
						tabindex="0"
						onkeydown={(e) => e.key === 'Escape' && (isDatePickerOpen = false)}
					></div>

					<!-- Popover -->
					<div
						class="absolute top-full left-0 mt-2 bg-white dark:bg-zinc-800 rounded-xl shadow-xl border border-gray-200 dark:border-zinc-700 p-4 z-20 min-w-[280px]"
					>
						<!-- Year Selector -->
						<div class="flex items-center justify-between mb-4 px-2">
							<button
								class="p-1 hover:bg-gray-100 dark:hover:bg-zinc-700 rounded-full cursor-pointer"
								onclick={stopPropagation(() => pickerYear--)}
							>
								<ChevronLeft class="w-5 h-5" />
							</button>
							<span class="font-bold text-lg">{pickerYear}</span>
							<button
								class="p-1 hover:bg-gray-100 dark:hover:bg-zinc-700 rounded-full cursor-pointer"
								onclick={stopPropagation(() => pickerYear++)}
							>
								<ChevronRight class="w-5 h-5" />
							</button>
						</div>

						<!-- Month Grid -->
						<div class="grid grid-cols-3 gap-2">
							{#each Array.from({ length: 12 }, (_, i) => i) as monthIndex}
								<button
									class="px-2 py-2 text-sm rounded-lg transition-colors cursor-pointer
									{monthIndex === month - 1 && pickerYear === year
										? 'bg-blue-600 text-white font-medium'
										: 'hover:bg-gray-100 dark:hover:bg-zinc-700 text-gray-700 dark:text-gray-300'}"
									onclick={stopPropagation(() => {
										goto(`?year=${pickerYear}&month=${monthIndex + 1}`);
										isDatePickerOpen = false;
									})}
								>
									{$formatDate(new Date(2000, monthIndex), {
										month: 'short'
									})}
								</button>
							{/each}
						</div>
					</div>
				{/if}
			</div>

			<!-- Monthly Stats -->
			{#if !$calendarLoading}
				<div
					class="hidden lg:flex items-center gap-2 md:gap-3 ml-2 md:ml-4 mr-auto text-xs font-medium text-gray-500 dark:text-gray-400"
				>
					<span
						class="flex items-center gap-1.5 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 px-2 py-1 rounded-full border border-blue-100 dark:border-blue-900/30"
					>
						<span class="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
						{currentMonthEvents.filter((e) => e.type === 'SHOW' || (!e.type && e.setlistId)).length}
						<span class="hidden sm:inline">{$t('theater.events.setlist')}</span>
					</span>
					<span
						class="flex items-center gap-1.5 bg-pink-50 dark:bg-pink-900/20 text-pink-700 dark:text-pink-300 px-2 py-1 rounded-full border border-pink-100 dark:border-pink-900/30"
					>
						<span class="w-1.5 h-1.5 rounded-full bg-pink-500"></span>
						{currentMonthEvents.filter((e) => e.type === 'BIRTHDAY' || e.isBirthday).length}
						<span class="hidden sm:inline">{$t('theater.events.birthday')}</span>
					</span>
					<span
						class="flex items-center gap-1.5 bg-purple-50 dark:bg-purple-900/20 text-purple-700 dark:text-purple-300 px-2 py-1 rounded-full border border-purple-100 dark:border-purple-900/30"
					>
						<span class="w-1.5 h-1.5 rounded-full bg-purple-500"></span>
						{currentMonthEvents.filter(
							(e) =>
								e.type !== 'SHOW' &&
								e.type !== 'BIRTHDAY' &&
								(!e.type ? !e.setlistId && !e.isBirthday : true)
						).length}
						<span class="hidden sm:inline">{$t('theater.events.eventType')}</span>
					</span>
				</div>
			{/if}

			<!-- Right: Controls -->
			<div class="flex items-center gap-2 md:gap-4">
				<!-- Today Button -->
				<button
					onclick={() => {
						const now = new Date();
						goto(`?year=${now.getFullYear()}&month=${now.getMonth() + 1}`);
					}}
					class="hidden md:block cursor-pointer px-4 py-1.5 text-sm font-medium border border-gray-300 dark:border-zinc-700 rounded-full hover:bg-gray-50 dark:hover:bg-zinc-800 transition-colors text-gray-700 dark:text-gray-300 shadow-sm"
				>
					{$t('theater.events.today') || 'Today'}
				</button>
				<button
					onclick={() => {
						const now = new Date();
						goto(`?year=${now.getFullYear()}&month=${now.getMonth() + 1}`);
					}}
					class="md:hidden cursor-pointer px-3 py-1.5 text-sm font-medium border border-gray-300 dark:border-zinc-700 rounded-full hover:bg-gray-50 dark:hover:bg-zinc-800 transition-colors text-gray-700 dark:text-gray-300 shadow-sm"
					aria-label="Today"
				>
					{$t('theater.events.today') || 'Today'}
				</button>

				<!-- Arrows -->
				<div class="flex items-center bg-gray-100 dark:bg-zinc-800 rounded-full p-0.5">
					<button
						onclick={() => changeMonth(-1)}
						class="cursor-pointer p-1.5 hover:bg-white dark:hover:bg-zinc-700 rounded-full transition-all text-gray-600 dark:text-gray-400 shadow-sm hover:shadow"
						aria-label="Previous month"
					>
						<ChevronLeft class="w-4 h-4" />
					</button>
					<button
						onclick={() => changeMonth(1)}
						class="cursor-pointer p-1.5 hover:bg-white dark:hover:bg-zinc-700 rounded-full transition-all text-gray-600 dark:text-gray-400 shadow-sm hover:shadow"
						aria-label="Next month"
					>
						<ChevronRight class="w-4 h-4" />
					</button>
				</div>
			</div>
		</div>

		<!-- Calendar Content -->
		{#if $calendarLoading && $calendarEvents.length === 0}
			<div class="flex-1 flex flex-col min-h-0 animate-pulse">
				<!-- Skeleton Header -->
				<div
					class="grid border-b border-gray-100 dark:border-zinc-800"
					style="grid-template-columns: repeat(7, 1fr);"
				>
					<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
					{#each Array(7) as _, i}
						<div class="py-3 flex justify-center">
							<div class="h-3 w-8 bg-gray-200 dark:bg-zinc-800 rounded"></div>
						</div>
					{/each}
				</div>
				<!-- Skeleton Grid -->
				<div
					class="grid flex-1 overflow-hidden"
					style="grid-template-columns: repeat(7, 1fr); grid-template-rows: repeat(6, 1fr);"
				>
					<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
					{#each Array(42) as _}
						<div
							class="border-b border-r border-gray-100 dark:border-zinc-800 p-1 flex flex-col items-center"
						>
							<div class="mt-1 mb-1 w-6 h-6 rounded-full bg-gray-200 dark:bg-zinc-800"></div>
							<div class="w-full h-8 bg-gray-100 dark:bg-zinc-800/50 rounded mt-1"></div>
						</div>
					{/each}
				</div>
			</div>
		{:else}
			<div class="flex-1 flex flex-col min-h-0">
				<!-- Weekday Headers -->
				<div
					class="grid border-b border-gray-200 dark:border-zinc-800"
					style="grid-template-columns: repeat(7, 1fr);"
				>
					{#each weekDays as dayKey, index}
						<div
							class="py-3 text-center text-[10px] font-semibold uppercase tracking-widest
								{index === 0
								? 'text-red-500 dark:text-red-400'
								: index === 6
									? 'text-blue-500 dark:text-blue-400'
									: 'text-gray-500 dark:text-gray-400'}"
						>
							{$t(`time.daysShort.${dayKey}`)}
						</div>
					{/each}
				</div>

				<!-- Calendar Grid -->
				<!-- Use grid-template-rows: repeat(6, 1fr) combined with h-full and min-h-0 to force equal heights and prevent expansion -->
				<div
					class="flex-1 grid min-h-0"
					style="grid-template-columns: repeat(7, 1fr); grid-template-rows: repeat(6, 1fr);"
				>
					{#each calendarDays as { date, isCurrentMonth }}
						{@const dayEvents = getEventsForDay(date)}
						{@const isTodayDate = isToday(date)}
						{@const dayOfWeek = date.getDay()}
						{@const isSunday = dayOfWeek === 0}
						{@const isSaturday = dayOfWeek === 6}

						<div
							role="button"
							tabindex="0"
							onclick={() => openDayModal(date, dayEvents)}
							onkeydown={(e) => {
								if (e.key === 'Enter' || e.key === ' ') {
									e.preventDefault();
									openDayModal(date, dayEvents);
								}
							}}
							class="border-b border-r border-gray-200 dark:border-zinc-800 p-0.5 md:p-1 min-h-0 flex flex-col items-center
                            {isCurrentMonth
								? 'bg-white dark:bg-zinc-900 hover:bg-gray-50 dark:hover:bg-zinc-800/50'
								: 'bg-gray-50/80 dark:bg-zinc-950/50 bg-striped'} 
							{isTodayDate && isCurrentMonth
								? isSunday
									? 'bg-red-50/50 dark:bg-red-900/10 ring-1 ring-inset ring-red-500/50 z-10'
									: 'bg-blue-50/50 dark:bg-blue-900/10 ring-1 ring-inset ring-blue-500/50 z-10'
								: ''}
                            group relative overflow-hidden cursor-pointer transition-all duration-200"
						>
							<!-- Date Number -->
							<div
								class="mt-0.5 md:mt-1 mb-0.5 md:mb-1 w-5 h-5 md:w-6 md:h-6 flex items-center justify-center rounded-full text-[10px] md:text-xs font-medium shrink-0 transition-transform group-hover:scale-110
                                 {isTodayDate
									? isSunday
										? 'bg-red-600 text-white shadow-sm shadow-red-200 dark:shadow-red-900/20'
										: 'bg-blue-600 text-white shadow-sm shadow-blue-200 dark:shadow-blue-900/20'
									: isCurrentMonth
										? isSunday
											? 'text-red-500 dark:text-red-400'
											: isSaturday
												? 'text-blue-500 dark:text-blue-400'
												: 'text-gray-700 dark:text-gray-300'
										: isSunday
											? 'text-red-300 dark:text-red-900/40'
											: isSaturday
												? 'text-blue-300 dark:text-blue-900/40'
												: 'text-gray-400 dark:text-zinc-600'}"
							>
								{date.getDate()}
							</div>

							<!-- Mobile Dot Indicator -->
							<!-- Show actual count of events -->
							<div
								class="flex flex-wrap justify-center gap-0.5 px-0.5 md:hidden w-full max-h-[50%] overflow-hidden"
							>
								<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
								{#each dayEvents.slice(0, 12) as _}
									<div class="w-1 h-1 rounded-full bg-blue-400 dark:bg-blue-500"></div>
								{/each}
								{#if dayEvents.length > 12}
									<div class="w-1 h-1 rounded-full bg-gray-300 dark:bg-gray-600"></div>
								{/if}
							</div>

							<!-- Desktop Events List (Hidden on Mobile) -->
							<div class="hidden md:flex w-full flex-1 flex-col gap-0.5 px-0.5 overflow-hidden">
								{#if dayEvents.length === 0 && isCurrentMonth}
									<!-- Empty State for Current Month -->
									<div
										class="h-full w-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
									>
										<span class="text-[9px] text-gray-300 dark:text-zinc-700 select-none">-</span>
									</div>
								{/if}

								{#each dayEvents.length > MAX_VISIBLE_EVENTS ? dayEvents.slice(0, MAX_VISIBLE_EVENTS - 1) : dayEvents as event}
									{@const isPast = new Date(event.date) < new Date()}
									<button
										class="block w-full px-1.5 py-0.5 rounded-[4px] text-[10px] font-medium text-left transition-all flex items-center gap-1.5 shadow-sm border border-transparent cursor-pointer
                                        {event.isBirthday
											? 'bg-pink-50 text-pink-700 dark:bg-pink-900/30 dark:text-pink-300 hover:bg-pink-100 dark:hover:bg-pink-900/40'
											: event.setlistId
												? 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/40'
												: 'bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300 hover:bg-purple-100 dark:hover:bg-purple-900/40'}
										{isPast ? 'opacity-50 saturate-50 brightness-95' : 'hover:brightness-95'}"
										title={event.title}
										onclick={stopPropagation(() => openDayModal(date, dayEvents))}
									>
										<!-- Time & Icon Container -->
										<div class="flex items-center gap-1 shrink-0">
											{#if new Date(event.date).getHours() !== 0 || new Date(event.date).getMinutes() !== 0}
												<span
													class="opacity-100 font-bold whitespace-nowrap leading-tight tracking-tight"
												>
													{$formatTime(new Date(event.date), {
														hour: '2-digit',
														minute: '2-digit',
														hour12: false
													})}
												</span>
											{/if}

											{#if event.isBirthday}
												<Cake class="w-3 h-3 mt-[-2px]" strokeWidth={2.5} />
											{:else if event.seitansaiMembers && event.seitansaiMembers.length > 0}
												<Cake class="w-3 h-3 mt-[-4px] text-pink-500" strokeWidth={2.5} />
											{:else if event.graduationMembers && event.graduationMembers.length > 0}
												<GraduationCap
													class="w-3 h-3 mt-[-4px] text-indigo-500"
													strokeWidth={2.5}
												/>
											{/if}
										</div>

										<span class="truncate leading-tight font-semibold opacity-90"
											>{event.title}</span
										>
									</button>
								{/each}

								<!-- More Indicator -->
								{#if dayEvents.length > MAX_VISIBLE_EVENTS}
									<button
										class="px-1.5 py-0.5 text-[9px] font-bold text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 text-left w-full hover:bg-gray-100 dark:hover:bg-zinc-800 rounded transition-colors cursor-pointer flex items-center gap-1"
										onclick={stopPropagation(() => openDayModal(date, dayEvents))}
									>
										<span class="w-1 h-1 rounded-full bg-gray-400 dark:bg-gray-500"></span>
										{$t('theater.events.moreEvents', {
											count: dayEvents.length - (MAX_VISIBLE_EVENTS - 1)
										})}
									</button>
								{/if}
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}
	</div>
</div>

<DayEventsModal
	isOpen={isModalOpen}
	date={modalDate}
	events={modalEvents}
	onclose={() => (isModalOpen = false)}
/>
