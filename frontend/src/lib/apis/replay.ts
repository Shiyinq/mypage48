import type { ReplayVideo } from '$lib/types/replay';

const REPLAY_API_BASE = 'https://jkt48.gemes.in/replay';
const SRT_BASE_URL = `${REPLAY_API_BASE}/data/srt`;

export const replayApi = {
	getVideos: async (): Promise<ReplayVideo[]> => {
		const response = await fetch(`${REPLAY_API_BASE}/data/videos.json?t=${Date.now()}`);
		if (!response.ok) throw new Error('Failed to fetch replay videos');
		return response.json();
	},
	getSrt: async (srtFile: string): Promise<string> => {
		const response = await fetch(`${SRT_BASE_URL}/${srtFile}?t=${Date.now()}`);
		if (!response.ok) throw new Error('Failed to fetch SRT file');
		return response.text();
	}
};
