import type { RequestHandler } from './$types';

export const GET: RequestHandler = async ({ url }) => {
	const imageUrl = url.searchParams.get('url');

	if (!imageUrl) {
		return new Response('Missing url parameter', { status: 400 });
	}

	try {
		// Fetch the image from the server-side to bypass browser CORS.
		const response = await fetch(imageUrl);

		if (!response.ok) {
			return new Response(`Failed to fetch image: ${response.statusText}`, {
				status: response.status
			});
		}

		const buffer = await response.arrayBuffer();

		return new Response(buffer, {
			headers: {
				'Content-Type': response.headers.get('Content-Type') || 'application/octet-stream',
				'Cache-Control': 'public, max-age=86400',
				// Crucial: allow the frontend to read this without CORS issues
				'Access-Control-Allow-Origin': '*'
			}
		});
	} catch (error) {
		console.error('Image proxy error:', error);
		return new Response('Error proxying image', { status: 500 });
	}
};
