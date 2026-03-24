<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { Calendar, X, ExternalLink, Clock, MapPin } from 'lucide-svelte';
	import { fade, scale } from 'svelte/transition';
	import { createEventDispatcher } from 'svelte';
	import type { CalendarEvent } from '$lib/types/events';
	import { formatDate } from '$lib/i18n';

	interface LandingCalendarEvent extends CalendarEvent {
		category?: string;
		time?: string;
		location?: string;
		id?: string;
		news_id?: string;
	}

	export let isOpen = false;
	export let date: Date;
	export let events: LandingCalendarEvent[] = [];

	const { t } = useTranslation();
	const dispatch = createEventDispatcher();

	function close() {
		dispatch('close');
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') close();
	}

	$: if (isOpen && typeof window !== 'undefined') {
		document.body.style.overflow = 'hidden';
	} else if (typeof window !== 'undefined') {
		document.body.style.overflow = 'unset';
	}
</script>

<svelte:window on:keydown={handleKeydown} />

{#if isOpen}
	<div
		class="fixed inset-0 z-[9999] flex items-center justify-center p-4 backdrop-blur-md bg-black/60 transition-all duration-300"
		on:click|self={close}
		role="presentation"
		transition:fade={{ duration: 300 }}
	>
		<div
			class="bg-white dark:bg-zinc-900 rounded-[2.5rem] shadow-2xl w-full max-w-lg overflow-hidden border border-gray-100 dark:border-zinc-800"
			transition:scale={{ duration: 300, start: 0.95 }}
		>
			<!-- Header -->
			<div class="px-8 py-6 border-b border-gray-50 dark:border-zinc-800 flex items-center justify-between bg-white dark:bg-zinc-900 sticky top-0 z-10">
				<div class="flex items-center gap-4">
					<div class="w-12 h-12 rounded-2xl bg-red-50 dark:bg-red-900/20 flex items-center justify-center text-red-600">
						<Calendar class="w-6 h-6" />
					</div>
					<div>
						<h2 class="text-xl font-black text-slate-900 dark:text-white uppercase tracking-tight">
							{$formatDate(date, { weekday: 'long', day: 'numeric', month: 'long' })}
						</h2>
						<p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-0.5">
							{events.length} {events.length === 1 ? $t('theater.events.event') : $t('nav.events')}
						</p>
					</div>
				</div>
				<button
					class="p-3 hover:bg-slate-50 dark:hover:bg-zinc-800 rounded-full transition-all text-slate-400 hover:text-red-600"
					on:click={close}
				>
					<X class="w-6 h-6" />
				</button>
			</div>

			<!-- Content -->
			<div class="p-6 max-h-[60vh] overflow-y-auto custom-scrollbar text-balance">
				{#if events.length === 0}
					<div class="flex flex-col items-center justify-center py-12 text-center space-y-4">
						<div class="w-20 h-20 rounded-full bg-slate-50 dark:bg-zinc-800/50 flex items-center justify-center text-slate-200">
							<Calendar class="w-10 h-10" />
						</div>
						<p class="text-slate-400 font-bold uppercase tracking-widest text-xs">
							{$t('theater.news.empty')}
						</p>
					</div>
				{:else}
					<div class="space-y-4">
						{#each events as event}
							<div class="group relative bg-white dark:bg-zinc-800/50 p-5 rounded-[2rem] border border-gray-100 dark:border-zinc-800 hover:border-red-200 dark:hover:border-red-900/30 transition-all duration-300">
								<div class="flex items-start justify-between gap-4">
									<div class="space-y-3 flex-1">
										<div class="flex flex-wrap gap-2">
											<span class="inline-flex items-center px-3 py-1 rounded-full text-[10px] font-black tracking-widest uppercase {event.isBirthday ? 'bg-pink-100 text-pink-700' : 'bg-red-600 text-white'}">
												{event.isBirthday ? $t('theater.events.birthday') : (event.category || 'EVENT')}
											</span>
											{#if event.time}
												<span class="inline-flex items-center gap-1.5 text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
													<Clock class="w-3.5 h-3.5" />
													{event.time}
												</span>
											{/if}
										</div>

										<h3 class="text-lg font-black text-slate-900 dark:text-white leading-tight group-hover:text-red-600 transition-colors">
											{event.title}
										</h3>

										{#if event.location}
											<div class="flex items-center gap-2 text-sm font-medium text-slate-500 dark:text-slate-400">
												<MapPin class="w-4 h-4 text-red-400" />
												{event.location}
											</div>
										{/if}
									</div>

									{#if event.id || event.news_id}
										<a
											href={event.news_id ? `/jkt48/news/${event.news_id}` : `/theater/schedule/${event.id}`}
											class="p-3 bg-slate-50 dark:bg-zinc-800 text-slate-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-2xl transition-all shrink-0"
											title={$t('theater.news.readMore')}
										>
											<ExternalLink class="w-5 h-5" />
										</a>
									{/if}
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<!-- Footer -->
			<div class="p-6 bg-slate-50/50 dark:bg-zinc-950/20 border-t border-gray-50 dark:border-zinc-800 text-center">
				<p class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em]">
					JKT48 {new Date().getFullYear()} • {$t('landing.nav.subtitle')}
				</p>
			</div>
		</div>
	</div>
{/if}

<style>
	.custom-scrollbar::-webkit-scrollbar {
		width: 6px;
	}
	.custom-scrollbar::-webkit-scrollbar-track {
		background: transparent;
	}
	.custom-scrollbar::-webkit-scrollbar-thumb {
		background: #e2e8f0;
		border-radius: 10px;
	}
	:global(.dark) .custom-scrollbar::-webkit-scrollbar-thumb {
		background: #27272a;
	}
</style>
