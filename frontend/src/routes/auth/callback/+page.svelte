<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { accessToken } from '$lib/store/auth';
	import { auth } from '$lib/apis/auth';

	onMount(async () => {
		try {
			// Get access token from HTTP-only cookie via refresh endpoint
			// The token was already set in cookie by the OAuth callback
			const data = await auth.refresh();
			accessToken.set(data.access_token);
		} catch (error) {
			console.error('Failed to refresh token:', error);
		}

		// Redirect to home
		goto('/', { replaceState: true });
	});
</script>

<div class="callback-container">
	<div class="spinner"></div>
</div>

<style>
	.callback-container {
		height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		background-color: var(--color-bg);
	}

	.spinner {
		width: 3rem;
		height: 3rem;
		border: 3px solid var(--color-primary);
		border-right-color: transparent;
		border-radius: 50%;
		animation: spin 0.8s linear infinite;
	}

	@keyframes spin {
		100% {
			transform: rotate(360deg);
		}
	}
</style>
