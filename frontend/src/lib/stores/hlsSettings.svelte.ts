import { browser } from '$app/environment';

export type HlsLatencyMode = 'realtime' | 'balanced' | 'stable';

export const HLS_MODES = {
	realtime: {
		label: 'Real-time',
		liveSyncDurationCount: 3,
		liveMaxLatencyDurationCount: 6
	},
	balanced: {
		label: 'Balanced',
		liveSyncDurationCount: 6,
		liveMaxLatencyDurationCount: 20
	},
	stable: {
		label: 'Ultra Stable',
		liveSyncDurationCount: 10,
		liveMaxLatencyDurationCount: 40
	}
};

class HlsSettings {
	mode = $state<HlsLatencyMode>('balanced');

	constructor() {
		if (browser) {
			const saved = localStorage.getItem('hlsLatencyMode') as HlsLatencyMode;
			if (saved && HLS_MODES[saved]) {
				this.mode = saved;
			}
		}
	}

	setMode(newMode: HlsLatencyMode) {
		this.mode = newMode;
		if (browser) {
			localStorage.setItem('hlsLatencyMode', newMode);
		}
	}

	get config() {
		return HLS_MODES[this.mode];
	}
}

export const hlsSettings = new HlsSettings();
