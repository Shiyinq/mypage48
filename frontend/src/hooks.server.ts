import type { Handle } from '@sveltejs/kit';
import { PUBLIC_SERVER_SIDE_API_BASE_URL } from '$env/static/public';

export const handle: Handle = async ({ event, resolve }) => {
	// If the request is for /api, proxy it to the backend
	if (event.url.pathname.startsWith('/api')) {
		const targetUrl = event.url.pathname.replace('/api', PUBLIC_SERVER_SIDE_API_BASE_URL);
		
		// Create a new request to the backend
		const requestHeaders = new Headers(event.request.headers);
		
		// Ensure host header matches target
		const targetUrlObj = new URL(targetUrl);
		requestHeaders.set('host', targetUrlObj.host);

		try {
			const response = await fetch(targetUrl + event.url.search, {
				method: event.request.method,
				headers: requestHeaders,
				body: event.request.method !== 'GET' && event.request.method !== 'HEAD' 
					? await event.request.arrayBuffer() 
					: undefined,
                // @ts-ignore - duplex is needed for streaming bodies in some environments
                duplex: 'half'
			});

			return response;
		} catch (error) {
			console.error('Proxy error:', error);
			return new Response('Proxy Error', { status: 502 });
		}
	}

	// For all other requests, continue as normal
	return resolve(event);
};
