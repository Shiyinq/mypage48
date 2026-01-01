<script lang="ts">
	import { X, Calendar, MapPin, Sparkles } from 'lucide-svelte';
	import { fade, scale } from 'svelte/transition';
	import type { Ticket } from '$lib/types';

	interface MemoryItem {
		uniqueId: string;
		type: 'TICKET' | '2SHOT';
		imageUrl: string;
		date: string;
		time: string;
		title: string;
		subtitle: string;
		notes?: string;
		originalTicket: Ticket;
	}

	export let selectedImage: MemoryItem | null = null;
	export let onClose: () => void;
</script>

{#if selectedImage}
	<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
	<div
		class="fixed inset-0 z-[9999] flex flex-col items-center justify-center p-4 bg-black/90 backdrop-blur-md cursor-pointer"
		transition:fade={{ duration: 200 }}
		on:click={onClose}
	>
		<button
			on:click={(e) => {
				e.stopPropagation();
				onClose();
			}}
			class="absolute top-4 right-4 p-3 bg-white/10 hover:bg-white/20 text-white rounded-full transition-colors z-50 backdrop-blur-sm cursor-pointer"
		>
			<X class="w-6 h-6" />
		</button>

		<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-noninteractive-element-interactions -->
		<div
			class="flex flex-col items-center pointer-events-none"
			transition:scale={{ duration: 300, start: 0.95 }}
		>
			<img
				src={selectedImage.imageUrl}
				alt={selectedImage.title}
				class="max-h-[70vh] w-auto object-contain rounded-lg shadow-2xl border border-white/10 cursor-default pointer-events-auto"
				on:click={(e) => e.stopPropagation()}
			/>

			<div
				class="mt-6 text-center w-full max-w-lg pointer-events-auto"
				on:click={(e) => e.stopPropagation()}
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
						{new Date(selectedImage.date).toLocaleDateString('id-ID', {
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
