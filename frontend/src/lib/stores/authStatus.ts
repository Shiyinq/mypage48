import { writable } from 'svelte/store';
import { browser } from '$app/environment';

export const AUTH_KEY = 'mypage48_auth';

const initialAuth = browser ? localStorage.getItem(AUTH_KEY) === 'true' : false;
export const isAuthenticated = writable<boolean>(initialAuth);

if (browser) {
	isAuthenticated.subscribe((value) => {
		if (value) {
			localStorage.setItem(AUTH_KEY, 'true');
			document.cookie = `${AUTH_KEY}=true; path=/; max-age=31536000; SameSite=Lax`;
		} else {
			localStorage.removeItem(AUTH_KEY);
			document.cookie = `${AUTH_KEY}=; path=/; max-age=0; SameSite=Lax`;
		}
	});
}
