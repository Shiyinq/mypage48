<script lang="ts">
	import { X, Calendar, MapPin, Sparkles } from 'lucide-svelte';
	import { fade, scale } from 'svelte/transition';
	import { formatDate } from '$lib/i18n';
	import type { MemoryItem } from '$lib/types';

	interface Props {
		selectedImage?: MemoryItem | null;
		onClose: () => void;
	}

	let { selectedImage = null, onClose }: Props = $props();
</script>

{#if selectedImage}
	<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-[10001] flex flex-col items-center justify-center p-4 bg-black/90 backdrop-blur-md cursor-pointer"
		transition:fade={{ duration: 200 }}
		onclick={onClose}
	>
		<button
			onclick={(e) => {
				e.stopPropagation();
				onClose();
			}}
			class="absolute top-4 right-4 p-3 bg-white/10 hover:bg-white/20 text-white rounded-full transition-colors z-50 backdrop-blur-sm cursor-pointer"
		>
			<X class="w-6 h-6" />
		</button>

		<!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_noninteractive_element_interactions -->
		<div
			class="flex flex-col items-center pointer-events-none"
			transition:scale={{ duration: 300, start: 0.95 }}
		>
			<img
				src={selectedImage.imageUrl}
				alt={selectedImage.title}
				class="max-h-[70vh] w-auto object-contain rounded-lg shadow-2xl border border-white/10 cursor-default pointer-events-auto"
				onclick={(e) => e.stopPropagation()}
			/>

			<div
				class="mt-6 text-center w-full max-w-lg pointer-events-auto"
				onclick={(e) => e.stopPropagation()}
			>
				<h3 class="text-2xl font-bold text-white tracking-tight drop-shadow-md">
					{selectedImage.title}
				</h3>
				<div
					class="flex flex-wrap items-center justify-center gap-2 text-sm font-medium text-white/90 mt-3"
				>
					<span
						class="flex items-center gap-1.5 bg-white/10 px-3 py-1.5 rounded-full backdrop-blur-md border border-white/10"
					>
						<Calendar class="w-3.5 h-3.5" />
						{$formatDate(selectedImage.date, {
							day: 'numeric',
							month: 'long',
							year: 'numeric'
						})}
					</span>
					<span
						class="flex items-center gap-1.5 bg-white/10 px-3 py-1.5 rounded-full backdrop-blur-md border border-white/10"
					>
						{#if selectedImage.type === 'TICKET'}
							<MapPin class="w-3.5 h-3.5" />
						{:else}
							<Sparkles class="w-3.5 h-3.5" />
						{/if}
						{selectedImage.subtitle}
					</span>
				</div>
			</div>
		</div>
	</div>
{/if}
