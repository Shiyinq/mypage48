<script lang="ts">
	import { tickets } from '$lib/stores';
	import {
		Image as ImageIcon,
		MapPin,
		Calendar,
		Ticket as TicketIcon,
		Camera,
		Grid,
		X,
		User,
		Sparkles
	} from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { fade, scale } from 'svelte/transition';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	type FilterType = 'ALL' | 'TICKET' | '2SHOT';

	interface MemoryItem {
		uniqueId: string;
		type: 'TICKET' | '2SHOT';
		imageUrl: string;
		date: string;
		time: string;
		title: string;
		subtitle: string;
		notes?: string;
		originalTicket: any;
	}

	let filter: FilterType = 'ALL';
	let selectedImage: MemoryItem | null = null;

	// Derived
	$: memoryItems = (() => {
		const items: MemoryItem[] = [];
		$tickets.forEach((ticket) => {
			// 1. Ticket Image
			if (ticket.imageUrl) {
				items.push({
					uniqueId: `${ticket._id}-ticket`,
					type: 'TICKET',
					imageUrl: ticket.imageUrl,
					date: ticket.event.date,
					time: ticket.event.time,
					title: ticket.event.title,
					subtitle: `${ticket.seat.section}-${ticket.seat.number}`,
					notes: ticket.notes,
					originalTicket: ticket
				});
			}
			// 2. 2-Shot Image
			if (ticket.two_shot?.imageUrl) {
				items.push({
					uniqueId: `${ticket._id}-2shot`,
					type: '2SHOT',
					imageUrl: ticket.two_shot.imageUrl,
					date: ticket.event.date,
					time: ticket.event.time,
					title: `2-Shot: ${ticket.two_shot.member_name}`,
					subtitle: ticket.two_shot.type, // Roulette / Birthday
					notes: ticket.notes,
					originalTicket: ticket
				});
			}
		});
		return items.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
	})();

	$: filteredItems =
		filter === 'ALL' ? memoryItems : memoryItems.filter((item) => item.type === filter);

	// Scroll lock
	$: if (typeof document !== 'undefined') {
		document.body.style.overflow = selectedImage ? 'hidden' : 'unset';
	}
</script>

<SEO title={$t('memories.title')} path="/memories" description={$t('seo.memories')} />

<!-- Lightbox -->
{#if selectedImage}
	<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
	<div
		class="fixed inset-0 z-[9999] flex flex-col items-center justify-center p-4 bg-black/90 backdrop-blur-md cursor-pointer"
		transition:fade={{ duration: 200 }}
		on:click={() => (selectedImage = null)}
	>
		<button
			on:click={(e) => {
				e.stopPropagation();
				selectedImage = null;
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

<div class="max-w-7xl mx-auto p-4 pb-32 animate-fade-in">
	<!-- Header -->
	<div class="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8">
		<div class="flex items-center gap-3">
			<div
				class="p-3 rounded-2xl bg-pink-50 dark:bg-pink-900/30 text-pink-500 dark:text-pink-400 transform -rotate-6 shadow-lg shadow-pink-100 dark:shadow-pink-900/20 border-2 border-white dark:border-zinc-700"
			>
				<ImageIcon class="w-6 h-6" />
			</div>
			<div>
				<h2 class="text-2xl font-bold text-themed tracking-tight relative w-fit">
					{$t('memories.title')}
					<span
						class="absolute -bottom-1 left-0 w-full h-2 bg-pink-200/60 dark:bg-pink-500/30 -z-10 transform -skew-x-12 rounded-sm"
					></span>
				</h2>
				<p class="text-sm text-themed-secondary mt-1">{$t('memories.subtitle')}</p>
			</div>
		</div>

		<!-- Filter Tabs -->
		<div
			class="bg-white dark:bg-zinc-900 p-1.5 rounded-xl border border-gray-200 dark:border-zinc-700 shadow-sm flex items-center gap-1 w-full md:w-auto overflow-x-auto"
		>
			<button
				on:click={() => (filter = 'ALL')}
				class={`px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2 transition-all whitespace-nowrap cursor-pointer ${filter === 'ALL' ? 'bg-pink-500 text-white shadow-md shadow-pink-200 dark:shadow-pink-900/30' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-zinc-800'}`}
			>
				<Grid class="w-3.5 h-3.5" />
				{$t('memories.allPhotos')}
			</button>
			<button
				on:click={() => (filter = 'TICKET')}
				class={`px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2 transition-all whitespace-nowrap cursor-pointer ${filter === 'TICKET' ? 'bg-red-500 text-white shadow-md shadow-red-200 dark:shadow-red-900/30' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-zinc-800'}`}
			>
				<TicketIcon class="w-3.5 h-3.5" />
				{$t('memories.tickets')}
			</button>
			<button
				on:click={() => (filter = '2SHOT')}
				class={`px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2 transition-all whitespace-nowrap cursor-pointer ${filter === '2SHOT' ? 'bg-purple-500 text-white shadow-md shadow-purple-200 dark:shadow-purple-900/30' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-zinc-800'}`}
			>
				<Camera class="w-3.5 h-3.5" />
				{$t('memories.twoShots')}
			</button>
		</div>
	</div>

	<!-- Gallery Grid -->
	{#if filteredItems.length === 0}
		<div
			class="flex flex-col items-center justify-center min-h-[400px] p-8 text-center border-2 border-dashed border-gray-200 dark:border-zinc-700 rounded-3xl bg-gray-50/50 dark:bg-white/5"
		>
			<div
				class="w-20 h-20 bg-white dark:bg-zinc-800 rounded-full shadow-sm flex items-center justify-center mb-6"
			>
				<ImageIcon class="w-10 h-10 text-gray-300 dark:text-zinc-600" />
			</div>
			<h3 class="text-xl font-bold text-gray-800 dark:text-white mb-2">
				{$t('memories.noMemories')}
			</h3>
			<p class="text-sm text-gray-500 dark:text-gray-400 max-w-md mx-auto">
				{$t('upload.subtitle')}
			</p>
		</div>
	{:else}
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8 md:gap-10 px-4">
			{#each filteredItems as item, index (item.uniqueId)}
				{@const rotation = (index % 5) - 2}
				{@const tapeColor = item.type === '2SHOT' ? 'bg-purple-200/80' : 'bg-red-200/80'}

				<!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
				<div
					class="group relative transition-all duration-500 hover:z-10 hover:scale-105 cursor-pointer"
					style={`transform: rotate(${rotation}deg)`}
					on:click={() => (selectedImage = item)}
				>
					<!-- Washi Tape -->
					<div
						class={`absolute -top-3 left-1/2 -translate-x-1/2 w-24 h-8 ${tapeColor} backdrop-blur-sm opacity-90 z-20 shadow-sm transform rotate-1 clip-path-tape`}
					></div>

					<!-- Polaroid Card -->
					<div
						class="bg-white dark:bg-zinc-900 p-3 pb-12 shadow-xl shadow-gray-200/50 dark:shadow-black/30 border border-gray-100 dark:border-zinc-700 rounded-sm transition-shadow duration-300 group-hover:shadow-2xl relative overflow-hidden"
					>
						<!-- Image Area -->
						<div
							class="aspect-[4/5] w-full bg-gray-100 mb-4 overflow-hidden relative border border-gray-50 grayscale-[20%] group-hover:grayscale-0 transition-all duration-500"
						>
							<img
								src={item.imageUrl}
								alt={item.title}
								class="w-full h-full object-cover"
								loading="lazy"
							/>

							<!-- Date Stamp -->
							<div
								class="absolute bottom-2 right-2 bg-black/50 backdrop-blur-sm text-white text-[10px] font-mono px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity"
							>
								{new Date(item.date).toLocaleDateString('en-GB', {
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
								class={`font-['Poppins'] font-bold text-sm leading-tight mb-1 transition-colors ${item.type === '2SHOT' ? 'text-purple-600 dark:text-purple-400' : 'text-gray-800 dark:text-gray-100 group-hover:text-red-600 dark:group-hover:text-red-400'}`}
							>
								{item.title}
							</h3>

							<div
								class="flex items-center justify-center gap-2 text-[10px] font-medium text-gray-400 uppercase tracking-wider"
							>
								{#if item.type === 'TICKET'}
									<span class="flex items-center gap-0.5"
										><MapPin class="w-3 h-3" /> {item.subtitle}</span
									>
									<span>•</span>
									<span class="flex items-center gap-0.5"
										><Calendar class="w-3 h-3" /> {item.time}</span
									>
								{:else}
									<span class="flex items-center gap-0.5"
										><Sparkles class="w-3 h-3" /> {item.subtitle}</span
									>
									<span>•</span>
									<span class="flex items-center gap-0.5"
										><User class="w-3 h-3" />
										{item.originalTicket.two_shot?.member_name.split(' ')[0]}</span
									>
								{/if}
							</div>
						</div>
					</div>
				</div>
			{/each}
		</div>
	{/if}

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
</div>
