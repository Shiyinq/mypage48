<script lang="ts">
	import { page } from '$app/stores';
	import { auth } from '$lib/apis/auth';
	import { onMount } from 'svelte';
	import { fade, fly, scale } from 'svelte/transition';

	type VerificationStatus = 'verifying' | 'success' | 'error';

	let status: VerificationStatus = 'verifying';
	let errorMessage = '';

	onMount(async () => {
		const token = $page.url.searchParams.get('token');

		if (!token) {
			status = 'error';
			errorMessage = 'No verification token provided.';
			return;
		}

		try {
			await auth.verifyEmail({ token });
			status = 'success';
		} catch (e: any) {
			status = 'error';
			errorMessage = e.detail || 'Verification failed. Token may be invalid or expired.';
		}
	});
</script>

<svelte:head>
	<title>FASMO | Email Verification</title>
	<meta name="description" content="Verify your email address for FASMO." />
	<meta name="robots" content="noindex, nofollow" />
</svelte:head>

<div class="page-container">
	<div class="content" in:fly={{ y: 50, duration: 800 }}>
		<!-- Visual Section -->
		<div class="visual-pane">
			<div class="header-section">
				{#if status === 'verifying'}
					<h1 in:fade>VERIFYING</h1>
					<p class="subtitle">Confirming your signal. <br />Please wait...</p>
				{:else if status === 'success'}
					<h1 in:fade>VERIFIED</h1>
					<p class="subtitle success">Connection established. <br />You're in the system.</p>
				{:else}
					<h1 in:fade>FAILED</h1>
					<p class="subtitle error">Signal lost. <br />Verification unsuccessful.</p>
				{/if}
			</div>

			<div class="asset-wrapper">
				<img
					src="/assets/background/login.png"
					alt="Verification"
					class="accent-asset {status}"
				/>
			</div>
		</div>

		<!-- Status Section -->
		<div class="interaction-pane glass-pane">
			{#if status === 'verifying'}
				<div class="status-container" in:fade>
					<div class="loader-wrapper">
						<div class="pulse-ring"></div>
						<div class="pulse-ring delay-1"></div>
						<div class="pulse-ring delay-2"></div>
						<div class="center-dot"></div>
					</div>
					<h2 class="status-title">Verifying Email</h2>
					<p class="status-desc">Please wait while we confirm your identity...</p>
				</div>
			{:else if status === 'success'}
				<div class="status-container success" in:scale={{ duration: 500, delay: 200 }}>
					<div class="icon-wrapper success">
						<svg viewBox="0 0 24 24" fill="none" class="status-icon">
							<path
								d="M20 6L9 17L4 12"
								stroke="currentColor"
								stroke-width="2.5"
								stroke-linecap="round"
								stroke-linejoin="round"
							/>
						</svg>
					</div>
					<h2 class="status-title">Email Verified!</h2>
					<p class="status-desc">
						Your email has been successfully verified. You now have full access to FASMO.
					</p>
					<a href="/login" class="cta-button">
						PROCEED TO LOGIN
					</a>
				</div>
			{:else}
				<div class="status-container error" in:scale={{ duration: 500, delay: 200 }}>
					<div class="icon-wrapper error">
						<svg viewBox="0 0 24 24" fill="none" class="status-icon">
							<path
								d="M18 6L6 18M6 6L18 18"
								stroke="currentColor"
								stroke-width="2.5"
								stroke-linecap="round"
								stroke-linejoin="round"
							/>
						</svg>
					</div>
					<h2 class="status-title">Verification Failed</h2>
					<p class="status-desc">
						{errorMessage}
					</p>
					<div class="action-buttons">
						<a href="/login" class="secondary-button">
							Back to Login
						</a>
					</div>
				</div>
			{/if}
		</div>
	</div>
</div>

<style>
	.page-container {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: var(--space-lg);
		position: relative;
	}

	.content {
		width: 100%;
		max-width: 1100px;
		display: grid;
		grid-template-columns: 1fr;
		gap: var(--space-xl);
		align-items: center;
	}

	@media (min-width: 1024px) {
		.content {
			grid-template-columns: 1fr 480px;
		}
	}

	/* Visual Pane */
	.visual-pane {
		display: flex;
		flex-direction: column;
		justify-content: center;
		position: relative;
		z-index: 1;
	}

	.header-section h1 {
		font-size: clamp(3rem, 6vw, 5rem);
		line-height: 0.9;
		margin-bottom: var(--space-md);
		background: linear-gradient(135deg, #fff 0%, rgba(255, 255, 255, 0.7) 100%);
		background-clip: text;
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
	}

	.subtitle {
		font-size: 1.125rem;
		max-width: 400px;
		color: var(--text-muted);
		border-left: 2px solid var(--primary);
		padding-left: var(--space-md);
		transition: border-color 0.5s ease;
	}

	.subtitle.success {
		border-color: var(--success);
	}

	.subtitle.error {
		border-color: var(--error);
	}

	.asset-wrapper {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		z-index: -1;
		width: 100%;
		height: 100%;
		pointer-events: none;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.accent-asset {
		width: 100%;
		max-width: 1050px;
		opacity: 0.6;
		transition: all 0.8s ease;
		filter: drop-shadow(0 0 40px var(--primary-glow));
		animation: float 8s ease-in-out infinite;
	}

	.accent-asset.verifying {
		animation: pulse-glow 2s ease-in-out infinite;
	}

	.accent-asset.success {
		filter: drop-shadow(0 0 60px rgba(0, 255, 157, 0.5));
		opacity: 0.8;
	}

	.accent-asset.error {
		filter: drop-shadow(0 0 60px rgba(255, 77, 77, 0.5));
		opacity: 0.5;
	}

	@keyframes pulse-glow {
		0%, 100% {
			filter: drop-shadow(0 0 40px var(--primary-glow));
			opacity: 0.6;
		}
		50% {
			filter: drop-shadow(0 0 60px var(--primary-glow));
			opacity: 0.8;
		}
	}

	/* Interaction Pane */
	.interaction-pane {
		padding: 48px;
		display: flex;
		flex-direction: column;
		position: relative;
		overflow: hidden;
		min-height: 350px;
		justify-content: center;
	}

	.interaction-pane::before {
		content: '';
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 2px;
		background: linear-gradient(90deg, transparent, var(--primary), transparent);
		transition: background 0.5s ease;
	}

	.interaction-pane:has(.success)::before {
		background: linear-gradient(90deg, transparent, var(--success), transparent);
	}

	.interaction-pane:has(.error)::before {
		background: linear-gradient(90deg, transparent, var(--error), transparent);
	}

	/* Status Container */
	.status-container {
		display: flex;
		flex-direction: column;
		align-items: center;
		text-align: center;
		gap: var(--space-md);
	}

	.status-title {
		font-size: 1.5rem;
		font-weight: 700;
		color: var(--ghost-white);
	}

	.status-desc {
		font-size: 1rem;
		color: var(--text-muted);
		max-width: 320px;
		line-height: 1.6;
	}

	/* Loader Animation */
	.loader-wrapper {
		position: relative;
		width: 80px;
		height: 80px;
		display: flex;
		align-items: center;
		justify-content: center;
		margin-bottom: var(--space-sm);
	}

	.pulse-ring {
		position: absolute;
		width: 100%;
		height: 100%;
		border: 2px solid var(--primary);
		border-radius: 50%;
		animation: pulse-expand 2s ease-out infinite;
		opacity: 0;
	}

	.pulse-ring.delay-1 {
		animation-delay: 0.4s;
	}

	.pulse-ring.delay-2 {
		animation-delay: 0.8s;
	}

	.center-dot {
		width: 16px;
		height: 16px;
		background: var(--primary);
		border-radius: 50%;
		box-shadow: 0 0 20px var(--primary-glow);
		animation: dot-pulse 1.5s ease-in-out infinite;
	}

	@keyframes pulse-expand {
		0% {
			transform: scale(0.3);
			opacity: 1;
		}
		100% {
			transform: scale(1.5);
			opacity: 0;
		}
	}

	@keyframes dot-pulse {
		0%, 100% {
			transform: scale(1);
			box-shadow: 0 0 20px var(--primary-glow);
		}
		50% {
			transform: scale(1.2);
			box-shadow: 0 0 30px var(--primary-glow);
		}
	}

	/* Icon Wrapper */
	.icon-wrapper {
		width: 72px;
		height: 72px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		margin-bottom: var(--space-sm);
	}

	.icon-wrapper.success {
		background: rgba(0, 255, 157, 0.1);
		border: 2px solid var(--success);
		color: var(--success);
		box-shadow: 0 0 30px rgba(0, 255, 157, 0.2);
	}

	.icon-wrapper.error {
		background: rgba(255, 77, 77, 0.1);
		border: 2px solid var(--error);
		color: var(--error);
		box-shadow: 0 0 30px rgba(255, 77, 77, 0.2);
	}

	.status-icon {
		width: 32px;
		height: 32px;
	}

	/* Buttons */
	.cta-button {
		width: 100%;
		max-width: 280px;
		padding: 16px 32px;
		border-radius: 12px;
		background: linear-gradient(135deg, var(--success) 0%, #00bc72 100%);
		color: #000;
		font-weight: 700;
		font-size: 0.9rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		transition: all 0.3s var(--ease-elastic);
		text-align: center;
		margin-top: var(--space-md);
		display: inline-block;
	}

	.cta-button:hover {
		transform: translateY(-2px);
		box-shadow: 0 10px 30px rgba(0, 255, 157, 0.3);
	}

	.action-buttons {
		display: flex;
		flex-direction: column;
		gap: var(--space-sm);
		margin-top: var(--space-md);
		width: 100%;
		max-width: 280px;
	}

	.secondary-button {
		padding: 14px 32px;
		border-radius: 12px;
		background: rgba(255, 255, 255, 0.05);
		border: 1px solid var(--glass-border);
		color: var(--ghost-white);
		font-weight: 600;
		font-size: 0.9rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		transition: all 0.3s ease;
		text-align: center;
	}

	.secondary-button:hover {
		background: rgba(255, 255, 255, 0.1);
		border-color: var(--ghost-white);
		transform: translateY(-2px);
	}
</style>
