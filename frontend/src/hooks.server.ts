import type { Handle } from '@sveltejs/kit';
import { env } from '$env/dynamic/public';
import { PUBLIC_SERVER_SIDE_API_BASE_URL } from '$env/static/public';

export const handle: Handle = async ({ event, resolve }) => {
	// Simple health check endpoint for Docker
	if (event.url.pathname === '/health') {
		return new Response('OK', { status: 200 });
	}

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
				body:
					event.request.method !== 'GET' && event.request.method !== 'HEAD'
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
	return resolve(event, {
		transformPageChunk: ({ html }) => {
			if (env.PUBLIC_UMAMI_URL && env.PUBLIC_UMAMI_WEBSITE_ID) {
				const script = `\n\t\t<script async defer src="${env.PUBLIC_UMAMI_URL}/script.js" data-website-id="${env.PUBLIC_UMAMI_WEBSITE_ID}"></script>\n`;
				// Inject before closing head tag
				return html.replace('</head>', `${script}</head>`);
			}
			return html;
		}
	});
};
