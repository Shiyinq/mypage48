import { writable } from 'svelte/store';

export interface GiftEvent {
	roomIdentifier: string;
	user: string;
	avatar?: string;
	gift: {
		name: string;
		img: string;
		color?: string;
	};
	timestamp: number;
}

export const giftEvents = writable<GiftEvent | null>(null);

export function broadcastGift(event: GiftEvent) {
	giftEvents.set(event);
}
