<script lang="ts">
	import { Image as ImageIcon, MapPin, Calendar, Sparkles, User } from 'lucide-svelte';
	import { formatDate } from '$lib/i18n';
	import type { MemoryItem } from '$lib/types';

	interface Props {
		item: MemoryItem;
		rotation?: number;
		onClick: (item: MemoryItem) => void;
	}

	let { item, rotation = 0, onClick }: Props = $props();

	let tapeColor = $derived(item.type === '2SHOT' ? 'bg-purple-200/80' : 'bg-red-200/80');
</script>

<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
<div
	class="group relative transition-all duration-500 hover:z-10 hover:scale-105 cursor-pointer"
	style={`transform: rotate(${rotation}deg)`}
	onclick={() => onClick(item)}
>
	<!-- Washi Tape -->
	<div
		class={`absolute -top-3 left-1/2 -translate-x-1/2 w-16 sm:w-24 h-6 sm:h-8 ${tapeColor} backdrop-blur-sm opacity-90 z-20 shadow-sm transform rotate-1 clip-path-tape`}
	></div>

	<!-- Polaroid Card -->
	<div
		class="bg-white dark:bg-zinc-900 p-2 sm:p-3 pb-8 sm:pb-12 shadow-xl shadow-gray-200/50 dark:shadow-black/30 border border-gray-100 dark:border-zinc-700 rounded-sm transition-shadow duration-300 group-hover:shadow-2xl relative overflow-hidden"
	>
		<!-- Image Area -->
		<div
			class="aspect-[4/5] w-full bg-gray-100 mb-4 overflow-hidden relative border border-gray-50 grayscale-[20%] group-hover:grayscale-0 transition-all duration-500"
		>
			<img src={item.imageUrl} alt={item.title} class="w-full h-full object-cover" loading="lazy" />

			<!-- Date Stamp -->
			<div
				class="absolute bottom-2 right-2 bg-black/50 backdrop-blur-sm text-white text-[10px] font-mono px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity"
			>
				{$formatDate(item.date, {
					day: 'numeric',
					month: 'short',
					year: '2-digit'
				})}
			</div>

			<!-- View Icon -->
			<div
				class="absolute inset-0 flex items-center justify-center bg-black/20 opacity-0 group-hover:opacity-100 transition-opacity"
			>
				<div class="bg-white/90 p-2 rounded-full shadow-lg">
					<ImageIcon class="w-5 h-5 text-gray-800" />
				</div>
			</div>
		</div>

		<!-- Caption -->
		<div class="px-2 text-center relative">
			<h3
				class={`font-['Poppins'] font-bold text-xs sm:text-sm leading-tight mb-1 transition-colors ${item.type === '2SHOT' ? 'text-purple-600 dark:text-purple-400' : 'text-gray-800 dark:text-gray-100 group-hover:text-red-600 dark:group-hover:text-red-400'}`}
			>
				{item.title}
			</h3>

			{#if item.type === '2SHOT'}
				<p
					class="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1 line-clamp-1"
				>
					{item.eventTitle}
				</p>
			{/if}

			<div
				class="flex items-center justify-center gap-2 text-[10px] font-medium text-gray-400 uppercase tracking-wider"
			>
				{#if item.type === 'TICKET'}
					<span class="flex items-center gap-0.5"><MapPin class="w-3 h-3" /> {item.subtitle}</span>
					<span>•</span>
					<span class="flex items-center gap-0.5"><Calendar class="w-3 h-3" /> {item.time}</span>
				{:else}
					<span class="flex items-center gap-0.5"><Sparkles class="w-3 h-3" /> {item.subtitle}</span
					>
					<span>•</span>
					<span class="flex items-center gap-0.5"
						><User class="w-3 h-3" />
						{item.twoShotMemberName?.split(' ')[0] ?? ''}</span
					>
				{/if}
			</div>
		</div>
	</div>
</div>

<style>
	.clip-path-tape {
		clip-path: polygon(
			2% 0,
			98% 0,
			100% 10%,
			98% 20%,
			100% 30%,
			98% 40%,
			100% 50%,
			98% 60%,
			100% 70%,
			98% 80%,
			100% 90%,
			98% 100%,
			2% 100%,
			0 90%,
			2% 80%,
			0 70%,
			2% 60%,
			0 50%,
			2% 40%,
			0 30%,
			2% 20%,
			0 10%
		);
	}
</style>
