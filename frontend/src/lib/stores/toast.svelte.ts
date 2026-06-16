/* 
    Svelte 5 Shared Rune State for Toast Notifications
    Replaces the legacy writable store.
*/

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
	message: string;
	type: ToastType;
}

// Private state
let currentToast = $state<Toast | null>(null);

// Public interface
export const toast = {
	get current() {
		return currentToast;
	},

	set current(value: Toast | null) {
		currentToast = value;
	},

	show(message: string, type: ToastType = 'success') {
		currentToast = { message, type };
		setTimeout(() => {
			if (currentToast?.message === message) {
				currentToast = null;
			}
		}, 3000);
	},

	hide() {
		currentToast = null;
	}
};

// Backward compatibility for function calls
export const showToast = toast.show;
