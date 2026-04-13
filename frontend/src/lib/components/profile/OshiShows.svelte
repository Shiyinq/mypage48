<script lang="ts">
	import { Calendar, History, ExternalLink, Music } from 'lucide-svelte';
	import type { OshiShow } from '$lib/types/auth';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { formatDate } from '$lib/i18n';

	interface Props {
		upcomingSchedule?: OshiShow[];
		pastSchedule?: OshiShow[];
		loading?: boolean;
	}

	let { upcomingSchedule = [], pastSchedule = [], loading = false }: Props = $props();

	const { t } = useTranslation();
</script>

<div class="flex flex-col gap-6">
	<div class="glass-panel p-5 rounded-3xl">
		<h4 class="font-bold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
			<Calendar class="w-4 h-4 text-blue-500" />
			{$t('profile.oshi.upcomingSchedule')}
		</h4>

		<div class="space-y-3">
			{#if loading}
				{#each [1, 2] as _}
					<div class="flex items-center gap-3 p-3 rounded-xl bg-gray-50/50 dark:bg-zinc-800/30">
						<div class="w-8 h-8 rounded-lg bg-gray-200 dark:bg-zinc-700 animate-pulse"></div>
						<div class="flex-1 space-y-2">
							<div class="h-3 w-3/4 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
							<div class="h-2 w-1/4 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
						</div>
					</div>
				{/each}
			{:else if upcomingSchedule.length === 0}
				<div
					class="text-center py-6 text-gray-500 bg-gray-50/50 dark:bg-zinc-800/30 rounded-2xl border border-dashed border-gray-100 dark:border-zinc-800"
				>
					<p class="text-xs">{$t('profile.oshi.noSchedule')}</p>
				</div>
			{:else}
				{#each upcomingSchedule as show}
					<div
						class="group flex items-center gap-3 p-3 rounded-xl bg-blue-50/30 dark:bg-blue-900/10 border border-blue-100/50 dark:border-blue-500/10 hover:border-blue-200 dark:hover:border-blue-500/20 transition-all"
					>
						<div
							class="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-600 dark:text-blue-400"
						>
							<Music class="w-5 h-5" />
						</div>
						<div class="flex-1 min-w-0">
							<p class="text-sm font-bold text-gray-800 dark:text-gray-200 truncate">
								{show.title}
							</p>
							<p class="text-[10px] font-medium text-gray-400">
								{$formatDate(show.date, { day: 'numeric', month: 'short', year: 'numeric' })}
							</p>
						</div>
						{#if show.url}
							<a
								href={show.url}
								target="_blank"
								rel="noopener noreferrer"
								class="p-2 text-gray-400 hover:text-blue-500 transition-colors"
							>
								<ExternalLink class="w-4 h-4" />
							</a>
						{/if}
					</div>
				{/each}
			{/if}
		</div>
	</div>

	<!-- Past Schedule -->
	<div class="glass-panel p-5 rounded-3xl">
		<h4 class="font-bold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
			<History class="w-4 h-4 text-purple-500" />
			{$t('profile.oshi.pastSchedule')}
		</h4>

		<div class="space-y-3">
			{#if loading}
				{#each [1, 2]}
					<div class="flex items-center gap-3 p-3 rounded-xl bg-gray-50/50 dark:bg-zinc-800/30">
						<div class="w-8 h-8 rounded-lg bg-gray-200 dark:bg-zinc-700 animate-pulse"></div>
						<div class="flex-1 space-y-2">
							<div class="h-3 w-3/4 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
							<div class="h-2 w-1/4 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
						</div>
					</div>
				{/each}
			{:else if pastSchedule.length === 0}
				<div
					class="text-center py-6 text-gray-500 bg-gray-50/50 dark:bg-zinc-800/30 rounded-2xl border border-dashed border-gray-100 dark:border-zinc-800"
				>
					<p class="text-xs">{$t('profile.oshi.noSchedule')}</p>
				</div>
			{:else}
				{#each pastSchedule as show}
					<div
						class="flex items-center gap-3 p-3 rounded-xl bg-purple-50/30 dark:bg-purple-900/10 border border-purple-100/50 dark:border-purple-500/10 hover:border-purple-200 dark:hover:border-purple-500/20 transition-all"
					>
						<div
							class="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center text-purple-600 dark:text-purple-400"
						>
							<Music class="w-5 h-5" />
						</div>
						<div class="flex-1 min-w-0">
							<p class="text-sm font-bold text-gray-800 dark:text-gray-200 truncate">
								{show.title}
							</p>
							<p class="text-[10px] font-medium text-gray-400">
								{$formatDate(show.date, { day: 'numeric', month: 'short', year: 'numeric' })}
							</p>
						</div>
						{#if show.url}
							<a
								href={show.url}
								target="_blank"
								rel="noopener noreferrer"
								class="p-2 text-gray-400 hover:text-purple-500 transition-colors"
							>
								<ExternalLink class="w-4 h-4" />
							</a>
						{/if}
					</div>
				{/each}
			{/if}
		</div>
	</div>
</div>
