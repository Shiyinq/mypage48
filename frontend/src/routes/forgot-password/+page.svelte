<script lang="ts">
	import { auth } from '$lib/apis/auth';
	import { fade, fly } from 'svelte/transition';

	let email = '';
	let loading = false;
	let error = '';
	let success = false;

	async function handleSubmit() {
		loading = true;
		error = '';
		success = false;

		try {
			await auth.forgotPassword({ email });
			success = true;
		} catch (e: any) {
			error = e.detail || 'Transmission failed.';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>FASMO | Recovery</title>
	<meta name="description" content="Recover lost access credentials." />
</svelte:head>

<div class="page-container">
	<div class="content">
		<!-- Visual Section -->
		<div class="visual-pane" in:fly={{ y: 20, duration: 1000, delay: 200 }}>
			<div class="header-section">
				<h1>RECOVERY</h1>
				<p class="subtitle">Lost your key? <br />Initiate recovery protocol.</p>
			</div>

			<div class="asset-wrapper">
				<img
					src="/assets/background/forgot-password.png"
					alt="Recovery Asset"
					class="accent-asset"
				/>
			</div>
		</div>

		<!-- Interaction Section -->
		<div class="interaction-pane glass-pane" in:fly={{ y: 50, duration: 1000 }}>
			{#if success}
				<div class="success-state" in:fade>
					<div class="success-icon">
						<svg viewBox="0 0 24 24" fill="none" class="check-svg">
							<path
								d="M20 6L9 17L4 12"
								stroke="currentColor"
								stroke-width="2"
								stroke-linecap="round"
								stroke-linejoin="round"
							/>
						</svg>
					</div>
					<h2>Check your inbox</h2>
					<p class="success-desc">
						We have sent a password recovery instruction to <strong>{email}</strong>.
					</p>

					<a href="/login" class="cta-button secondary">Back to Login</a>
				</div>
			{:else}
				<form on:submit|preventDefault={handleSubmit} class="recovery-form">
					{#if error}
						<div class="error-banner" transition:fade>
							<span class="error-icon">!</span>
							{error}
						</div>
					{/if}

					<div class="input-group">
						<label for="email" class="input-label">Email Address</label>
						<p class="helper-text">We'll send you a link to reset your password.</p>
						<input
							id="email"
							type="email"
							placeholder="Enter your registered email"
							bind:value={email}
							class="glass-input"
							required
						/>
					</div>

					<button type="submit" class="cta-button" disabled={loading}>
						{#if loading}
							Sending Signal...
						{:else}
							SEND RESET LINK
						{/if}
					</button>

					<a href="/login" class="back-link"> ← Back to Login </a>
				</form>
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
			grid-template-columns: 1fr 450px;
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
		color: var(--ghost-white);
	}

	.subtitle {
		font-size: 1.125rem;
		max-width: 400px;
		color: var(--text-muted);
		border-left: 2px solid var(--warning);
		padding-left: var(--space-md);
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
		max-width: 1125px;
		opacity: 0.9;
		filter: drop-shadow(0 0 40px var(--warning-glow));
		animation: float 8s ease-in-out infinite;
	}

	/* Interaction Pane */
	.interaction-pane {
		padding: 48px;
		display: flex;
		flex-direction: column;
		position: relative;
		overflow: hidden;
		min-height: 400px;
		justify-content: center;
	}

	/* Add top accent line */
	.interaction-pane::before {
		content: '';
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 2px;
		background: linear-gradient(90deg, transparent, var(--warning), transparent);
	}

	.recovery-form {
		display: flex;
		flex-direction: column;
		gap: var(--space-lg);
	}

	.input-group {
		display: flex;
		flex-direction: column;
		gap: 8px;
	}

	.input-label {
		font-weight: 600;
		font-size: 0.95rem;
		color: var(--ghost-white);
	}

	.helper-text {
		font-size: 0.85rem;
		color: var(--text-muted);
		margin-bottom: 4px;
	}

	.glass-input {
		width: 100%;
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid var(--glass-border);
		border-radius: 12px;
		padding: 16px 20px;
		color: var(--ghost-white);
		font-family: var(--font-body);
		font-size: 1rem;
		transition: all 0.3s var(--ease-smooth);
	}

	.glass-input:focus {
		outline: none;
		border-color: var(--warning);
		box-shadow: 0 0 15px rgba(255, 191, 0, 0.15);
		background: rgba(255, 255, 255, 0.05);
	}

	.cta-button {
		width: 100%;
		padding: 16px;
		border-radius: 12px;
		background: linear-gradient(135deg, var(--warning) 0%, #ff8800 100%);
		color: #000;
		font-weight: 700;
		font-size: 1rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		transition: all 0.3s var(--ease-elastic);
		text-align: center;
		display: inline-block;
	}

	.cta-button:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 10px 30px rgba(255, 191, 0, 0.3);
	}

	.cta-button:disabled {
		opacity: 0.7;
		cursor: not-allowed;
		filter: grayscale(1);
	}

	.cta-button.secondary {
		background: rgba(255, 255, 255, 0.1);
		color: var(--ghost-white);
		border: 1px solid var(--glass-border);
	}

	.cta-button.secondary:hover {
		background: rgba(255, 255, 255, 0.15);
	}

	.back-link {
		text-align: center;
		color: var(--text-muted);
		font-size: 0.9rem;
		transition: color 0.2s;
	}

	.back-link:hover {
		color: var(--ghost-white);
	}

	/* Success State */
	.success-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		text-align: center;
		gap: var(--space-md);
	}

	.success-icon {
		width: 64px;
		height: 64px;
		background: rgba(0, 255, 157, 0.1);
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--success);
		margin-bottom: var(--space-sm);
	}

	.check-svg {
		width: 32px;
		height: 32px;
	}

	.success-desc {
		font-size: 1rem;
		color: var(--text-muted);
		margin-bottom: var(--space-md);
	}

	.error-banner {
		background: rgba(255, 77, 77, 0.1);
		border: 1px solid var(--error);
		padding: 12px;
		border-radius: 8px;
		color: #ff8888;
		font-size: 0.9rem;
		display: flex;
		align-items: center;
		gap: 10px;
	}

	.error-icon {
		background: var(--error);
		color: black;
		width: 20px;
		height: 20px;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 50%;
		font-weight: bold;
		font-size: 0.8rem;
	}
</style>
