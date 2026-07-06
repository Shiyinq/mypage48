import { client } from './client';
import type { ReplayVideo, ReplayDetailResponse } from '$lib/types/replay';

const REPLAY_API_BASE = 'https://jkt48.gemes.in/replay';
const SRT_BASE_URL = `${REPLAY_API_BASE}/data/srt`;

export const replayApi = {
	getReplayByLiveId: async (liveId: string): Promise<ReplayDetailResponse> => {
		return await client<ReplayDetailResponse>(`/replays/${liveId}`);
	},
	getVideos: async (): Promise<ReplayVideo[]> => {
		return await client<ReplayVideo[]>('/replays');
	},
	getSrt: async (liveId: string): Promise<string> => {
		return await client<string>(`/replays/${liveId}/srt`, { responseType: 'text' });
	},
	getJeketiBotsVideos: async (): Promise<ReplayVideo[]> => {
		const response = await fetch(`${REPLAY_API_BASE}/data/videos.json?t=${Date.now()}`);
		if (!response.ok) throw new Error('Failed to fetch replay videos');
		return response.json();
	},
	getJeketiBotsSrt: async (srtFile: string): Promise<string> => {
		const response = await fetch(`${SRT_BASE_URL}/${srtFile}?t=${Date.now()}`);
		if (!response.ok) throw new Error('Failed to fetch SRT file');
		return response.text();
	}
};
