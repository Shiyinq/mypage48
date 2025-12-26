import { writable } from 'svelte/store';

export type ToastType = 'success' | 'error' | 'info';

export interface Toast {
	id: number;
	message: string;
	type: ToastType;
}

export const toasts = writable<Toast[]>([]);

let idCounter = 0;

export function addToast(message: string, type: ToastType = 'info', duration = 3000) {
	const id = ++idCounter;
	const toast: Toast = { id, message, type };

	toasts.update((all) => [...all, toast]);

	setTimeout(() => {
		removeToast(id);
	}, duration);
}

export function removeToast(id: number) {
	toasts.update((all) => all.filter((t) => t.id !== id));
}
