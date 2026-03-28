/**
 * Builds a proxied URL for external media (jkt48.com storage).
 */
export function getExternalMediaUrl(path: string | null | undefined): string {
	if (!path) return '';
	const cleanPath = path.replace(/^\/+/, '');
	return `/api/storage/external/${cleanPath}`;
}

/**
 * Capture a screenshot from a video element and trigger a download.
 */
export function captureVideoScreenshot(video: HTMLVideoElement, memberName?: string) {
	if (!video) return;

	try {
		const canvas = document.createElement('canvas');
		canvas.width = video.videoWidth;
		canvas.height = video.videoHeight;
		const ctx = canvas.getContext('2d');

		if (ctx) {
			ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
			const dataUrl = canvas.toDataURL('image/png');
			const link = document.createElement('a');
			const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
			const name = memberName ? memberName.replace(/\s+/g, '_') : 'JKT48_Live';
			link.download = `Screenshot_${name}_${timestamp}.png`;
			link.href = dataUrl;
			link.click();
		}
	} catch (err) {
		console.error('Screenshot failed:', err);
	}
}

/**
 * Helper to get supported mime types for MediaRecorder
 */
export function getSupportedVideoMimeType(): string {
	const types = [
		'video/webm;codecs=vp9,opus',
		'video/webm;codecs=vp8,opus',
		'video/webm',
		'video/mp4'
	];
	return types.find((type) => MediaRecorder.isTypeSupported(type)) || '';
}

/**
 * Handle video recording logic. Returns a MediaRecorder instance.
 */
export async function startVideoRecording(
	video: HTMLVideoElement,
	onData: (blob: Blob) => void
): Promise<MediaRecorder | null> {
	if (!video) return null;

	try {
		const v = video as any;
		let stream = v['captureStream'] ? v['captureStream']() : v['mozCaptureStream']();

		// Zero-Loss Strategy: Check for tracks INSTANTLY
		if (stream.getTracks().length === 0) {
			await new Promise((r) => setTimeout(r, 200));
			stream = v['captureStream'] ? v['captureStream']() : v['mozCaptureStream']();
		}

		const mimeType = getSupportedVideoMimeType();
		const mediaRecorder = new MediaRecorder(stream, mimeType ? { mimeType } : {});

		mediaRecorder.ondataavailable = (e: any) => {
			if (e.data.size > 0) {
				onData(e.data);
			}
		};

		mediaRecorder.start();
		return mediaRecorder;
	} catch (err) {
		console.error('Recording failed to start:', err);
		return null;
	}
}

/**
 * Download recorded video chunks as a file.
 */
export function downloadRecording(chunks: Blob[], memberName?: string) {
	if (chunks.length === 0) return;

	const mimeType = getSupportedVideoMimeType();
	const blob = new Blob(chunks, { type: mimeType || 'video/webm' });
	const url = URL.createObjectURL(blob);
	const link = document.createElement('a');
	const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
	const name = memberName ? memberName.replace(/\s+/g, '_') : 'JKT48_Live';
	const ext = mimeType.includes('mp4') ? 'mp4' : 'webm';

	link.href = url;
	link.download = `Recording_${name}_${timestamp}.${ext}`;
	link.click();
	URL.revokeObjectURL(url);
}
