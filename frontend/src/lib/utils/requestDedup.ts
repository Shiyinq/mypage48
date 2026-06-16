/**
 * Request deduplication utility.
 *
 * Prevents duplicate concurrent API calls by tracking in-flight promises per key.
 * If a request with the same key is already in-flight, the existing promise is
 * returned instead of making a new network request.
 *
 * This solves three scenarios:
 * 1. SvelteKit hover-prefetch + click navigation race condition
 * 2. +page.ts load() + onMount() firing simultaneously on manual refresh
 * 3. Reactive $effect triggering multiple loads before first resolves
 *
 * Usage:
 *   const dedup = createRequestDedup();
 *   dedup.execute('key', () => fetch('/api/data'));
 */
export function createRequestDedup() {
	const inflight = new Map<string, Promise<unknown>>();

	return {
		/**
		 * Run fn if no matching in-flight request exists; otherwise return existing promise.
		 * @param key  - Unique identifier for this request (use JSON.stringify for params)
		 * @param fn   - Async factory that performs the actual API call
		 */
		execute<T>(key: string, fn: () => Promise<T>): Promise<T> {
			const existing = inflight.get(key);
			if (existing) return existing as Promise<T>;

			const promise = fn().finally(() => {
				inflight.delete(key);
			}) as Promise<T>;

			inflight.set(key, promise);
			return promise;
		},

		/** True if a request with this key is currently in-flight. */
		isInflight(key: string): boolean {
			return inflight.has(key);
		},

		/** Clear all tracked in-flight requests (call on logout / store reset). */
		clear() {
			inflight.clear();
		}
	};
}
