import { browser } from '$app/environment';
import type { PageLoad } from './$types';
import { page48Reads } from '$lib/stores/page48.svelte';
import type { Page48NotificationTab } from '$lib/api/page48';
import { isAuthenticated } from '$lib/stores/authStatus.svelte';

export const load: PageLoad = async ({ url }) => {
	if (!browser || !isAuthenticated.value) return;

	const tab = url.searchParams.get('tab');
	queueMicrotask(() => {
		const request = tab
			? page48Reads.getNotifications(tab as Page48NotificationTab, 20, null)
			: page48Reads.getNotificationOverview();
		void request.catch(() => {});
	});
};
