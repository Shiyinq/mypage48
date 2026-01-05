import { writable } from 'svelte/store';

// Access token store - kept in separate file to avoid circular dependencies
// This is imported by both client.ts and auth.ts
export const accessToken = writable<string>('');
