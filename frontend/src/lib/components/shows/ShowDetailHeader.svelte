<script lang="ts">
	import { ArrowLeft, AudioLines } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { OptimizedImage } from '$lib/components/common';

	interface ShowInfo {
		title: string;
		image: string;
	}

	interface Props {
		title: string;
		info: ShowInfo | undefined;
		ticketCount: number;
		onBack: () => void;
	}

	let { title, info, ticketCount, onBack }: Props = $props();

	const { t } = useTranslation();
</script>

<button onclick={onBack} class="flex items-center gap-4 mb-8 group cursor-pointer w-fit text-left">
	<div
		class="p-2.5 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 group-hover:bg-gray-200 dark:group-hover:bg-gray-700 group-hover:text-gray-900 dark:group-hover:text-white transition-all shadow-sm"
	>
		<ArrowLeft class="w-5 h-5" />
	</div>
	<div>
		<h2
			class="text-lg font-bold text-gray-900 dark:text-white group-hover:text-red-600 dark:group-hover:text-red-500 transition-colors leading-none"
		>
			{t('shows.backTitle')}
		</h2>
		<p class="text-xs text-gray-500 dark:text-gray-400 mt-1 font-medium">
			{t('shows.backSubtitle')}
		</p>
	</div>
</button>

<!-- Header -->
<div class="relative rounded-3xl overflow-hidden mb-8 shadow-lg group bg-gray-900 h-64 md:h-80">
	{#if info}
		<OptimizedImage
			src={info.image}
			alt={title}
			class="absolute inset-0 w-full h-full object-cover transition-opacity duration-700"
		/>
		<div class="absolute inset-0 bg-gradient-to-r from-black/90 via-black/60 to-transparent"></div>
	{/if}
	<div
		class="relative z-10 p-8 md:p-12 flex flex-col md:flex-row items-start md:items-center gap-6 h-full justify-center md:justify-start"
	>
		<div
			class="p-4 rounded-2xl bg-red-600/20 backdrop-blur-md text-white border border-white/10 shadow-inner"
		>
			<AudioLines class="w-8 h-8" />
		</div>
		<div>
			<h2 class="text-3xl md:text-4xl font-black text-white leading-none mb-2 drop-shadow-lg">
				{title}
			</h2>
			<p class="text-gray-200 font-medium text-lg">
				{ticketCount}
				{t('shows.performancesAttended')}
			</p>
		</div>
	</div>
</div>
