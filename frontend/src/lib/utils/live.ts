import { showToast } from '$lib/stores/toast.svelte';
import type { LiveStatus, LiveStreamingResponse } from '$lib/types/live';
import type { UserWithProfileStats } from '$lib/types/profile';

/**
 * Checks if a stream is IDN Premium and the user is not an admin.
 * If so, shows a localized toast warning and returns the target URL for redirection.
 * Otherwise returns false.
 */
export function getPremiumLiveRedirectUrl(
	stream: LiveStatus | LiveStreamingResponse,
	userProfileData?: UserWithProfileStats | null,
	t?: (key: string) => string,
	slugFallback?: string
): string | false {
	if (stream.live_type && stream.live_type !== 'public' && !userProfileData?.isAdmin) {
		const msg = t
			? t('theater.live.premium_redirect')
			: 'This is a Premium Live. Redirecting to IDN App...';
		showToast(msg, 'warning');

		const slug = stream.room_id || stream.live_id || slugFallback;

		// Safely extract username from various fallback paths
		const username =
			stream.room_url_key ||
			stream.member?.id ||
			stream.member?.name?.toLowerCase().replace(/\s+/g, '');

		return username ? `https://www.idn.app/${username}/live/${slug}` : `https://www.idn.app`;
	}

	return false;
}
