import { browser } from '$app/environment';
import type { PageLoad } from './$types';
import { page48Reads } from '$lib/stores/page48.svelte';
import { isAuthenticated } from '$lib/stores/authStatus.svelte';

export const load: PageLoad = async ({ url }) => {
	if (!browser || !isAuthenticated.value) return;

	const query = (url.searchParams.get('query') ?? '').trim();
	if (query.length < 2) return;

	const tab = url.searchParams.get('tab');
	queueMicrotask(() => {
		const request =
			tab === 'top'
				? page48Reads.searchTop(query)
				: tab === 'users'
					? page48Reads.searchUsers(query)
					: tab === 'tags'
						? page48Reads.searchTags(query)
						: page48Reads.searchPosts(query, tab === 'media' ? 'media' : 'posts', 20, null);
		void request.catch(() => {});
	});
};
