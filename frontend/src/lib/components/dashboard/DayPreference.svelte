<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	interface Props {
		stats: {
			name: string;
			count: number;
		}[];
		maxCount: number;
		loading?: boolean;
	}

	let { stats, maxCount, loading = false }: Props = $props();
</script>

<div class="glass-panel p-6 rounded-3xl flex flex-col">
	<div class="mb-6">
		<h3 class="text-xl font-bold text-themed">
			{t('dashboard.dayPreference.title')}
		</h3>
		<p class="text-xs text-gray-400">{t('dashboard.dayPreference.subtitle')}</p>
	</div>

	<div class="flex flex-wrap justify-center gap-3 flex-1 content-start w-full">
		{#if loading}
			<!-- Skeleton Loading for Days -->
			<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
			{#each Array(7) as _unused, i}
				<div
					class="flex flex-col items-center w-[calc(33.33%-0.5rem)] sm:w-[calc(25%-0.56rem)] lg:w-[calc(33.33%-0.5rem)] xl:w-[calc(25%-0.56rem)]"
				>
					<div
						class="w-full aspect-square rounded-2xl mb-2 bg-gray-200 dark:bg-zinc-700 animate-pulse"
					></div>
					<div class="h-3 w-8 bg-gray-200 dark:bg-zinc-700 rounded animate-pulse"></div>
				</div>
			{/each}
		{:else}
			{#each stats as day}
				{@const intensity = day.count > 0 ? 0.2 + (day.count / maxCount) * 0.8 : 0.05}
				{@const hasData = day.count > 0}
				{@const isHighIntensity = intensity > 0.5}
				<div
					class="flex flex-col items-center group w-[calc(33.33%-0.5rem)] sm:w-[calc(25%-0.56rem)] lg:w-[calc(33.33%-0.5rem)] xl:w-[calc(25%-0.56rem)]"
				>
					<div
						class="w-full aspect-square rounded-2xl mb-2 flex flex-col items-center justify-center relative overflow-hidden transition-all duration-300 group-hover:-translate-y-1 group-hover:shadow-lg group-hover:scale-105 border"
						style={`
                            background: ${hasData ? `rgba(227, 0, 15, ${intensity})` : 'var(--color-surface)'}; 
                            border-color: ${hasData ? 'transparent' : 'var(--color-border-light)'};
                            box-shadow: ${hasData ? `0 4px 12px -2px rgba(220, 38, 38, ${intensity * 0.6})` : 'none'}
                        `}
					>
						{#if hasData}
							<span
								class={`text-xl md:text-2xl font-black drop-shadow-sm transition-colors duration-300 ${isHighIntensity ? 'text-white' : 'text-red-600 dark:text-red-400'}`}
							>
								{day.count}
							</span>
							<span
								class={`text-[8px] font-bold uppercase tracking-wider transition-colors duration-300 ${isHighIntensity ? 'text-white/80' : 'text-red-600/70 dark:text-red-400/70'}`}
							>
								{t('shows.unit')}
							</span>
						{:else}
							<span class="text-gray-300 dark:text-gray-600 text-xl font-bold opacity-30">-</span>
						{/if}
					</div>
					<div class="text-center w-full">
						<span
							class="text-[10px] font-bold text-gray-500 dark:text-gray-400 block uppercase tracking-wide group-hover:text-red-500 transition-colors"
							>{t('time.daysShort.' + day.name.substring(0, 3).toLowerCase())}</span
						>
					</div>
				</div>
			{/each}
		{/if}
	</div>
</div>
