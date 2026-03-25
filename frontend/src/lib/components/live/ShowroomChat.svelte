
<script lang="ts">
	import { onMount, onDestroy, tick } from 'svelte';
	import { MessageCircle } from 'lucide-svelte';
	import { API_BASE } from '$lib/apis/client';
	import type { LiveChatShowroomMessage } from '$lib/types';

	export let roomId: string;

	let messages: LiveChatShowroomMessage[] = [];
	let chatContainer: HTMLElement;
	let pollingInterval: any;
	let lastCommentTime = 0;
	let loading = true;
	let isFirstLoad = true;

	async function fetchComments() {
		try {
			const res = await fetch(`${API_BASE}/jkt48/live/showroom/comments?room_id=${roomId}`);
			const data = await res.json();
			
			if (data && data.comment_log) {
				// Filter specifically for comments, not gifts (gifts have comment field too but often special ua)
				// showroom returns latest first, so we reverse it to process chronologically
				const validComments = data.comment_log
					.filter((c: { comment: string }) => c.comment && !c.comment.match(/^\d+$/))
					.reverse();

				const newComments = validComments.filter((c: { created_at: number }) => c.created_at > lastCommentTime);

				if (newComments.length > 0) {
					lastCommentTime = Math.max(...newComments.map((c: { created_at: number }) => c.created_at));
					
					const mapped = newComments.map((c: { user_id: number; created_at: number; name: string; comment: string; avatar_url?: string }, index: number) => ({
						id: `${c.user_id}-${c.created_at}-${index}`,
						user: c.name,
						text: c.comment,
						avatar: c.avatar_url
					}));

					// Avoid duplicates based on ID
					const existingIds = new Set(messages.map(m => m.id));
					const uniqueNew = mapped.filter((m: any) => !existingIds.has(m.id));

					if (uniqueNew.length > 0) {
						const isAtBottom = chatContainer && (chatContainer.scrollHeight - chatContainer.scrollTop <= chatContainer.clientHeight + 100);
						messages = [...messages, ...uniqueNew].slice(-100);
						
						// Auto-scroll logic
						if (isFirstLoad || isAtBottom) {
							setTimeout(() => {
								if (chatContainer) {
									chatContainer.scrollTop = chatContainer.scrollHeight;
									isFirstLoad = false;
								}
							}, 100);
						}
					}
				}
			}
			loading = false;
		} catch (e) {
			console.error('Failed to fetch Showroom comments:', e);
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
		{#if messages.length === 0}
			<div class="text-[10px] text-center text-slate-400 py-4 font-bold uppercase tracking-widest flex items-center gap-4 before:h-px before:flex-1 before:bg-slate-100 dark:before:bg-zinc-900 after:h-px after:flex-1 after:bg-slate-100 dark:after:bg-zinc-900">
				Showroom Chat
			</div>
		{/if}

		{#each messages as msg (msg.id)}
			<div class="flex items-start gap-3 group">
				{#if msg.avatar}
					<img src={msg.avatar} alt={msg.user} class="w-8 h-8 rounded-full object-cover border border-gray-100 dark:border-zinc-800" />
				{:else}
					<div class="w-8 h-8 rounded-full bg-slate-100 dark:bg-zinc-800 flex items-center justify-center text-[10px] font-bold text-slate-400">
						{msg.user[0]}
					</div>
				{/if}
				<div class="flex-1 min-w-0">
					<p class="text-[11px] font-bold text-slate-500 dark:text-zinc-500 mb-0.5">{msg.user}</p>
					<div class="inline-block px-3 py-2 rounded-2xl rounded-tl-none bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-zinc-100 text-sm leading-relaxed shadow-sm">
						{msg.text}
					</div>
				</div>
			</div>
		{/each}

		{#if messages.length === 0 && !loading}
			<div class="flex-1 flex flex-col items-center justify-center text-center py-20 opacity-40">
				<MessageCircle size={32} class="text-slate-300 dark:text-zinc-700 mb-2" />
				<p class="text-xs font-bold uppercase tracking-widest text-slate-400">No messages yet</p>
			</div>
		{/if}
	</div>
</div>

<style>
	.overflow-y-auto {
		scrollbar-width: thin;
		scrollbar-color: rgba(0,0,0,0.1) transparent;
		overflow-y: auto !important;
	}

	/* Force scrollbar to be visible for debugging */
	.overflow-y-auto::-webkit-scrollbar {
		width: 6px;
	}
	.overflow-y-auto::-webkit-scrollbar-thumb {
		background: rgba(0,0,0,0.2);
		border-radius: 10px;
	}
	
	:global(.dark) .overflow-y-auto {
		scrollbar-color: rgba(255,255,255,0.1) transparent;
	}
</style>
