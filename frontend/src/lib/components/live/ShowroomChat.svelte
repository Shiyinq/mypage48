<script lang="ts">
	import { tick, onDestroy, untrack } from 'svelte';
	import { slide } from 'svelte/transition';
	import { MessageCircle } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { OptimizedImage } from '$lib/components/common';
	import { showroomChatStore } from '$lib/stores/showroomChat.svelte';

	interface Props {
		roomId: string;
		onStatusChange?: (status: 'connecting' | 'connected' | 'disconnected') => void;
	}

	let { roomId, onStatusChange }: Props = $props();

	const { t } = useTranslation();

	let chatContainer: HTMLElement | undefined = $state();
	let isUserAtBottom = $state(true);

	$effect(() => {
		onStatusChange?.(showroomChatStore.status);
	});

	$effect(() => {
		if (roomId) {
			showroomChatStore.init(roomId);
		}
	});

	onDestroy(() => {
		showroomChatStore.cleanup();
	});

	function handleScroll(e: Event) {
		const target = e.target as HTMLElement;
		// 150px threshold for bottom detection
		isUserAtBottom = target.scrollHeight - target.scrollTop <= target.clientHeight + 150;
	}

	// Auto scroll logic when new messages arrive
	$effect(() => {
		// Only react to the number of messages changing
		const msgLength = showroomChatStore.messages.length;

		if (msgLength > 0 && chatContainer) {
			// Untrack to prevent re-running when user manually scrolls
			const atBottom = untrack(() => isUserAtBottom);
			const firstLoad = untrack(() => showroomChatStore.isFirstLoad);

			if (firstLoad || atBottom) {
				tick().then(() => {
					// Add a small delay to ensure the browser has fully calculated the new layout heights
					setTimeout(() => {
						if (chatContainer) {
							chatContainer.scrollTo({
								top: chatContainer.scrollHeight + 1000, // Extra padding to guarantee bottom
								behavior: firstLoad ? 'auto' : 'smooth'
							});
							if (firstLoad) {
								showroomChatStore.setIsFirstLoad(false);
							}
						}
					}, 50);
				});
			}
		}
	});
</script>

<div class="flex-1 min-h-0 flex flex-col overflow-hidden relative">
	<!-- Connection Status Overlay -->
	<div
		class="absolute inset-x-0 top-0 z-30 pointer-events-none p-2 flex flex-col items-center gap-2"
	>
		{#if showroomChatStore.status === 'disconnected'}
			<div
				class="w-full bg-red-500/90 backdrop-blur-md border border-red-400/30 rounded-xl p-2.5 flex items-center justify-center shadow-sm transition-all duration-300 pointer-events-auto"
				transition:slide={{ duration: 300 }}
			>
				<p class="text-[9px] text-white font-medium text-center">
					{t('theater.live.reconnect_idn')}
				</p>
			</div>
		{/if}
	</div>

	<!-- Messages Area -->
	<div
		bind:this={chatContainer}
		onscroll={handleScroll}
		class="flex-1 p-4 overflow-y-auto flex flex-col gap-3 scroll-smooth"
	>
		{#if showroomChatStore.loading && showroomChatStore.messages.length === 0}
			<div class="flex-1 flex flex-col items-center justify-center text-center py-10 opacity-60">
				<div
					class="w-6 h-6 border-2 border-red-500 border-t-transparent rounded-full animate-spin mb-3"
				></div>
				<p class="text-[11px] font-bold text-slate-500 dark:text-zinc-400">
					{t('theater.live.connecting')}
				</p>
			</div>
		{/if}

		{#if showroomChatStore.messages.length === 0 && showroomChatStore.status === 'connected'}
			<div
				class="text-[10px] text-center text-slate-400 py-4 font-bold uppercase tracking-widest flex items-center gap-4 before:h-px before:flex-1 before:bg-slate-100 dark:before:bg-zinc-900 after:h-px after:flex-1 after:bg-slate-100 dark:after:bg-zinc-900"
			>
				{t('theater.live.chat_started')}
			</div>
		{/if}

		{#each showroomChatStore.messages as msg (msg.id)}
			<div class="flex items-start gap-3 group">
				{#if msg.avatar}
					<OptimizedImage
						src={msg.avatar}
						alt={msg.user}
						class="w-8 h-8 rounded-full object-cover border border-gray-100 dark:border-zinc-800"
					/>
				{:else}
					<div
						class="w-8 h-8 rounded-full bg-slate-100 dark:bg-zinc-800 flex items-center justify-center text-[10px] font-bold text-slate-400"
					>
						{msg.user[0]}
					</div>
				{/if}
				<div class="flex-1 min-w-0">
					<p class="text-[11px] font-bold text-slate-500 dark:text-zinc-500 mb-0.5 truncate">
						{msg.user}
					</p>
					{#if msg.isGift && msg.gift}
						<div
							class="inline-flex items-center gap-3 px-3.5 py-2 rounded-2xl rounded-tl-none text-white text-[13px] font-black italic transition-all max-w-full"
							style="background: #19191a;"
						>
							{#if msg.gift.img}
								<OptimizedImage
									src={msg.gift.img}
									alt={msg.gift.name}
									referrerPolicy="no-referrer"
									style="width: 36px; height: 36px;"
									class="object-contain"
									noBackground={true}
								/>
							{/if}
							<div class="flex flex-col justify-center">
								<p
									class="text-[9px] uppercase tracking-tighter mb-0.5 font-bold not-italic w-fit"
									style="background: linear-gradient(to right, #F8B62D, #A4D233, #00AEEF, #B95BA5, #EA5571); -webkit-background-clip: text; -webkit-text-fill-color: transparent;"
								>
									{t('theater.live.multiview.sending_gift')}
								</p>
								<span class="leading-tight">
									{msg.gift.name.toUpperCase()}
									{msg.gift.num > 1 ? `x${msg.gift.num}` : ''}
								</span>
							</div>
						</div>
					{:else}
						<div
							class="inline-block px-3 py-2 rounded-2xl rounded-tl-none bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-zinc-100 text-sm leading-relaxed shadow-sm break-words overflow-wrap-anywhere whitespace-pre-wrap max-w-full"
						>
							{msg.text}
						</div>
					{/if}
				</div>
			</div>
		{/each}

		{#if showroomChatStore.messages.length === 0 && !showroomChatStore.loading && showroomChatStore.status !== 'connected'}
			<div class="flex-1 flex flex-col items-center justify-center text-center py-20 opacity-40">
				<MessageCircle size={32} class="text-slate-300 dark:text-zinc-700 mb-2" />
				<p class="text-xs font-bold uppercase tracking-widest text-slate-400">
					{t('theater.live.multiview.no_messages')}
				</p>
			</div>
		{/if}
	</div>
</div>

<style>
	.overflow-y-auto {
		scrollbar-width: thin;
		scrollbar-color: rgba(0, 0, 0, 0.1) transparent;
		overflow-y: auto !important;
	}

	/* Force scrollbar to be visible for debugging */
	.overflow-y-auto::-webkit-scrollbar {
		width: 6px;
	}
	.overflow-y-auto::-webkit-scrollbar-thumb {
		background: rgba(0, 0, 0, 0.2);
		border-radius: 10px;
	}

	:global(.dark) .overflow-y-auto {
		scrollbar-color: rgba(255, 255, 255, 0.1) transparent;
	}
</style>
