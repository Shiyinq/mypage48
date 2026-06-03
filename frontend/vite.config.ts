import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig, type Plugin } from 'vite';

// Plugin to fix malformed URIs (like a naked '%') before they crash Vite/SvelteKit
const uriFixPlugin = (): Plugin => ({
	name: 'uri-fix-plugin',
	configureServer(server) {
		server.middlewares.use((req, res, next) => {
			if (req.url && req.url.includes('%')) {
				try {
					decodeURI(req.url);
				} catch (_) {
					// Replace any '%' that is not followed by two hex digits with '%25'
					req.url = req.url.replace(/%(?![0-9a-fA-F]{2})/g, '%25');
					if (req.originalUrl) {
						req.originalUrl = req.originalUrl.replace(/%(?![0-9a-fA-F]{2})/g, '%25');
					}
				}
			}
			next();
		});
	}
});

export default defineConfig({
	plugins: [uriFixPlugin(), sveltekit()],
	build: {
		sourcemap: false
	},
	server: {
		proxy: {
			'/api': {
				target: 'http://localhost:8000',
				changeOrigin: true
			}
		}
	}
});
