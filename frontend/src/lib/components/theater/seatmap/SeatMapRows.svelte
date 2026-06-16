<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		rows: readonly string[];
		rowStats: { counts: Record<string, number>; maxCount: number };
		isLoading: boolean;
	}

	let { rows, rowStats, isLoading }: Props = $props();

	const { t } = useTranslation();
</script>

{#if isLoading}
	<!-- Skeleton Loading for Rows -->
	<div
		class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 md:gap-x-16 gap-y-4 max-w-4xl mx-auto mt-2 pt-4 pb-4 px-4"
	>
		<!-- eslint-disable-next-line @typescript-eslint/no-unused-vars -->
		{#each rows as row}
			<div class="flex items-center gap-3">
				<div
					class="w-9 h-9 md:w-10 md:h-10 flex-shrink-0 rounded-xl bg-gray-200 dark:bg-zinc-700 animate-pulse"
				></div>
				<div class="flex-1 h-9 md:h-10 rounded-xl bg-gray-200 dark:bg-zinc-700 animate-pulse"></div>
			</div>
		{/each}
	</div>
{:else}
	<div
		class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 md:gap-x-16 gap-y-4 max-w-4xl mx-auto mt-2 pt-4 pb-4 px-4"
	>
		{#each rows as row}
			{@const count = rowStats.counts[row] || 0}
			{@const intensity = rowStats.maxCount > 0 ? count / rowStats.maxCount : 0}
			{@const hasData = count > 0}
			<div class="flex items-center gap-3 group">
				<div
					class={`w-9 h-9 md:w-10 md:h-10 flex-shrink-0 flex items-center justify-center rounded-xl text-sm font-bold transition-all duration-300 shadow-sm ${!hasData ? 'bg-gray-100 dark:bg-gray-800 text-gray-400' : ''}`}
					style={hasData
						? `background-color: rgba(220, 38, 38, ${0.2 + intensity * 0.8}); color: ${intensity > 0.4 ? 'white' : '#dc2626'}; box-shadow: 0 4px 12px -2px rgba(220, 38, 38, ${intensity * 0.5})`
						: ''}
				>
					{row}
				</div>
				<div
					class={`flex-1 h-9 md:h-10 rounded-xl flex items-center px-3 md:px-4 relative overflow-hidden transition-all duration-300 ${hasData ? 'bg-white dark:bg-gray-800 border border-red-100 dark:border-red-500/30 shadow-sm' : 'bg-gray-50 dark:bg-gray-800/50 border border-gray-100 dark:border-gray-700 border-dashed'}`}
				>
					{#if hasData}
						<div
							class="absolute left-0 top-0 bottom-0 transition-all duration-1000"
							style={`width: ${intensity * 100}%; background-color: rgba(220, 38, 38, ${0.1 + intensity * 0.9});`}
						>
							<div class="absolute right-0 top-0 bottom-0 w-[1px] bg-red-400 opacity-20"></div>
						</div>
					{/if}
					<div class="relative z-10 w-full flex justify-between items-center px-1">
						<span
							class={`text-[10px] md:text-xs font-bold uppercase tracking-wide transition-colors duration-300 ${hasData && intensity <= 0.3 ? 'text-gray-600 dark:text-gray-300' : ''} ${!hasData ? 'text-gray-300 dark:text-gray-600' : ''}`}
							style={hasData && intensity > 0.3
								? 'color: white; text-shadow: 0 1px 2px rgba(0,0,0,0.3)'
								: ''}>{t('dashboard.seatMap.row')} {row}</span
						>
						<span
							class={`text-base md:text-lg font-black transition-colors duration-300 ${hasData && intensity <= 0.85 ? 'text-red-600 dark:text-red-400' : ''} ${!hasData ? 'text-gray-300 dark:text-gray-600' : ''}`}
							style={hasData && intensity > 0.85
								? 'color: white; text-shadow: 0 1px 2px rgba(0,0,0,0.3)'
								: ''}>{count}</span
						>
					</div>
				</div>
			</div>
		{/each}
	</div>
{/if}
