<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { CalendarEvent } from '$lib/types/events';
	import { Cake, ChevronRight, Calculator, Calendar, ExternalLink } from 'lucide-svelte';

	export let isOpen = false;
	export let date: Date;
	export let events: CalendarEvent[] = [];

	const dispatch = createEventDispatcher();
	const { t, locale } = useTranslation();

	function close() {
		dispatch('close');
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape' && isOpen) {
			close();
		}
	}
</script>

<svelte:window on:keydown={handleKeydown} />

{#if isOpen}
	<div
		class="fixed inset-0 z-[9999] flex items-center justify-center p-4 backdrop-blur-sm bg-black/50 transition-opacity"
		on:click|self={close}
		role="presentation"
	>
		<div
			class="w-full max-w-md bg-white dark:bg-zinc-900 rounded-2xl shadow-xl border border-gray-200 dark:border-zinc-800 overflow-hidden transform transition-all scale-100 opacity-100"
		>
			<!-- Header -->
			<div
				class="px-5 py-4 border-b border-gray-100 dark:border-zinc-800 flex items-center justify-between bg-gray-50/50 dark:bg-zinc-900/50"
			>
				<div>
					<h3
						class="font-semibold text-lg text-gray-900 dark:text-gray-100 flex items-center gap-2"
					>
						<Calendar class="w-5 h-5 text-gray-500" />
						{date.toLocaleDateString(
							$locale === 'en' ? 'en-US' : $locale === 'ja' ? 'ja-JP' : 'id-ID',
							{
								weekday: 'long',
								day: 'numeric',
								month: 'long'
							}
						)}
					</h3>
				</div>
				<button
					on:click={close}
					class="p-2 hover:bg-gray-100 dark:hover:bg-zinc-800 rounded-full transition-colors text-gray-500"
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						width="20"
						height="20"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
						stroke-width="2"
						stroke-linecap="round"
						stroke-linejoin="round"
						><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"
						></line></svg
					>
				</button>
			</div>

			<!-- Content -->
			<div class="max-h-[60vh] overflow-y-auto p-2 custom-scrollbar">
				{#if events.length === 0}
					<div
						class="py-12 flex flex-col items-center text-center text-gray-400 dark:text-zinc-600"
					>
						<Calendar class="w-10 h-10 mb-2 opacity-20" />
						<p>{$t('theater.events.noEvents')}</p>
					</div>
				{:else}
					<div class="space-y-1">
						{#each events as event}
							<a
								href={`https://jkt48.com${event.url}`}
								target="_blank"
								class="block p-3 hover:bg-gray-50 dark:hover:bg-zinc-800/50 rounded-xl transition-colors group"
							>
								<div class="flex items-start gap-4">
									<!-- Time -->
									<div class="w-14 shrink-0 flex flex-col items-center justify-center pt-0.5">
										{#if new Date(event.date).getHours() !== 0 || new Date(event.date).getMinutes() !== 0}
											<span class="text-sm font-bold text-gray-900 dark:text-gray-100">
												{new Date(event.date).toLocaleTimeString(
													$locale === 'en' ? 'en-US' : $locale === 'ja' ? 'ja-JP' : 'id-ID',
													{ hour: '2-digit', minute: '2-digit', hour12: false }
												)}
											</span>
										{:else}
											<span class="text-xs text-gray-400 font-medium">TBA</span>
										{/if}
									</div>

									<!-- Details -->
									<div class="flex-1 min-w-0">
										<!-- Badges -->
										<div class="flex flex-wrap gap-1.5 mb-1.5">
											{#if event.setlistId}
												<span
													class="px-2 py-0.5 text-[10px] uppercase font-bold tracking-wider rounded-md bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
												>
													{$t('theater.events.setlist')}
												</span>
											{:else}
												<span
													class="px-2 py-0.5 text-[10px] uppercase font-bold tracking-wider rounded-md bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300"
												>
													{$t('theater.events.eventType')}
												</span>
											{/if}

											{#if event.seitansaiMembers && event.seitansaiMembers.length > 0}
												<span
													class="flex items-center gap-1.5 text-[10px] bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-300 px-2 py-0.5 rounded-md font-medium leading-none"
												>
													<Cake class="w-3 h-3 mb-[3px]" />
													{$t('theater.events.birthday')}
													{#if event.seitansaiMembers.length > 0}
														: {event.seitansaiMembers.join(', ')}
													{/if}
												</span>
											{/if}
										</div>

										<h4
											class="font-medium text-gray-900 dark:text-gray-100 leading-snug group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors"
										>
											{event.title}
										</h4>
									</div>

									<ExternalLink
										class="w-4 h-4 text-gray-300 dark:text-zinc-600 group-hover:text-blue-400 dark:group-hover:text-blue-400 self-center"
									/>
								</div>
							</a>
						{/each}
					</div>
				{/if}
			</div>
		</div>
	</div>
{/if}
