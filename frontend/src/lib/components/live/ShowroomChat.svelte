<script lang="ts">
	import { onMount, onDestroy, tick } from 'svelte';
	import { fade, slide } from 'svelte/transition';
	import { MessageCircle, RefreshCw } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { API_BASE } from '$lib/apis/client';
	import type { LiveChatShowroomMessage } from '$lib/types';

	interface Props {
		roomId: string;
		onStatusChange?: (status: 'connecting' | 'connected' | 'disconnected') => void;
	}

	let { roomId, onStatusChange }: Props = $props();

	const { t } = useTranslation();

	let messages: LiveChatShowroomMessage[] = $state([]);
	let chatContainer: HTMLElement | undefined = $state();
	let pollingInterval: ReturnType<typeof setInterval> | undefined;
	let lastCommentTime = 0;
	let status: 'connecting' | 'connected' | 'disconnected' = $state('connecting');
	let loading = $state(true);
	let isFirstLoad = true;

	$effect(() => {
		onStatusChange?.(status);
	});

	async function fetchComments() {
		try {
			const res = await fetch(`${API_BASE}/jkt48/live/showroom/comments?room_id=${roomId}`);
			if (!res.ok) throw new Error('Failed to fetch');
			const data = await res.json();

			if (data && data.comment_log) {
				status = 'connected';
				// Filter specifically for comments, not gifts (gifts have comment field too but often special ua)
				// showroom returns latest first, so we reverse it to process chronologically
				const validComments = data.comment_log
					.filter((c: { comment: string }) => c.comment && !c.comment.match(/^\d+$/))
					.reverse();

				const newComments = validComments.filter(
					(c: { created_at: number }) => c.created_at > lastCommentTime
				);

				if (newComments.length > 0) {
					lastCommentTime = Math.max(
						...newComments.map((c: { created_at: number }) => c.created_at)
					);

					const mapped = newComments.map(
						(
							c: {
								user_id: number;
								created_at: number;
								name: string;
								comment: string;
								avatar_url?: string;
							},
							index: number
						) => ({
							id: `${c.user_id}-${c.created_at}-${index}`,
							user: c.name,
							text: c.comment,
							avatar: c.avatar_url
						})
					);

					// Avoid duplicates based on ID
					const existingIds = new Set(messages.map((m) => m.id));
					const uniqueNew = mapped.filter((m: LiveChatShowroomMessage) => !existingIds.has(m.id));

					if (uniqueNew.length > 0) {
						const isAtBottom =
							chatContainer &&
							chatContainer.scrollHeight - chatContainer.scrollTop <=
								chatContainer.clientHeight + 100;
						messages = [...messages, ...uniqueNew].slice(-100);

						// Auto-scroll logic
						if (isFirstLoad || isAtBottom) {
							await tick();
							if (chatContainer) {
								chatContainer.scrollTo({
									top: chatContainer.scrollHeight,
									behavior: isFirstLoad ? 'auto' : 'smooth'
								});
								isFirstLoad = false;
							}
						}
					}
				}
			}
			loading = false;
		} catch (e) {
			console.error('Failed to fetch Showroom comments:', e);
			status = 'disconnected';
		}
	}

	onMount(() => {
		fetchComments();
		pollingInterval = setInterval(fetchComments, 4000); // 4 seconds interval to be safe
	});

	onDestroy(() => {
		if (pollingInterval) clearInterval(pollingInterval);
	});
</script>

<div class="flex-1 min-h-0 flex flex-col overflow-hidden">
	<div
		bind:this={chatContainer}
		class="flex-1 p-4 overflow-y-auto flex flex-col gap-3 scroll-smooth"
	>
		{#if status === 'disconnected'}
			<div
				class="bg-red-500/10 border border-red-500/20 rounded-2xl p-3 flex flex-col items-center gap-2 mb-2 shrink-0"
				transition:fade
			>
				<div class="flex items-center gap-2">
					<div class="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
					<span class="text-[10px] font-black uppercase tracking-widest text-red-500"
						>{$t('theater.live.disconnected')}</span
					>
				</div>
				<p class="text-[9px] text-red-500/60 font-medium text-center leading-relaxed">
					{$t('theater.live.reconnect_showroom')}
				</p>
			</div>
		{:else if status === 'connecting'}
			<div class="flex items-center justify-center gap-2 py-4 opacity-50 shrink-0" transition:fade>
				<RefreshCw size={12} class="animate-spin text-slate-400" />
				<span class="text-[10px] font-bold uppercase tracking-widest text-slate-400"
					>{$t('theater.live.connecting')}</span
				>
			</div>
		{/if}

		{#if messages.length === 0 && status === 'connected'}
			<div
				class="text-[10px] text-center text-slate-400 py-4 font-bold uppercase tracking-widest flex items-center gap-4 before:h-px before:flex-1 before:bg-slate-100 dark:before:bg-zinc-900 after:h-px after:flex-1 after:bg-slate-100 dark:after:bg-zinc-900"
			>
				{$t('theater.live.chat_started')}
			</div>
		{/if}

		{#each messages as msg (msg.id)}
			<div class="flex items-start gap-3 group">
				{#if msg.avatar}
					<img
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
					<div
						class="inline-block px-3 py-2 rounded-2xl rounded-tl-none bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-zinc-100 text-sm leading-relaxed shadow-sm break-words overflow-wrap-anywhere whitespace-pre-wrap max-w-full"
					>
						{msg.text}
					</div>
				</div>
			</div>
		{/each}

		{#if messages.length === 0 && !loading}
			<div class="flex-1 flex flex-col items-center justify-center text-center py-20 opacity-40">
				<MessageCircle size={32} class="text-slate-300 dark:text-zinc-700 mb-2" />
				<p class="text-xs font-bold uppercase tracking-widest text-slate-400">
					{$t('theater.live.multiview.no_messages')}
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
