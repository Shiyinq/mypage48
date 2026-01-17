<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import SEO from '$lib/components/SEO.svelte';
	import { ChevronLeft, ChevronRight, Calendar as CalendarIcon, Cake } from 'lucide-svelte';
	import { calendarEvents, calendarLoading, eventsStore, calendarError } from '$lib/stores/events';

	const { t, locale } = useTranslation();

	// Default initialization
	const now = new Date();
	let year: number = now.getFullYear();
	let month: number = now.getMonth() + 1; // 1-12
	let calendarDays: { date: Date; isCurrentMonth: boolean }[] = [];

	// Date Picker State
	let isDatePickerOpen = false;
	let pickerYear = year;

	$: if (isDatePickerOpen) {
		pickerYear = year;
	}

	// Initialize with today or query params
	$: {
		const qYear = $page.url.searchParams.get('year');
		const qMonth = $page.url.searchParams.get('month');

		// If query params exist, override the local state
		// Otherwise, keep the default initialized values (current date)
		if (qYear) year = parseInt(qYear);
		if (qMonth) month = parseInt(qMonth);

		updateCalendar(year, month);
	}

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
</script>

<SEO
	title={`${$t('theater.events.title')} - Calendar`}
	path="/theater/events/calendar"
	description="Theater schedule calendar"
/>

<div class="space-y-6">
	<!-- Main Calendar Container -->
	<div
		class="h-[calc(100vh-100px)] flex flex-col bg-white dark:bg-zinc-900 rounded-xl shadow-sm border border-gray-200 dark:border-zinc-800 overflow-hidden"
	>
		<!-- Header -->
		<div
			class="flex items-center justify-between px-6 py-3 border-b border-gray-200 dark:border-zinc-800"
		>
			<div class="flex items-center gap-6">
				<!-- Today Button -->
				<button
					on:click={() => {
						const now = new Date();
						goto(`?year=${now.getFullYear()}&month=${now.getMonth() + 1}`);
					}}
					class="cursor-pointer px-5 py-2 text-sm font-medium border border-gray-300 dark:border-zinc-700 rounded-full hover:bg-gray-50 dark:hover:bg-zinc-800 transition-colors text-gray-700 dark:text-gray-300 shadow-sm"
				>
					{$t('theater.events.today') || 'Today'}
				</button>

				<div class="flex items-center gap-4">
					<!-- Arrows -->
					<div class="flex items-center gap-1">
						<button
							on:click={() => changeMonth(-1)}
							class="cursor-pointer p-2 hover:bg-gray-100 dark:hover:bg-zinc-800 rounded-full transition-colors text-gray-600 dark:text-gray-400"
							aria-label="Previous month"
						>
							<ChevronLeft class="w-5 h-5" />
						</button>
						<button
							on:click={() => changeMonth(1)}
							class="cursor-pointer p-2 hover:bg-gray-100 dark:hover:bg-zinc-800 rounded-full transition-colors text-gray-600 dark:text-gray-400"
							aria-label="Next month"
						>
							<ChevronRight class="w-5 h-5" />
						</button>
					</div>

					<!-- Month Title / Picker Toggle -->
					<div class="relative">
						<button
							class="text-xl font-normal text-gray-800 dark:text-gray-100 cursor-pointer hover:bg-gray-100 dark:hover:bg-zinc-800 px-3 py-1 rounded-lg transition-colors flex items-center gap-2 min-w-[180px]"
							on:click={() => (isDatePickerOpen = !isDatePickerOpen)}
						>
							{new Date(year, month - 1).toLocaleString($locale === 'en' ? 'en-US' : 'id-ID', {
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
								on:click={() => (isDatePickerOpen = false)}
								role="button"
								tabindex="0"
								on:keydown={(e) => e.key === 'Escape' && (isDatePickerOpen = false)}
							></div>

							<!-- Popover -->
							<div
								class="absolute top-full left-0 mt-2 bg-white dark:bg-zinc-800 rounded-xl shadow-xl border border-gray-200 dark:border-zinc-700 p-4 z-20 min-w-[280px]"
							>
								<!-- Year Selector -->
								<div class="flex items-center justify-between mb-4 px-2">
									<button
										class="p-1 hover:bg-gray-100 dark:hover:bg-zinc-700 rounded-full cursor-pointer"
										on:click|stopPropagation={() => pickerYear--}
									>
										<ChevronLeft class="w-5 h-5" />
									</button>
									<span class="font-bold text-lg">{pickerYear}</span>
									<button
										class="p-1 hover:bg-gray-100 dark:hover:bg-zinc-700 rounded-full cursor-pointer"
										on:click|stopPropagation={() => pickerYear++}
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
											on:click|stopPropagation={() => {
												goto(`?year=${pickerYear}&month=${monthIndex + 1}`);
												isDatePickerOpen = false;
											}}
										>
											{new Date(2000, monthIndex).toLocaleString(
												$locale === 'en' ? 'en-US' : 'id-ID',
												{ month: 'short' }
											)}
										</button>
									{/each}
								</div>
							</div>
						{/if}
					</div>
				</div>
			</div>

			<!-- Right side placeholder -->
			<div></div>
		</div>

		<!-- Calendar Content -->
		{#if $calendarLoading && $calendarEvents.length === 0}
			<div class="flex-1 flex flex-col min-h-0 animate-pulse">
				<!-- Skeleton Header -->
				<div
					class="grid border-b border-gray-100 dark:border-zinc-800"
					style="grid-template-columns: repeat(7, 1fr);"
				>
					{#each Array(7) as _}
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
					{#each weekDays as dayKey}
						<div
							class="py-3 text-center text-[10px] font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-widest"
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

						<div
							class="border-b border-r border-gray-200 dark:border-zinc-800 p-1 min-h-0 flex flex-col items-center
                            {isCurrentMonth
								? 'bg-white dark:bg-zinc-900'
								: 'bg-white dark:bg-zinc-900'} 
                            group relative overflow-hidden"
						>
							<!-- Date Number -->
							<div
								class="mt-1 mb-1 w-6 h-6 flex items-center justify-center rounded-full text-xs font-medium shrink-0
                                 {isTodayDate
									? 'bg-blue-600 text-white'
									: isCurrentMonth
										? 'text-gray-700 dark:text-gray-300'
										: 'text-gray-400 dark:text-zinc-600'}"
							>
								{date.getDate()}
							</div>

							<!-- Events List -->
							<div
								class="w-full flex-1 flex flex-col gap-0.5 px-0.5 overflow-y-auto min-h-0 scrollbar-hide"
							>
								{#each dayEvents as event}
									<a
										href={`https://jkt48.com${event.url}`}
										target="_blank"
										class="block w-full px-2 py-0.5 rounded text-[10px] font-medium text-left transition-opacity hover:opacity-80 flex items-start gap-1.5
                                        {event.setlistId
											? 'bg-[#E8F0FE] text-[#1967D2] border border-[#E8F0FE] dark:bg-[#1967D2]/30 dark:text-[#E8F0FE] dark:border-transparent'
											: 'bg-[#F3E8FD] text-[#9334E6] border border-[#F3E8FD] dark:bg-[#9334E6]/30 dark:text-[#F3E8FD] dark:border-transparent'}"
										title={event.title}
									>
										<!-- Time & Icon Container -->
										<div class="flex items-center gap-1 shrink-0">
											{#if new Date(event.date).getHours() !== 0 || new Date(event.date).getMinutes() !== 0}
												<span class="opacity-75 whitespace-nowrap leading-tight">
													{new Date(event.date).toLocaleTimeString(
														$locale === 'en' ? 'en-US' : 'id-ID',
														{ hour: '2-digit', minute: '2-digit', hour12: false }
													)}
												</span>
											{/if}

											{#if event.seitansaiMembers && event.seitansaiMembers.length > 0}
												<Cake class="w-3 h-3 mt-[-4.5px]" strokeWidth={2.5} />
											{/if}
										</div>

										<span class="break-words leading-tight">{event.title}</span>
									</a>
								{/each}
							</div>
						</div>
					{/each}
				</div>
			</div>
		{/if}
	</div>
</div>
