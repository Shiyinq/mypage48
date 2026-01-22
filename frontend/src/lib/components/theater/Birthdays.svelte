<script lang="ts">
	import { writable } from 'svelte/store';
	import { onMount } from 'svelte';
	import { Cake } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { BirthdayResponse } from '$lib/apis/members';

	const { t, locale } = useTranslation();

	export let birthdays: BirthdayResponse[] = [];
	export let isLoading = true;

	function getBirthdayText(daysUntil: number, t: Function): string {
		if (daysUntil === 0) return t('common.today');
		if (daysUntil === 1) return t('common.tomorrow');
		return t('theater.birthdays.daysLeft', { days: daysUntil });
	}

	// Scroll container reference for possible future enhancements like drag-to-scroll
	let scrollContainer: HTMLElement;
</script>

<div class="space-y-4 mb-8">
	<div class="flex items-center gap-2">
		<Cake class="w-5 h-5 text-pink-400" />
		<h2 class="text-xl font-bold text-gray-800 dark:text-gray-100">
			{$t('theater.birthdays.title') || 'Upcoming Birthdays'}
		</h2>
	</div>

	{#if isLoading}
		<div class="flex gap-4 overflow-x-auto pb-4 scrollbar-hide">
			{#each Array(4) as _}
				<div
					class="flex-none w-40 h-52 rounded-xl bg-gray-200 dark:bg-zinc-800 animate-pulse"
				></div>
			{/each}
		</div>
	{:else if birthdays.length === 0}
		<div
			class="p-6 rounded-xl bg-gray-100 dark:bg-zinc-800/50 border border-dashed border-gray-300 dark:border-zinc-700 text-center text-gray-500"
		>
			{$t('theater.birthdays.empty') || 'No upcoming birthdays in the next 30 days.'}
		</div>
	{:else}
		<div
			bind:this={scrollContainer}
			class="flex gap-4 overflow-x-auto pb-4 scrollbar-hide snap-x snap-mandatory"
		>
			{#each birthdays as member}
				<div class="flex-none w-40 snap-start">
					<div
						class="relative group aspect-[3/4] rounded-xl overflow-hidden bg-gray-100 dark:bg-zinc-800 shadow-sm hover:shadow-md transition-all mb-2"
					>
						{#if member.img}
							<img
								src={member.img}
								alt={member.name}
								class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
							/>
						{:else}
							<div class="w-full h-full flex items-center justify-center bg-gray-200 text-gray-400">
								<Cake class="w-8 h-8" />
							</div>
						{/if}
						<div
							class="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent"
						></div>

						<!-- Top Overlay Gradient -->
						<div
							class="absolute inset-x-0 top-0 h-10 bg-gradient-to-b from-black/40 to-transparent pointer-events-none"
						></div>

						<!-- Countdown Overlay (Top) -->
						<div class="absolute top-2 left-0 right-0 flex justify-center">
							<span
								class="inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold shadow-sm backdrop-blur-md border border-white/20 drop-shadow-sm {member.days_until ===
								0
									? 'bg-pink-500/90 text-white animate-pulse'
									: 'bg-black/40 text-white'}"
							>
								{getBirthdayText(member.days_until, $t)}
							</span>
						</div>

						<div class="absolute bottom-0 left-0 right-0 p-3">
							<div class="text-white font-bold text-sm truncate drop-shadow-sm">
								{member.name}
							</div>
							<div class="text-gray-200 text-xs font-medium drop-shadow-sm">
								{new Date(member.birthdate).getDate()}
								{new Date(member.birthdate).toLocaleString($locale, { month: 'short' })}
								•
								{member.age}
								{$t('member.yearsOld') || 'years old'}
							</div>
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
