/// <reference lib="webworker" />
import { precacheAndRoute } from 'workbox-precaching';
import { NavigationRoute, registerRoute } from 'workbox-routing';
import { NetworkOnly } from 'workbox-strategies';

declare let self: ServiceWorkerGlobalScope;

// Precache the assets injected by vite-plugin-pwa (including offline.html)
precacheAndRoute(self.__WB_MANIFEST || []);

// Create a NetworkOnly strategy for navigation requests
const networkOnly = new NetworkOnly();

// Define a fallback route for navigations (SSR pages)
const fallbackRoute = new NavigationRoute(async (params) => {
	try {
		// Attempt to fetch from network first (for SSR pages)
		return await networkOnly.handle(params);
	} catch (_error) {
		// If network fails (offline), return the precached offline page
		const fallbackResponse = await caches.match('/offline', {
			ignoreSearch: true
		});

		if (fallbackResponse) {
			return fallbackResponse;
		}

		// Ultimate fallback if even the offline page isn't cached
		return new Response('You are offline. Please check your internet connection.', {
			status: 503,
			headers: { 'Content-Type': 'text/plain; charset=utf-8' }
		});
	}
});

// Register the route
registerRoute(fallbackRoute);

// Listen for the SKIP_WAITING message from the client (ReloadPrompt)
self.addEventListener('message', (event) => {
	if (event.data && event.data.type === 'SKIP_WAITING') {
		self.skipWaiting();
	}
});

self.addEventListener('activate', (event: ExtendableEvent) => {
	event.waitUntil(self.clients.claim());
});
