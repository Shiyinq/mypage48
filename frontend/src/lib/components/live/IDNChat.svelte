<script lang="ts">
	import { onMount, onDestroy, afterUpdate, tick } from 'svelte';
	import { MessageCircle } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';
	import type { LiveChatIDNMessage } from '$lib/types';
	import { broadcastGift } from '$lib/stores/gift';

	export let roomIdentifier: string;

	const { t } = useTranslation();

	let socket: WebSocket | null = null;
	let messages: LiveChatIDNMessage[] = [];
	let chatContainer: HTMLElement;
	let connected = false;

	function getExternalMediaUrl(url?: string) {
		if (!url) return '';
		if (url.includes('idn.app')) {
			try {
				const u = new URL(url);
				u.searchParams.delete('timestamp');
				return u.toString();
			} catch (e) {
				return url;
			}
		}
		return url;
	}

	function connect() {
		if (!roomIdentifier) return;

		socket = new WebSocket('wss://chat.idn.app/');

		socket.onopen = () => {
			console.log('IDN Chat: Connected');
			connected = true;

			const userId = Math.floor(Math.random() * 1000000);
			const timestamp = Date.now();
			const uuid = crypto.randomUUID();

			socket?.send(`CAP LS 302\n`);
			socket?.send(`NICK idn-${userId}-${timestamp}\n`);
			socket?.send(`USER ${userId}_${uuid} 0 * null\n`);
			socket?.send(`CAP REQ :idn.app/tags idn.app/commands idn.app/membership\n`);
			socket?.send(`CAP END\n`);
		};

		socket.onmessage = (event) => {
			const data = event.data;
			if (data.startsWith('PING')) {
				socket?.send(data.replace('PING', 'PONG') + '\n');
				return;
			}
			if (data.includes(':Welcome')) {
				socket?.send(`@label=1 JOIN #${roomIdentifier}\n`);
				return;
			}
			if (data.includes('PRIVMSG')) {
				parseIRCMessage(data);
			}
		};

		socket.onclose = () => {
			connected = false;
			setTimeout(connect, 5000);
		};
	}

	let isFirstLoad = true;

	async function parseIRCMessage(raw: string) {
		try {
			const parts = raw.split(' ');
			let tags: Record<string, string> = {};

			if (raw.startsWith('@')) {
				const tagString = parts[0].substring(1);
				tagString.split(';').forEach((t) => {
					const [key, value] = t.split('=');
					tags[key] = decodeURIComponent(value || '');
				});
			}

			const messageIdx = raw.indexOf(' :', raw.indexOf('PRIVMSG'));
			if (messageIdx === -1) return;
			const text = raw.substring(messageIdx + 2).trim();

			let parsedText = text;
			let senderName = tags['display-name'] || tags['idn.app/display-name'] || 'User';
			let avatar = tags['idn.app/avatar'];
			let isGift = false;
			let giftData: { name: string; img: string; color?: string } | undefined = undefined;

			if (text.startsWith('{')) {
				try {
					const json = JSON.parse(text);

					// Hydrate user info first
					if (json.user) {
						senderName =
							json.user.name || json.user.display_name || json.user.username || senderName;
						avatar = json.user.avatar_url || avatar;
					}

					if (json.gift) {
						isGift = true;
						const g = json.gift;
						giftData = {
							name: g.name,
							img:
								g.image_url ||
								g.image ||
								g.icon_url ||
								g.icon ||
								g.sticker_url ||
								g.animation_large_url ||
								g.animation_large ||
								g.animation_url,
							color: g.bg_color
						};
						broadcastGift({
							roomIdentifier,
							user: senderName,
							avatar,
							gift: giftData,
							timestamp: Date.now()
						});
						parsedText = `GIFT: ${g.name}`;
					} else if (json.chat && json.chat.message) {
						parsedText = json.chat.message;
					} else if (json.system && json.system.message) {
						parsedText = json.system.message;
					} else {
						parsedText = json.message || json.text || parsedText;
					}
				} catch (e) {}
			} else if (text.startsWith('***')) {
				return;
			}

			const isAtBottom =
				chatContainer &&
				chatContainer.scrollHeight - chatContainer.scrollTop <= chatContainer.clientHeight + 100;

			messages = [
				...messages,
				{
					id: crypto.randomUUID(),
					user: senderName,
					text: parsedText,
					avatar,
					timestamp: Date.now(),
					type: isGift ? 'gift' : 'chat',
					gift: giftData
				}
			];
			if (messages.length > 100) messages = messages.slice(-100);

			// Auto-scroll
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
		} catch (e) {
			console.error('Failed to parse IRC message:', e);
		}
	}

	onMount(() => {
		connect();
	});

	onDestroy(() => {
		if (socket) {
			socket.close();
		}
	});

	function handleMediaError(e: any) {
		if (e.currentTarget instanceof HTMLElement) {
			e.currentTarget.style.display = 'none';
		}
	}
</script>

<div class="flex-1 min-h-0 flex flex-col overflow-hidden">
	<div
		bind:this={chatContainer}
		class="flex-1 p-4 overflow-y-auto flex flex-col gap-3 scroll-smooth"
	>
		{#if messages.length === 0}
			<div
				class="text-[10px] text-center text-slate-400 py-4 font-bold uppercase tracking-widest flex items-center gap-4 before:h-px before:flex-1 before:bg-slate-100 dark:before:bg-zinc-900 after:h-px after:flex-1 after:bg-slate-100 dark:after:bg-zinc-900"
			>
				{$t('theater.live.multiview.chat_started')}
			</div>
		{/if}

		{#each messages as msg (msg.id || msg.timestamp + msg.user)}
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
					<p class="text-[11px] font-bold text-slate-500 dark:text-zinc-500 mb-0.5">{msg.user}</p>

					{#if msg.type === 'gift' && msg.gift}
						{@const isLottie = msg.gift.img
							? msg.gift.img.includes('/animation/') ||
								!msg.gift.img.match(/\.(png|jpg|jpeg|webp|gif|svg)$/i)
							: false}
						{@const isRecent = messages
							.filter((m) => m.type === 'gift')
							.slice(-3)
							.some((m) => (m.id || m.timestamp) === (msg.id || msg.timestamp))}
						<div
							class="inline-flex items-center gap-3 px-4 py-2.5 rounded-2xl rounded-tl-none text-white text-sm font-black italic shadow-lg shadow-black/10 transition-all"
							style="background: {msg.gift.color || '#ef4444'}"
						>
							{#if msg.gift.img}
								{#if isLottie && isRecent}
									<lottie-player
										src={getExternalMediaUrl(msg.gift.img)}
										background="transparent"
										speed="1"
										style="width: 50px; height: 50px;"
										class="object-contain drop-shadow-md"
										loop
										autoplay
										on:error={handleMediaError}
									></lottie-player>
								{:else if isLottie}
									<!-- Static fallback for older Lottie gifts to save resources -->
									<div class="w-[50px] h-[50px] flex items-center justify-center opacity-50">
										<MessageCircle size={20} />
									</div>
								{:else}
									<img
										src={getExternalMediaUrl(msg.gift.img)}
										alt={msg.gift.name}
										referrerpolicy="no-referrer"
										style="width: 50px; height: 50px;"
										on:error={handleMediaError}
										class="object-contain drop-shadow-md"
									/>
								{/if}
							{/if}
							<div>
								<p class="text-[10px] uppercase tracking-tighter opacity-80 mb-0.5">
									{$t('theater.live.multiview.sending_gift')}
								</p>
								{msg.gift.name.toUpperCase()}
							</div>
						</div>
					{:else}
						<div
							class="inline-block px-3 py-2 rounded-2xl rounded-tl-none bg-slate-50 dark:bg-zinc-900 text-slate-900 dark:text-zinc-100 text-sm leading-relaxed shadow-sm"
						>
							{msg.text}
						</div>
					{/if}
				</div>
			</div>
		{/each}

		{#if messages.length === 0}
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
