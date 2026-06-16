// See https://kit.svelte.dev/docs/types#app
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}
	namespace svelteHTML {
		// eslint-disable-next-line @typescript-eslint/no-unused-vars
		interface HTMLAttributes<T> {
			onintersect?: (event: CustomEvent<unknown>) => void;
			'on:intersect'?: (event: CustomEvent<unknown>) => void;
		}
	}

	interface YTVideoData {
		video_id: string;
		title: string;
	}

	interface YTPlayer {
		playVideo(): void;
		pauseVideo(): void;
		loadPlaylist(options: {
			listType: string;
			list: string;
			index?: number;
			startSeconds?: number;
		}): void;
		setVolume(volume: number): void;
		nextVideo(): void;
		getVideoData(): YTVideoData | null;
		destroy(): void;
	}

	interface YTEvent {
		target: YTPlayer;
		data: number;
	}

	interface Window {
		YT: {
			Player: new (
				element: HTMLElement | undefined,
				options: {
					height: string;
					width: string;
					playerVars: {
						listType?: string;
						list?: string;
						autoplay?: number;
						controls?: number;
						showinfo?: number;
						rel?: number;
						loop?: number;
					};
					events: {
						onReady?: (event: YTEvent) => void;
						onStateChange?: (event: YTEvent) => void;
					};
				}
			) => YTPlayer;
		};
		onYouTubeIframeAPIReady: () => void;
	}
}

export {};
