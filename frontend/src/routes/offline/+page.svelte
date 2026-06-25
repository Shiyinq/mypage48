<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();
</script>

<svelte:head>
	<title>Offline - MyPage48</title>
</svelte:head>

<div
	class="absolute inset-0 flex flex-col items-center justify-center p-6 bg-gray-50 dark:bg-[#0f0f11] overflow-y-auto z-10"
>
	<div class="max-w-md w-full flex flex-col items-center text-center space-y-8 pb-16">
		<!-- Animated pulsing circle with icon -->
		<div class="relative flex items-center justify-center">
			<div
				class="absolute inset-0 bg-red-500/20 dark:bg-red-500/10 rounded-full blur-2xl animate-pulse"
			></div>
			<div
				class="relative w-28 h-28 flex items-center justify-center bg-white dark:bg-zinc-900 border-4 border-red-50 dark:border-zinc-800 rounded-full shadow-2xl"
			>
				<svg
					class="w-12 h-12 text-red-500"
					fill="none"
					stroke="currentColor"
					viewBox="0 0 24 24"
					xmlns="http://www.w3.org/2000/svg"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M3 3l18 18M18.364 5.636a9 9 0 00-12.728 0M15.536 8.464a5 5 0 00-7.072 0M12 14v.01"
					/>
				</svg>
			</div>
		</div>

		<div class="space-y-4 px-2">
			<h1 class="text-3xl font-black text-gray-900 dark:text-white tracking-tight">
				{t('offline.title')}
			</h1>
			<p
				class="text-base sm:text-lg text-gray-500 dark:text-zinc-400 leading-relaxed max-w-sm mx-auto"
			>
				{t('offline.message')}
			</p>
		</div>

		<div class="pt-4 w-full sm:w-auto px-4">
			<button
				onclick={() => window.location.reload()}
				class="w-full sm:min-w-[240px] bg-red-600 hover:bg-red-700 text-white font-bold py-4 px-8 rounded-full transition-all shadow-[0_0_20px_rgba(220,38,38,0.3)] hover:shadow-[0_0_30px_rgba(220,38,38,0.5)] active:scale-95 flex items-center justify-center gap-2 cursor-pointer"
			>
				<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
					/>
				</svg>
				{t('offline.retry')}
			</button>
		</div>
	</div>
</div>
