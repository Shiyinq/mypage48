<script lang="ts">
	import { tick, onMount } from 'svelte';
	import { replayApi } from '$lib/apis/replay';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { ReplayChatMessage } from '$lib/types/replay';
	import { MessageCircle, Gift, Search, ChevronDown } from 'lucide-svelte';

	const { t } = useTranslation();

	interface Props {
		srtFile: string;
		currentTime: number;
		source?: 'jeketibots' | 'mypage48';
	}

	let { srtFile, currentTime, source = 'jeketibots' }: Props = $props();

	let allMessages: ReplayChatMessage[] = $state([]);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let search = $state('');
	let autoScroll = $state(true);
	let chatContainer: HTMLDivElement | undefined = $state();
	let isFirstLoad = $state(true);
	let newMessageCount = $state(0);
	let prevCount = $state(0);
	let scrollTimer: ReturnType<typeof setTimeout> | undefined;

	onMount(() => {
		return () => clearTimeout(scrollTimer);
	});

	$effect(() => {
		async function fetchSrt() {
			try {
				loading = true;
				error = null;
				let text: string;
				if (source === 'mypage48') {
					text = await replayApi.getSrt(srtFile); // srtFile acts as liveId for mypage48
				} else {
					text = await replayApi.getJeketiBotsSrt(srtFile);
				}
				allMessages = parseSrt(text);
			} catch (e) {
				console.error('Failed to fetch SRT:', e);
				error = t('replay.chat.error');
			} finally {
				loading = false;
			}
		}
		if (srtFile) fetchSrt();
	});

	function parseSrt(srtText: string): ReplayChatMessage[] {
		const entries: ReplayChatMessage[] = [];
		const blocks = srtText.trim().split(/\n\s*\n/);

		for (const block of blocks) {
			const lines = block.trim().split('\n');
			if (lines.length < 3) continue;

			const timeLine = lines[1];
			const textLine = lines.slice(2).join(' ');

			const timeMatch = timeLine.match(
				/(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})/
			);
			if (!timeMatch) continue;

			const startSeconds =
				parseInt(timeMatch[1]) * 3600 +
				parseInt(timeMatch[2]) * 60 +
				parseInt(timeMatch[3]) +
				parseInt(timeMatch[4]) / 1000;

			const isGift = textLine.startsWith('[GIFT] ');
			const cleanText = isGift ? textLine.replace('[GIFT] ', '') : textLine;
			const colonIndex = cleanText.indexOf(': ');

			let username: string;
			let message: string;
			if (colonIndex !== -1) {
				username = cleanText.substring(0, colonIndex).trim();
				message = cleanText.substring(colonIndex + 2).trim();
			} else {
				username = 'Unknown';
				message = cleanText;
			}

			entries.push({
				id: parseInt(lines[0]),
				startTime: startSeconds,
				username,
				message,
				isGift
			});
		}

		return entries;
	}

	function formatTime(seconds: number): string {
		const hrs = Math.floor(seconds / 3600);
		const mins = Math.floor((seconds % 3600) / 60);
		const secs = Math.floor(seconds % 60);
		if (hrs > 0) {
			return `${hrs}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
		}
		return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
	}

	let visibleMessages = $derived.by(() => {
		let msgs = allMessages.filter((msg) => msg.startTime <= currentTime);

		if (search) {
			const searchLower = search.toLowerCase();
			msgs = msgs.filter(
				(msg) =>
					msg.username.toLowerCase().includes(searchLower) ||
					msg.message.toLowerCase().includes(searchLower)
			);
		}
		return msgs.slice(-100);
	});

	$effect(() => {
		if (!chatContainer) return;
		const count = visibleMessages.length;

		if (count > prevCount && !autoScroll && !isFirstLoad && prevCount > 0) {
			newMessageCount += count - prevCount;
			clearTimeout(scrollTimer);
			scrollTimer = setTimeout(() => {
				if (chatContainer && newMessageCount > 0) {
					chatContainer.scrollTo({ top: chatContainer.scrollHeight, behavior: 'smooth' });
					newMessageCount = 0;
					autoScroll = true;
				}
			}, 8000);
		}
		prevCount = count;

		if (isFirstLoad || autoScroll) {
			tick().then(() => {
				if (chatContainer) {
					chatContainer.scrollTo({
						top: chatContainer.scrollHeight,
						behavior: isFirstLoad ? 'auto' : 'smooth'
					});
					isFirstLoad = false;
				}
			});
		}
	});

	function handleScroll() {
		if (!chatContainer) return;
		const diff = chatContainer.scrollHeight - chatContainer.scrollTop - chatContainer.clientHeight;
		autoScroll = diff < 60;
		if (autoScroll) {
			newMessageCount = 0;
			clearTimeout(scrollTimer);
		}
	}

	function scrollToBottom() {
		if (!chatContainer) return;
		chatContainer.scrollTo({ top: chatContainer.scrollHeight, behavior: 'smooth' });
		newMessageCount = 0;
		autoScroll = true;
		clearTimeout(scrollTimer);
	}
</script>

<div class="flex flex-col flex-1 relative overflow-hidden min-h-0">
	<div
		class="flex items-center justify-between px-4 py-3 border-b border-slate-200 dark:border-zinc-800 flex-shrink-0"
	>
		<div class="flex items-center gap-2">
			<span class="w-2 h-2 rounded-full bg-sky-500 animate-pulse"></span>
			<span class="text-xs font-black uppercase tracking-widest text-slate-900 dark:text-zinc-100"
				>{t('replay.chat.header')}</span
			>
		</div>
		<span class="text-[10px] font-bold text-slate-400 dark:text-zinc-500 uppercase tracking-wider">
			{allMessages.length.toLocaleString()}
			{t('replay.chat.messages')}
		</span>
	</div>

	<div class="px-3 py-2 border-b border-slate-200 dark:border-zinc-800 flex-shrink-0">
		<div class="relative">
			<Search size={14} class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
			<input
				type="text"
				class="w-full pl-9 pr-3 py-2 bg-slate-50 dark:bg-zinc-900 border border-slate-300 dark:border-zinc-700 rounded-lg text-xs text-slate-900 dark:text-zinc-200 placeholder-slate-400 dark:placeholder-zinc-500 outline-none focus:border-sky-500 transition-colors"
				placeholder={t('replay.chat.searchPlaceholder')}
				bind:value={search}
			/>
		</div>
	</div>

	{#if loading}
		<div class="flex flex-col items-center justify-center py-16 text-slate-400 gap-3">
			<div
				class="w-8 h-8 border-2 border-slate-300 dark:border-zinc-700 border-t-sky-500 rounded-full animate-spin"
			></div>
			<p class="text-xs">{t('replay.chat.loading')}</p>
		</div>
	{:else if error}
		<div class="flex flex-col items-center justify-center py-16 text-slate-400 gap-3">
			<MessageCircle size={32} class="text-slate-300 dark:text-zinc-700" />
			<p class="text-xs">{error}</p>
		</div>
	{:else}
		<div
			bind:this={chatContainer}
			onscroll={handleScroll}
			class="flex-1 p-4 overflow-y-auto flex flex-col gap-3 scroll-smooth"
			class:scrollbar-hide={autoScroll}
			class:custom-scrollbar={!autoScroll}
		>
			{#if visibleMessages.length === 0}
				<div class="flex flex-col items-center justify-center text-center py-20 opacity-40">
					<MessageCircle size={32} class="text-slate-300 dark:text-zinc-700 mb-2" />
					<p class="text-xs font-bold uppercase tracking-widest text-slate-400">
						{currentTime === 0
							? t('replay.chat.startPlaying')
							: search
								? t('replay.chat.notFound')
								: t('replay.chat.noChatAtTime')}
					</p>
				</div>
			{:else}
				{#each visibleMessages as msg (msg.id)}
					<div class="flex items-start gap-3 group">
						<div
							class="w-8 h-8 rounded-full bg-slate-100 dark:bg-zinc-800 flex items-center justify-center text-[10px] font-bold text-slate-400 shrink-0"
						>
							{msg.username[0]}
						</div>
						<div class="flex-1 min-w-0">
							<p class="text-[11px] font-bold text-slate-500 dark:text-zinc-500 mb-0.5 truncate">
								{#if msg.isGift}
									<Gift size={11} class="inline text-yellow-500 mr-0.5" />
								{/if}
								{msg.username}
								<span class="text-[10px] text-slate-400 dark:text-zinc-600 ml-2 font-normal"
									>{formatTime(msg.startTime)}</span
								>
							</p>
							{#if msg.isGift}
								<div
									class="inline-flex items-center gap-2 px-4 py-2 rounded-2xl rounded-tl-none bg-yellow-50 dark:bg-yellow-500/15 border border-yellow-200 dark:border-yellow-500/30 text-yellow-800 dark:text-yellow-200 text-sm font-bold shadow-sm max-w-full"
								>
									<Gift size={14} class="text-yellow-500 shrink-0" />
									{msg.message}
								</div>
							{:else}
								<div
									class="inline-block px-3 py-2 rounded-2xl rounded-tl-none bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-zinc-100 text-sm leading-relaxed shadow-sm break-words overflow-wrap-anywhere whitespace-pre-wrap max-w-full"
								>
									{msg.message}
								</div>
							{/if}
						</div>
					</div>
				{/each}
			{/if}
		</div>
		{#if newMessageCount > 0}
			<button
				onclick={scrollToBottom}
				class="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-2 px-4 py-2 rounded-full bg-red-600 hover:bg-red-700 text-white text-[11px] font-bold shadow-lg transition-all cursor-pointer z-10"
			>
				{newMessageCount}
				<ChevronDown size={14} />
			</button>
		{/if}
	{/if}
</div>
