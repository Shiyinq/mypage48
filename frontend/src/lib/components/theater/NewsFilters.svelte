<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { Calendar, RotateCcw } from 'lucide-svelte';

	const { t } = useTranslation();

	let {
		startDate = $bindable(),
		endDate = $bindable(),
		onClear = () => {}
	} = $props<{
		startDate?: string;
		endDate?: string;
		onClear?: () => void;
	}>();

	function handleClear() {
		startDate = undefined;
		endDate = undefined;
		onClear();
	}
</script>

<div
	class="bg-white dark:bg-zinc-900 rounded-xl shadow-lg border border-gray-100 dark:border-white/10 p-4"
>
	<div class="md:hidden flex items-center gap-2 mb-4">
		<h3 class="font-semibold text-sm text-gray-900 dark:text-white">
			{t('common.filter') || 'Filter'}
		</h3>
	</div>

	<div class="flex flex-col sm:flex-row items-center gap-2 mb-4">
		<!-- Start Date -->
		<div
			class="flex items-center bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-lg shadow-sm overflow-hidden flex-1 w-full px-3 py-2 gap-2 transition-all focus-within:ring-2 focus-within:ring-red-500 focus-within:border-transparent"
		>
			<span class="text-[10px] font-bold text-gray-500 uppercase tracking-wider shrink-0"
				>{t('common.fromShort') || 'Dari'}</span
			>
			<div class="relative w-full flex items-center">
				<input
					type="date"
					id="startDate"
					bind:value={startDate}
					class="w-full bg-transparent text-xs font-medium text-gray-700 dark:text-gray-300 focus:outline-none cursor-pointer color-scheme-dark z-10"
				/>
				<Calendar class="absolute right-0 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
			</div>
		</div>

		<!-- End Date -->
		<div
			class="flex items-center bg-gray-50 dark:bg-zinc-800/50 border border-gray-200 dark:border-zinc-700 rounded-lg shadow-sm overflow-hidden flex-1 w-full px-3 py-2 gap-2 transition-all focus-within:ring-2 focus-within:ring-red-500 focus-within:border-transparent"
		>
			<span class="text-[10px] font-bold text-gray-500 uppercase tracking-wider shrink-0"
				>{t('common.toShort') || 'Ke'}</span
			>
			<div class="relative w-full flex items-center">
				<input
					type="date"
					id="endDate"
					bind:value={endDate}
					class="w-full bg-transparent text-xs font-medium text-gray-700 dark:text-gray-300 focus:outline-none cursor-pointer color-scheme-dark z-10"
				/>
				<Calendar class="absolute right-0 w-3.5 h-3.5 text-gray-400 pointer-events-none" />
			</div>
		</div>
	</div>

	<!-- Clear Filter Button -->
	<div class="pt-3 border-t border-gray-100 dark:border-white/5">
		<button
			onclick={handleClear}
			class="flex items-center justify-center gap-2 w-full py-2 px-4 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 bg-gray-50 hover:bg-gray-100 dark:bg-zinc-800/50 dark:hover:bg-zinc-800 transition-colors border border-gray-200 dark:border-zinc-700 cursor-pointer"
		>
			<RotateCcw class="w-4 h-4" />
			{t('common.clearFilters') || 'Hapus Filter'}
		</button>
	</div>
</div>

<style>
	input[type='date'].color-scheme-dark {
		color-scheme: light dark;
	}

	input[type='date']::-webkit-calendar-picker-indicator {
		cursor: pointer;
		opacity: 0;
		width: 100%;
		height: 100%;
		position: absolute;
		right: 0;
		top: 0;
		margin: 0;
		padding: 0;
	}
</style>
