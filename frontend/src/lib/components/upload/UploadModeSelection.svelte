<script lang="ts">
	import { ScanLine, Keyboard, X, Image } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { TICKET_EXAMPLE_BASE64 } from '$lib/constants/ticketExample';

	interface Props {
		onScanClick: () => void;
		onManualClick: () => void;
		onCancel: () => void;
	}

	let { onScanClick, onManualClick, onCancel }: Props = $props();

	const { t } = useTranslation();

	let showExample = $state(false);
</script>

<div class="min-h-[80vh] flex flex-col items-center justify-center p-4 max-w-4xl mx-auto">
	<div class="hidden sm:block text-center mb-6 sm:mb-10">
		<h2 class="text-2xl sm:text-3xl font-black text-gray-800 dark:text-white mb-2">
			{t('upload.title')}
		</h2>
		<p class="text-sm sm:text-base text-gray-500 dark:text-gray-400">{t('upload.subtitle')}</p>
	</div>
	<div class="grid md:grid-cols-2 gap-4 sm:gap-6 w-full px-2 sm:px-0">
		<button
			onclick={onScanClick}
			class="group relative overflow-hidden bg-white dark:bg-zinc-800 p-6 sm:p-8 rounded-3xl border-2 border-red-100 dark:border-red-900/30 hover:border-red-500 dark:hover:border-red-500 shadow-lg hover:shadow-xl transition-all duration-300 text-left flex flex-col h-52 sm:h-64 justify-between cursor-pointer"
		>
			<div
				class="absolute top-0 right-0 w-32 h-32 bg-red-50 dark:bg-red-900/10 rounded-bl-full -mr-10 -mt-10 transition-transform group-hover:scale-110"
			></div>
			<div
				class="p-3 sm:p-4 bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-2xl w-fit z-10"
			>
				<ScanLine class="w-6 h-6 sm:w-8 sm:h-8" />
			</div>
			<div class="z-10">
				<h3
					class="text-xl sm:text-2xl font-bold text-gray-800 dark:text-gray-100 mb-1 group-hover:text-red-600 dark:group-hover:text-red-400 transition-colors"
				>
					{t('upload.scanTicket')}
				</h3>
				<p
					class="text-[12px] sm:text-sm font-medium text-gray-600 dark:text-gray-400 leading-relaxed"
				>
					{t('upload.scanDescription')}
				</p>
			</div>
		</button>
		<button
			onclick={onManualClick}
			class="group relative overflow-hidden bg-white dark:bg-zinc-800 p-6 sm:p-8 rounded-3xl border-2 border-gray-100 dark:border-zinc-700 hover:border-gray-400 dark:hover:border-zinc-500 shadow-lg hover:shadow-xl transition-all duration-300 text-left flex flex-col h-52 sm:h-64 justify-between cursor-pointer"
		>
			<div
				class="absolute top-0 right-0 w-32 h-32 bg-gray-50 dark:bg-zinc-700/50 rounded-bl-full -mr-10 -mt-10 transition-transform group-hover:scale-110"
			></div>
			<div
				class="p-3 sm:p-4 bg-gray-100 dark:bg-zinc-700 text-gray-600 dark:text-gray-300 rounded-2xl w-fit z-10"
			>
				<Keyboard class="w-6 h-6 sm:w-8 sm:h-8" />
			</div>
			<div class="z-10">
				<h3
					class="text-xl sm:text-2xl font-bold text-gray-800 dark:text-gray-100 mb-1 group-hover:text-gray-600 dark:group-hover:text-gray-300 transition-colors"
				>
					{t('upload.manualEntry')}
				</h3>
				<p class="text-[12px] sm:text-sm font-medium text-gray-600 dark:text-gray-400">
					{t('upload.manualDescription')}
				</p>
			</div>
		</button>
	</div>
	<!-- View supported ticket format example button -->
	<div class="mt-8">
		<button
			onclick={() => (showExample = true)}
			class="inline-flex items-center gap-2 px-5 py-2.5 text-xs sm:text-sm font-semibold text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/20 rounded-full border border-red-100 dark:border-red-900/30 hover:bg-red-100 dark:hover:bg-red-900/40 transition-all duration-300 cursor-pointer shadow-sm hover:shadow active:scale-95"
		>
			<Image class="w-4 h-4" />
			{t('upload.viewExample')}
		</button>
	</div>
	<button
		onclick={onCancel}
		class="mt-12 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 font-medium text-sm flex items-center gap-2 px-4 py-2 rounded-full hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
	>
		<X class="w-4 h-4" />
		{t('common.cancel')}
	</button>
</div>

{#if showExample}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md transition-opacity duration-300"
		onclick={() => (showExample = false)}
		role="presentation"
	>
		<div
			class="relative bg-white dark:bg-zinc-900 rounded-3xl max-w-lg w-full overflow-hidden shadow-2xl border border-gray-100 dark:border-zinc-800 p-6 flex flex-col items-center gap-4 transition-transform duration-300 scale-100"
			onclick={(e) => e.stopPropagation()}
			role="presentation"
		>
			<!-- Header row (flex row to prevent overlapping) -->
			<div
				class="flex items-start justify-between w-full gap-4 pb-3 border-b border-gray-100 dark:border-zinc-800"
			>
				<div class="flex flex-col text-left">
					<h3
						class="text-base sm:text-lg font-black text-gray-800 dark:text-gray-100 flex items-center gap-2"
					>
						<ScanLine class="w-5 h-5 text-red-500 shrink-0" />
						{t('upload.exampleTitle')}
					</h3>
					<p
						class="text-[11px] sm:text-xs text-gray-500 dark:text-gray-400 mt-0.5 font-medium leading-tight"
					>
						{t('upload.exampleSubtitle')}
					</p>
				</div>
				<button
					onclick={() => (showExample = false)}
					class="p-2 rounded-full bg-gray-100 dark:bg-zinc-800 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors cursor-pointer shrink-0"
					aria-label="Close"
				>
					<X class="w-4 h-4" />
				</button>
			</div>

			<!-- Image container with premium glow -->
			<div
				class="relative w-full rounded-2xl overflow-hidden shadow-lg border border-gray-100 dark:border-zinc-800/80 bg-zinc-50 dark:bg-zinc-950 flex justify-center items-center p-2 group"
			>
				<img
					src={TICKET_EXAMPLE_BASE64}
					alt="JKT48 Theater Ticket Example"
					class="w-full h-auto rounded-xl object-contain max-h-[350px] transition-transform duration-500 group-hover:scale-[1.02]"
				/>
			</div>

			<div
				class="bg-red-50/50 dark:bg-red-950/10 border border-red-100/50 dark:border-red-900/20 rounded-2xl p-4 text-left w-full"
			>
				<p class="text-xs text-gray-600 dark:text-gray-300 leading-relaxed font-medium">
					💡 {t('upload.exampleDescription')}
				</p>
			</div>
		</div>
	</div>
{/if}
