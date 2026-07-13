import { live as liveApi } from '$lib/apis/live';
import type { LiveChatShowroomMessage } from '$lib/types';
import { logger } from '$lib/utils/logger';

interface ShowroomChatState {
	messages: LiveChatShowroomMessage[];
	status: 'connecting' | 'connected' | 'disconnected';
	loading: boolean;
	error: string | null;
}

const initialState: ShowroomChatState = {
	messages: [],
	status: 'connecting',
	loading: true,
	error: null
};

const state = $state<ShowroomChatState>(initialState);

// Private variables for polling and mapping
let currentRoomId = '';
let lastCommentTime = 0;
let lastGiftTime = 0;
let isFirstLoad = true;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let giftListCache: Record<number, any> = {};

let commentInterval: ReturnType<typeof setInterval> | null = null;
let giftInterval: ReturnType<typeof setInterval> | null = null;

function createShowroomChatStore() {
	return {
		get messages() {
			return state.messages;
		},
		get status() {
			return state.status;
		},
		get loading() {
			return state.loading;
		},
		get error() {
			return state.error;
		},
		get isFirstLoad() {
			return isFirstLoad;
		},
		setIsFirstLoad: (val: boolean) => {
			isFirstLoad = val;
		},

		init: async (roomId: string) => {
			if (currentRoomId === roomId) return;

			currentRoomId = roomId;
			state.messages = [];
			state.status = 'connecting';
			state.loading = true;
			state.error = null;
			lastCommentTime = 0;
			lastGiftTime = 0;
			isFirstLoad = true;
			giftListCache = {};

			if (commentInterval) clearInterval(commentInterval);
			if (giftInterval) clearInterval(giftInterval);

			await showroomChatStore.fetchGiftList(roomId);
			await showroomChatStore.fetchComments();
			await showroomChatStore.fetchGifts();

			commentInterval = setInterval(showroomChatStore.fetchComments, 4000);
			giftInterval = setInterval(showroomChatStore.fetchGifts, 5000);

			state.loading = false;
		},

		cleanup: () => {
			currentRoomId = '';
			if (commentInterval) clearInterval(commentInterval);
			if (giftInterval) clearInterval(giftInterval);
			state.messages = [];
			state.status = 'disconnected';
		},

		fetchGiftList: async (roomId: string) => {
			try {
				const data = await liveApi.getShowroomGiftList(roomId);
				const items = data?.normal || data || [];
				// eslint-disable-next-line @typescript-eslint/no-explicit-any
				items.forEach((g: any) => {
					if (g.gift_id) {
						giftListCache[g.gift_id] = {
							gift_name: g.gift_name || 'Unknown',
							image: g.image || ''
						};
					}
				});
			} catch (e) {
				logger.error('Failed to fetch Showroom gift list', e);
			}
		},

		fetchComments: async () => {
			if (!currentRoomId) return;
			try {
				const data = await liveApi.getShowroomComments(currentRoomId);
				if (data && data.comment_log) {
					state.status = 'connected';
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

						// eslint-disable-next-line @typescript-eslint/no-explicit-any
						const mapped = newComments.map((c: any, index: number) => ({
							id: `comment-${c.user_id}-${c.created_at}-${index}`,
							user: c.name || 'Anonymous',
							avatar: c.avatar_url,
							text: c.comment,
							isGift: false
						}));
						showroomChatStore.addMessages(mapped);
					}
				}
			} catch (e) {
				logger.error('Failed to fetch Showroom comments', e);
				state.error = 'Failed to load comments';
			}
		},

		fetchGifts: async () => {
			if (!currentRoomId) return;
			try {
				const data = await liveApi.getShowroomGifts(currentRoomId);
				if (data && data.gift_log) {
					const gifts = data.gift_log.reverse();
					const newGifts = gifts.filter((g: { created_at: number }) => g.created_at > lastGiftTime);

					if (newGifts.length > 0) {
						lastGiftTime = Math.max(...newGifts.map((g: { created_at: number }) => g.created_at));

						// eslint-disable-next-line @typescript-eslint/no-explicit-any
						const mappedGifts = newGifts.map((g: any, index: number) => {
							const meta = giftListCache[g.gift_id] || {};
							const realGiftName = meta.gift_name || `Gift ${g.gift_id}`;
							const realGiftImage = meta.image || g.image || '';
							return {
								id: `gift-${g.user_id}-${g.created_at}-${index}`,
								user: g.name || 'Anonymous',
								avatar: g.avatar_url,
								text: '',
								isGift: true,
								gift: {
									name: realGiftName,
									num: g.num,
									img: realGiftImage
								}
							};
						});
						showroomChatStore.addMessages(mappedGifts);
					}
				}
			} catch (e) {
				logger.error('Failed to fetch Showroom gifts', e);
			}
		},

		addMessages: (newMessages: LiveChatShowroomMessage[]) => {
			const existingIds = new Set(state.messages.map((m) => m.id));
			const uniqueNew = newMessages.filter((m) => !existingIds.has(m.id));
			if (uniqueNew.length > 0) {
				state.messages = [...state.messages, ...uniqueNew].slice(-100);
			}
		}
	};
}

export const showroomChatStore = createShowroomChatStore();
