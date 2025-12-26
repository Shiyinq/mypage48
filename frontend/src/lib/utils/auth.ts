export function getCookie(name: string): string | null {
	if (typeof document === 'undefined') return null; // Server-side guard
	const value = `; ${document.cookie}`;
	const parts = value.split(`; ${name}=`);
	if (parts.length === 2) return parts.pop()?.split(';').shift() || null;
	return null;
}

export function getCSRFToken(): string {
	return getCookie('csrf_token') || '';
}

export function isTokenExpired(token: string): boolean {
	if (!token) return true;
	try {
		const payload = JSON.parse(atob(token.split('.')[1]));
		if (!payload.exp) return false;
		const currentTime = Math.floor(Date.now() / 1000);
		// Add a small buffer (e.g. 10s) to avoid edge cases
		return payload.exp < currentTime + 10;
	} catch (e) {
		return true;
	}
}
