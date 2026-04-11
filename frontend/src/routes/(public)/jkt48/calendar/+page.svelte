<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { ChevronLeft, ChevronRight, Cake, GraduationCap } from 'lucide-svelte';
	import { calendarEvents, calendarLoading, eventsStore } from '$lib/stores/events';
	import LandingDayEventsModal from '$lib/components/landing-page/LandingDayEventsModal.svelte';
	import type { CalendarEvent } from '$lib/types/events';
	import { formatDate, formatTime } from '$lib/i18n';
	import SEO from '$lib/components/SEO.svelte';

	const { t } = useTranslation();

	const basePath = '/jkt48/calendar';

	// Default initialization
	const now = new Date();
	let year: number = now.getFullYear();
	let month: number = now.getMonth() + 1; // 1-12
	let calendarDays: { date: Date; isCurrentMonth: boolean }[] = [];

	// Date Picker State
	let isDatePickerOpen = false;
	let pickerYear = year;

	// Modal State
	let isModalOpen = false;
	let modalDate = new Date();
	let modalEvents: CalendarEvent[] = [];

	function openDayModal(date: Date, events: CalendarEvent[]) {
		modalDate = date;
		modalEvents = events;
		isModalOpen = true;
	}

	$: if (isDatePickerOpen) {
		pickerYear = year;
	}

	$: {
		const qYear = $page.url.searchParams.get('year');
		const qMonth = $page.url.searchParams.get('month');
		if (qYear) year = parseInt(qYear);
		if (qMonth) month = parseInt(qMonth);
		updateCalendar(year, month);
	}

	function updateCalendar(y: number, m: number) {
		const days: { date: Date; isCurrentMonth: boolean }[] = [];
		const firstDayOfMonth = new Date(y, m - 1, 1);
		const startDayOfWeek = firstDayOfMonth.getDay();
		const startDate = new Date(firstDayOfMonth);
		startDate.setDate(startDate.getDate() - startDayOfWeek);

		let currentDate = new Date(startDate);
		for (let i = 0; i < 42; i++) {
			days.push({
				date: new Date(currentDate),
				isCurrentMonth: currentDate.getMonth() === m - 1
			});
			currentDate.setDate(currentDate.getDate() + 1);
		}
		calendarDays = days;
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
		goto(`${basePath}?year=${newYear}&month=${newMonth}`, { replaceState: true });
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

	$: currentMonthEvents = $calendarEvents.filter((e) => {
		const d = new Date(e.date);
		return d.getMonth() === month - 1 && d.getFullYear() === year;
	});

	$: setlistsCount = currentMonthEvents.filter(
		(e) => e.type === 'SHOW' || (!e.type && e.setlistId)
	).length;
	$: birthdaysCount = currentMonthEvents.filter(
		(e) => e.type === 'BIRTHDAY' || e.isBirthday
	).length;
	$: othersCount = currentMonthEvents.length - setlistsCount - birthdaysCount;
</script>

<SEO title={$t('theater.events.title')} path="/jkt48/calendar" description={$t('seo.calendar')} />

<div class="space-y-8 max-w-7xl mx-auto px-0 sm:px-4 pt-4 md:pt-6 pb-12">
	<div class="text-center space-y-4 mb-8">
		<h1
			class="text-3xl md:text-5xl font-black text-slate-900 dark:text-white tracking-tighter uppercase mb-3"
		>
			{$t('theater.events.title')}
		</h1>
		<p
			class="text-base md:text-lg text-slate-500 dark:text-slate-400 font-medium max-w-2xl mx-auto uppercase tracking-widest leading-relaxed"
		>
			{$t('theater.calendar.subtitle')}
		</p>
	</div>

	<div
		class="flex flex-col bg-white dark:bg-zinc-900 rounded-[2.5rem] shadow-2xl border border-gray-100 dark:border-zinc-800 overflow-hidden transition-all duration-500"
	>
		<!-- Header -->
		<div
			class="flex items-center justify-between px-1.5 md:px-6 py-4 border-b border-gray-50 dark:border-zinc-800"
		>
			<div class="relative">
				<button
					class="text-base md:text-xl font-black text-slate-900 dark:text-white cursor-pointer hover:text-red-600 px-2 md:px-3 py-1.5 rounded-xl transition-all flex items-center gap-1.5 uppercase tracking-tight"
					on:click={() => (isDatePickerOpen = !isDatePickerOpen)}
				>
					{$formatDate(new Date(year, month - 1), { month: 'short' })}
					<span class="hidden md:inline"
						>{$formatDate(new Date(2000, 0), { year: 'numeric' }).replace(
							'2000',
							year.toString()
						)}</span
					>
					<ChevronRight
						class="w-4 h-4 md:w-5 md:h-5 opacity-40 transition-transform {isDatePickerOpen
							? 'rotate-90'
							: ''}"
					/>
				</button>

				{#if isDatePickerOpen}
					<div
						class="fixed inset-0 z-10"
						on:click={() => (isDatePickerOpen = false)}
						role="presentation"
					></div>
					<div
						class="absolute top-full left-0 mt-3 bg-white dark:bg-zinc-800 rounded-3xl shadow-2xl border border-gray-100 dark:border-zinc-700 p-6 z-20 min-w-[320px]"
					>
						<div class="flex items-center justify-between mb-6">
							<button
								class="p-2 hover:bg-gray-50 dark:hover:bg-zinc-700 rounded-full transition-colors cursor-pointer"
								on:click|stopPropagation={() => pickerYear--}
							>
								<ChevronLeft class="w-6 h-6" />
							</button>
							<span class="font-black text-xl text-themed">{pickerYear}</span>
							<button
								class="p-2 hover:bg-gray-50 dark:hover:bg-zinc-700 rounded-full transition-colors cursor-pointer"
								on:click|stopPropagation={() => pickerYear++}
							>
								<ChevronRight class="w-6 h-6" />
							</button>
						</div>
						<div class="grid grid-cols-3 gap-3">
							{#each Array.from({ length: 12 }, (_, i) => i) as monthIndex}
								<button
									class="px-3 py-3 text-sm font-bold rounded-2xl transition-all cursor-pointer {monthIndex ===
										month - 1 && pickerYear === year
										? 'bg-red-600 text-white shadow-lg shadow-red-500/30'
										: 'hover:bg-gray-50 dark:hover:bg-zinc-700 text-slate-600'}"
									on:click|stopPropagation={() => {
										goto(`${basePath}?year=${pickerYear}&month=${monthIndex + 1}`);
										isDatePickerOpen = false;
									}}
								>
									{$formatDate(new Date(2000, monthIndex), { month: 'short' })}
								</button>
							{/each}
						</div>
					</div>
				{/if}
			</div>

			<!-- Center: Badges -->
			{#if !$calendarLoading && currentMonthEvents.length > 0}
				<div
					class="flex items-center gap-1 md:gap-3 ml-1 md:ml-4 mr-1 md:mr-auto text-xs font-medium text-gray-500 dark:text-gray-400 min-w-0"
				>
					{#if setlistsCount > 0}
						<div
							class="flex items-center gap-1 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 px-2 py-1 rounded-full border border-blue-100 dark:border-blue-900/30 text-[9px] md:text-[10px] font-black uppercase tracking-wider shrink-0"
						>
							<div class="w-1 h-1 md:w-1.5 md:h-1.5 rounded-full bg-blue-500 animate-pulse"></div>
							{setlistsCount} <span class="hidden sm:inline">{$t('theater.events.setlist')}</span>
						</div>
					{/if}
					{#if birthdaysCount > 0}
						<div
							class="flex items-center gap-1 bg-pink-50 dark:bg-pink-900/20 text-pink-600 dark:text-pink-400 px-2 py-1 rounded-full border border-pink-100 dark:border-pink-900/30 text-[9px] md:text-[10px] font-black uppercase tracking-wider shrink-0"
						>
							<div class="w-1 h-1 md:w-1.5 md:h-1.5 rounded-full bg-pink-500 animate-pulse"></div>
							{birthdaysCount} <span class="hidden sm:inline">{$t('theater.events.birthday')}</span>
						</div>
					{/if}
					{#if othersCount > 0}
						<div
							class="flex items-center gap-1 bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400 px-2 py-1 rounded-full border border-purple-100 dark:border-purple-900/30 text-[9px] md:text-[10px] font-black uppercase tracking-wider shrink-0"
						>
							<div class="w-1 h-1 md:w-1.5 md:h-1.5 rounded-full bg-purple-500 animate-pulse"></div>
							{othersCount} <span class="hidden sm:inline">{$t('theater.events.eventType')}</span>
						</div>
					{/if}
				</div>
			{/if}

			<!-- Controls -->
			<div class="flex items-center gap-2 md:gap-4 shrink-0">
				<button
					on:click={() => {
						const now = new Date();
						goto(`${basePath}?year=${now.getFullYear()}&month=${now.getMonth() + 1}`);
					}}
					class="hidden md:block px-6 py-2 text-xs font-black uppercase tracking-widest border-2 border-slate-100 dark:border-zinc-800 rounded-full hover:border-red-600 hover:text-red-600 transition-all text-slate-500 cursor-pointer active:scale-95 shadow-sm"
				>
					{$t('theater.events.today')}
				</button>
				<button
					on:click={() => {
						const now = new Date();
						goto(`${basePath}?year=${now.getFullYear()}&month=${now.getMonth() + 1}`);
					}}
					class="md:hidden cursor-pointer px-2 py-1 text-[9px] font-black uppercase tracking-widest border-2 border-slate-100 dark:border-zinc-800 rounded-full hover:border-red-600 hover:text-red-600 transition-all text-slate-500 active:scale-95 shadow-sm shrink-0"
				>
					{$t('theater.events.today')}
				</button>

				<div
					class="flex items-center bg-slate-100/50 dark:bg-zinc-800 rounded-full p-0.5 md:p-1 border border-slate-100 dark:border-zinc-700/50 scale-90 md:scale-100"
				>
					<button
						on:click={() => changeMonth(-1)}
						class="p-1 md:p-2 hover:bg-white dark:hover:bg-zinc-700 rounded-full transition-all text-slate-600 hover:text-red-600 cursor-pointer active:scale-90"
					>
						<ChevronLeft class="w-4 h-4 md:w-5 md:h-5" />
					</button>
					<button
						on:click={() => changeMonth(1)}
						class="p-1 md:p-2 hover:bg-white dark:hover:bg-zinc-700 rounded-full transition-all text-slate-600 hover:text-red-600 cursor-pointer active:scale-90"
					>
						<ChevronRight class="w-4 h-4 md:w-5 md:h-5" />
					</button>
				</div>
			</div>
		</div>

		<!-- Calendar Content -->
		{#if $calendarLoading && $calendarEvents.length === 0}
			<div class="flex-1 flex flex-col animate-pulse">
				<div
					class="grid border-b border-gray-50 dark:border-zinc-800"
					style="grid-template-columns: repeat(7, minmax(0, 1fr));"
				>
					{#each Array(7) as _}
						<div class="py-4 flex justify-center">
							<div class="h-3 w-12 bg-gray-100 dark:bg-zinc-800 rounded-full"></div>
						</div>
					{/each}
				</div>
				<div
					class="grid flex-1"
					style="grid-template-columns: repeat(7, minmax(0, 1fr)); grid-template-rows: repeat(6, 1fr);"
				>
					{#each Array(42) as _}
						<div
							class="border-b border-r border-gray-50 dark:border-zinc-800 p-2 flex flex-col items-center gap-2"
						>
							<div class="w-7 h-7 rounded-full bg-gray-50 dark:bg-zinc-800/50"></div>
							<div class="hidden md:flex flex-col w-full gap-1">
								<div class="h-4 w-full bg-gray-50 dark:bg-zinc-800/30 rounded-lg"></div>
								<div class="h-4 w-3/4 bg-gray-50 dark:bg-zinc-800/30 rounded-lg"></div>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{:else}
			<div class="flex-1 flex flex-col min-h-0">
				<div
					class="grid border-b border-gray-50 dark:border-zinc-800"
					style="grid-template-columns: repeat(7, minmax(0, 1fr));"
				>
					{#each weekDays as dayKey, index}
						<div
							class="py-4 text-center text-[10px] font-black uppercase tracking-[0.2em] {index === 0
								? 'text-red-600'
								: index === 6
									? 'text-blue-600'
									: 'text-slate-400'}"
						>
							{$t(`time.daysShort.${dayKey}`)}
						</div>
					{/each}
				</div>

				<div
					class="flex-1 grid min-h-0"
					style="grid-template-columns: repeat(7, minmax(0, 1fr)); grid-template-rows: repeat(6, 1fr);"
				>
					{#each calendarDays as { date, isCurrentMonth }}
						{@const dayEvents = getEventsForDay(date)}
						{@const isTodayDate = isToday(date)}
						{@const isSunday = date.getDay() === 0}
						{@const isSaturday = date.getDay() === 6}

						<div
							role="button"
							tabindex="0"
							on:click={() => openDayModal(date, dayEvents)}
							on:keydown={(e) =>
								(e.key === 'Enter' || e.key === ' ') && openDayModal(date, dayEvents)}
							class="border-b border-r border-gray-50 dark:border-zinc-800 p-1 flex flex-col items-center group relative cursor-pointer min-w-0 overflow-hidden transition-all duration-300 {isCurrentMonth
								? 'bg-white dark:bg-zinc-900 hover:bg-slate-50/50 dark:hover:bg-zinc-800/50'
								: 'bg-slate-50/30 dark:bg-zinc-950/30'} {isTodayDate && isCurrentMonth
								? 'ring-2 ring-inset ring-red-600/30 z-10'
								: ''}"
						>
							<div
								class="mt-2 mb-2 w-7 h-7 flex items-center justify-center rounded-full text-xs font-black shrink-0 transition-all group-hover:scale-110 {isTodayDate
									? 'bg-red-600 text-white shadow-lg shadow-red-500/30'
									: isCurrentMonth
										? isSunday
											? 'text-red-500'
											: isSaturday
												? 'text-blue-500'
												: 'text-slate-900 dark:text-white'
										: 'text-slate-300 dark:text-zinc-700'}"
							>
								{date.getDate()}
							</div>

							<!-- Mobile Dot Indicators -->
							<div
								class="flex flex-wrap justify-center gap-0.5 px-0.5 md:hidden w-full max-h-[50%] overflow-hidden mb-1"
							>
								{#each dayEvents.slice(0, 8) as event}
									<div
										class={`w-1 h-1 rounded-full ${event.type === 'BIRTHDAY' || event.isBirthday ? 'bg-pink-400' : event.type === 'SHOW' || event.setlistId ? 'bg-blue-400' : 'bg-purple-400'}`}
									></div>
								{/each}
								{#if dayEvents.length > 8}
									<div class="w-1 h-1 rounded-full bg-gray-300 dark:bg-gray-600"></div>
								{/if}
							</div>

							<!-- Desktop Events List (Hidden on Mobile) -->
							<div class="hidden md:flex flex-col w-full gap-1 px-1 overflow-hidden min-w-0">
								{#each dayEvents.slice(0, 3) as event}
									<button
										class="px-2 py-1 rounded-lg text-[9px] font-black uppercase tracking-wider truncate cursor-pointer {event.isBirthday
											? 'bg-pink-100 text-pink-700'
											: 'bg-red-50 text-red-700'} brightness-95 min-w-0 hover:scale-[1.02] active:scale-95 transition-transform"
										on:click|stopPropagation={() => openDayModal(date, dayEvents)}
									>
										{event.title}
									</button>
								{/each}
								{#if dayEvents.length > 3}
									<button
										on:click|stopPropagation={() => openDayModal(date, dayEvents)}
										class="text-[8px] font-black text-slate-400 text-center uppercase tracking-widest mt-0.5 truncate cursor-pointer hover:text-themed transition-colors"
									>
										{$t('theater.calendar.more', { count: dayEvents.length - 3 })}
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

<LandingDayEventsModal
	isOpen={isModalOpen}
	date={modalDate}
	events={modalEvents}
	on:close={() => (isModalOpen = false)}
/>
