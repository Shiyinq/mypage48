/**
 * Gift store - migrated to Svelte 5 Shared Rune State.
 * Manages the broadcast of live gift events.
 */

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

let currentEvent = $state<GiftEvent | null>(null);

function createGiftStore() {
	return {
		get value() {
			return currentEvent;
		},

		broadcast: (event: GiftEvent) => {
			currentEvent = event;
		},

		/**
		 * Legacy subscribe method for backward compatibility
		 */
		subscribe: (fn: (val: GiftEvent | null) => void) => {
			$effect.root(() => {
				$effect(() => {
					fn(currentEvent);
				});
			});
			return () => {};
		}
	};
}

export const giftStore = createGiftStore();

// Compatibility export
export const giftEvents = giftStore;

export function broadcastGift(event: GiftEvent) {
	giftStore.broadcast(event);
}
