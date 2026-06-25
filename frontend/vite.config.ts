import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig, type Plugin } from 'vite';
import { SvelteKitPWA } from '@vite-pwa/sveltekit';

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
	plugins: [
		uriFixPlugin(),
		sveltekit(),
		SvelteKitPWA({
			registerType: 'prompt',
			strategies: 'injectManifest',
			srcDir: 'src',
			filename: 'service-worker.ts',
			injectRegister: 'auto',
			devOptions: {
				enabled: false,
				suppressWarnings: true,
				type: 'module'
			},
			manifest: {
				name: 'MyPage48',
				short_name: 'MyPage48',
				description: 'Your Ultimate JKT48 Companion',
				categories: ['entertainment', 'music', 'lifestyle'],
				theme_color: '#ffffff',
				background_color: '#ffffff',
				display: 'standalone',
				icons: [
					{
						src: '/pwa-192x192.png',
						sizes: '192x192',
						type: 'image/png'
					},
					{
						src: '/pwa-512x512.png',
						sizes: '512x512',
						type: 'image/png'
					}
				]
			},
			injectManifest: {
				globPatterns: ['client/**/*.{js,css,ico,png,svg,webp,webmanifest}', 'prerendered/**/*.html']
			}
		})
	],
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
