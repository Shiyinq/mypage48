/**
 * Navigation state for Page48, kept in its own module so the API client and the
 * component store can both read it without importing each other.
 */

/**
 * Timestamp (ms) of the last browser back/forward navigation, or 0 when none has
 * happened yet.
 *
 * A timestamp rather than a flag: the list endpoints only honour it for a short
 * window while the target page mounts, so an ordinary visit later in the session
 * still fetches fresh data without anyone having to reset anything.
 */
export const page48NavStore = $state<{ viaHistoryAt: number }>({ viaHistoryAt: 0 });

/** Where the activity page was opened from, so its back button can return there. */
export const activityNavStore = $state<{ fromList: boolean }>({ fromList: false });
