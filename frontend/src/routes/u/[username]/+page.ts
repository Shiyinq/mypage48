import { error } from '@sveltejs/kit';
import type { PageLoad } from './$types';
import { API_BASE } from '$lib/apis/client';

export const load: PageLoad = async ({ params, fetch }) => {
	const { username } = params;
	try {
		const res = await fetch(`${API_BASE}/u/${username}`);

		if (res.status === 404) {
			// We can return a specific error object or throw
			throw error(404, {
				message: 'User not found or profile is private'
			});
		}

		if (!res.ok) {
			throw error(res.status, 'Failed to load profile');
		}

		const profile = await res.json();
		return {
			profile
		};
	} catch (err) {
		const e = err as { status?: number; message?: string };
		if (e.status) throw e; // Re-throw SvelteKit errors
		console.error(e);
		throw error(500, 'Could not load profile');
	}
};
