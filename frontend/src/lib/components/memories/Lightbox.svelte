<script lang="ts">
	import {
		Heart,
		X,
		Calendar,
		MapPin,
		Sparkles,
		Trash2,
		Download,
		LoaderCircle
	} from 'lucide-svelte';
	import { fade, scale } from 'svelte/transition';
	import { formatDate } from '$lib/i18n';
	import type { MemoryItem } from '$lib/types';
	import { OptimizedImage } from '$lib/components/common';

	interface Props {
		selectedImage?: MemoryItem | null;
		onClose: () => void;
		onfavoriteToggle?: (item: MemoryItem) => void;
		onDeletePhoto?: (item: MemoryItem) => void;
	}

	let { selectedImage = null, onClose, onfavoriteToggle, onDeletePhoto }: Props = $props();
	let isDownloading = $state(false);

	async function downloadImage() {
		if (!selectedImage || isDownloading) return;
		isDownloading = true;
		try {
			const proxyUrl = `/proxy/image?url=${encodeURIComponent(selectedImage.imageUrl)}`;
			const response = await fetch(proxyUrl);
			const blob = await response.blob();
			const url = window.URL.createObjectURL(blob);
			const link = document.createElement('a');
			link.href = url;
			const filename =
				selectedImage.imageUrl.split('/').pop()?.split('?')[0] || selectedImage.title || 'image';
			link.download = filename.includes('.') ? filename : `${filename}.jpg`;
			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);
			window.URL.revokeObjectURL(url);
		} catch (error) {
			console.error('Download failed:', error);
			window.open(`/proxy/image?url=${encodeURIComponent(selectedImage.imageUrl)}`, '_blank');
		} finally {
			isDownloading = false;
		}
	}
</script>

{#if selectedImage}
	{@const image = selectedImage}
	<div
		class="fixed inset-0 z-[10001] flex flex-col items-center justify-center p-4 bg-black/90 backdrop-blur-md cursor-pointer"
		transition:fade={{ duration: 200 }}
		onclick={onClose}
		onkeydown={(e) => e.key === 'Escape' && onClose()}
		role="button"
		tabindex="-1"
		aria-label="Close lightbox"
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

		<div
			class="flex flex-col items-center pointer-events-none"
			transition:scale={{ duration: 300, start: 0.95 }}
		>
			<OptimizedImage
				src={image.imageUrl}
				alt={image.title}
				class="max-h-[70vh] w-auto rounded-lg shadow-2xl border border-white/10 cursor-default pointer-events-auto"
				objectFit="contain"
				onclick={(e: MouseEvent) => e.stopPropagation()}
				onkeydown={(e: KeyboardEvent) => e.stopPropagation()}
			/>

			<div
				class="mt-6 text-center w-full max-w-lg pointer-events-auto"
				onclick={(e: MouseEvent) => e.stopPropagation()}
				onkeydown={(e: KeyboardEvent) => e.stopPropagation()}
				role="presentation"
			>
				<h3 class="text-2xl font-bold text-white tracking-tight drop-shadow-md">
					{image.title}
				</h3>
				<div
					class="flex flex-wrap items-center justify-center gap-1.5 sm:gap-2 text-xs sm:text-sm font-medium text-white/90 mt-3"
				>
					<span
						class="flex items-center gap-1.5 bg-white/10 px-2.5 sm:px-3 py-1.5 rounded-full backdrop-blur-md border border-white/10"
					>
						<Calendar class="w-3.5 h-3.5 sm:w-4 sm:h-4" />
						{formatDate(image.date, {
							day: 'numeric',
							month: 'long',
							year: 'numeric'
						})}
					</span>
					<span
						class="flex items-center gap-1.5 bg-white/10 px-2.5 sm:px-3 py-1.5 rounded-full backdrop-blur-md border border-white/10"
					>
						{#if image.type === 'TICKET'}
							<MapPin class="w-3.5 h-3.5 sm:w-4 sm:h-4" />
						{:else}
							<Sparkles class="w-3.5 h-3.5 sm:w-4 sm:h-4" />
						{/if}
						{image.subtitle}
					</span>
				</div>
				<div class="flex items-center justify-center gap-2 sm:gap-2 mt-2">
					{#if onDeletePhoto}
						<div
							onclick={(e: MouseEvent) => {
								e.stopPropagation();
								onDeletePhoto(image);
							}}
							onkeydown={(e: KeyboardEvent) => {
								if (e.key === 'Enter') {
									onDeletePhoto(image);
								}
							}}
							class="flex items-center justify-center w-9 h-9 sm:w-10 sm:h-10 rounded-full backdrop-blur-md border border-white/10 bg-white/10 cursor-pointer transition-transform hover:scale-105 hover:bg-red-500/20 hover:border-red-500/30 group"
							role="button"
							tabindex="0"
							aria-label="Delete photo"
						>
							<Trash2 class="w-4 h-4 sm:w-5 sm:h-5 text-white/70 group-hover:text-red-400" />
						</div>
					{/if}
					<div
						onclick={(e: MouseEvent) => {
							e.stopPropagation();
							downloadImage();
						}}
						onkeydown={(e: KeyboardEvent) => {
							if (e.key === 'Enter') downloadImage();
						}}
						class="flex items-center justify-center w-9 h-9 sm:w-10 sm:h-10 rounded-full backdrop-blur-md border border-white/10 bg-white/10 cursor-pointer transition-transform hover:scale-105 hover:bg-pink-500/20 hover:border-pink-500/30 group disabled:opacity-50 disabled:cursor-not-allowed"
						role="button"
						tabindex="0"
						aria-label="Download photo"
					>
						{#if isDownloading}
							<LoaderCircle class="w-4 h-4 sm:w-5 sm:h-5 text-pink-400 animate-spin" />
						{:else}
							<Download class="w-4 h-4 sm:w-5 sm:h-5 text-white/70 group-hover:text-pink-400" />
						{/if}
					</div>
					<div
						onclick={(e: MouseEvent) => {
							e.stopPropagation();
							onfavoriteToggle?.(image);
						}}
						onkeydown={(e: KeyboardEvent) => {
							if (e.key === 'Enter') onfavoriteToggle?.(image);
						}}
						class={'flex items-center justify-center w-9 h-9 sm:w-10 sm:h-10 rounded-full backdrop-blur-md border border-white/10 cursor-pointer transition-transform hover:scale-105 ' +
							(image.is_favorite ? 'bg-red-500/20' : 'bg-white/10')}
						role="button"
						tabindex="0"
						aria-label="Toggle favorite"
					>
						<Heart
							class={'w-4 h-4 sm:w-5 sm:h-5 ' +
								(image.is_favorite ? 'fill-current text-red-400' : 'text-white/70')}
						/>
					</div>
				</div>
			</div>
		</div>
	</div>
{/if}
