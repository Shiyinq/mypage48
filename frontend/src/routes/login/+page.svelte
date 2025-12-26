<script lang="ts">
	import { auth } from '$lib/apis/auth';
	import { goto } from '$app/navigation';
	import { fade, fly } from 'svelte/transition';

	let username = '';
	let password = '';
	let rememberMe = false;
	let loading = false;
	let error = '';

	async function handleLogin() {
		loading = true;
		error = '';
		try {
			await auth.login({ username, password });
			goto('/app');
		} catch (e: any) {
			console.error(e);
			error = e.detail || 'Connection refused.';
		} finally {
			loading = false;
		}
	}

	function handleSocialLogin(provider: 'google' | 'github') {
		if (provider === 'google') {
			window.location.href = auth.googleLoginUrl;
		} else if (provider === 'github') {
			window.location.href = auth.githubLoginUrl;
		}
	}
</script>

<svelte:head>
	<title>FASMO | Login</title>
	<meta name="description" content="Secure login access to the FASMO architecture." />
</svelte:head>

<div class="page-container">
	<div class="content">
		<!-- Visual Section -->
		<div class="visual-pane" in:fly={{ y: 20, duration: 1000, delay: 200 }}>
			<div class="header-section">
				<h1>LOGIN</h1>
				<p class="subtitle">Resume your session. <br />Enter the stream.</p>
			</div>

			<div class="asset-wrapper">
				<img src="/assets/background/login.png" alt="Login Key" class="accent-asset" />
			</div>
		</div>

		<!-- Interaction Section -->
		<div class="interaction-pane glass-pane" in:fly={{ y: 50, duration: 1000 }}>
			<form class="login-form" on:submit|preventDefault={handleLogin}>
				{#if error}
					<div class="error-banner" transition:fade>
						<span class="error-icon">!</span>
						{error}
					</div>
				{/if}

				<div class="input-group">
					<label for="username" class="visually-hidden">Username or Email</label>
					<input
						id="username"
						type="text"
						placeholder="Username or Email"
						bind:value={username}
						class="glass-input"
						required
					/>
				</div>

				<div class="input-group">
					<label for="password" class="visually-hidden">Password</label>
					<input
						id="password"
						type="password"
						placeholder="Password"
						bind:value={password}
						class="glass-input"
						required
					/>
				</div>

				<div class="form-options">
					<label class="checkbox-container">
						<input type="checkbox" bind:checked={rememberMe} />
						<span class="checkmark"></span>
						<span class="label-text">Remember me</span>
					</label>
					<a href="/forgot-password" class="link-text">Forgot Password?</a>
				</div>

				<button type="submit" class="cta-button" disabled={loading}>
					{#if loading}
						<span class="loading-dots">Logging in...</span>
					{:else}
						LOGIN
					{/if}
				</button>

				<div class="divider">
					<span>Or continue with</span>
				</div>

				<div class="social-actions">
					<button
						type="button"
						class="social-btn"
						on:click={() => handleSocialLogin('google')}
						aria-label="Login with Google"
					>
						<!-- Google Icon placeholder or SVG -->
						<svg class="social-icon" viewBox="0 0 24 24" fill="currentColor"
							><path
								d="M12.545,10.239v3.821h5.445c-0.712,2.315-2.647,3.972-5.445,3.972c-3.332,0-6.033-2.701-6.033-6.032s2.701-6.032,6.033-6.032c1.498,0,2.866,0.549,3.921,1.453l2.814-2.814C17.503,2.988,15.139,2,12.545,2C7.021,2,2.543,6.477,2.543,12s4.478,10,10.002,10c8.396,0,10.249-7.85,9.426-11.748L12.545,10.239z"
							/></svg
						>
					</button>
					<button
						type="button"
						class="social-btn"
						on:click={() => handleSocialLogin('github')}
						aria-label="Login with Github"
					>
						<!-- Github Icon placeholder or SVG -->
						<svg class="social-icon" viewBox="0 0 24 24" fill="currentColor"
							><path
								d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"
							/></svg
						>
					</button>
				</div>

				<div class="footer-register">
					<p>Don't have an account?</p>
					<a href="/register" class="create-account-link">Create Account</a>
				</div>
			</form>
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
		max-width: 1200px;
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
		font-size: clamp(3rem, 6vw, 6rem);
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
		opacity: 0.8;
		animation: float 8s ease-in-out infinite;
		filter: drop-shadow(0 0 40px var(--primary-glow));
	}

	/* Interaction Pane */
	.interaction-pane {
		padding: 48px;
		display: flex;
		flex-direction: column;
		position: relative;
		overflow: hidden;
	}

	/* Add top accent line */
	.interaction-pane::before {
		content: '';
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 2px;
		background: linear-gradient(90deg, transparent, var(--primary), transparent);
	}

	.login-form {
		display: flex;
		flex-direction: column;
		gap: var(--space-md);
	}

	.input-group {
		position: relative;
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
		border-color: var(--primary);
		box-shadow: 0 0 20px rgba(0, 242, 234, 0.1);
		background: rgba(255, 255, 255, 0.05);
	}

	.glass-input::placeholder {
		color: rgba(255, 255, 255, 0.2);
	}

	/* Form Options */
	.form-options {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-top: -8px;
	}

	.checkbox-container {
		display: flex;
		align-items: center;
		cursor: pointer;
		user-select: none;
		gap: 10px;
	}

	.checkbox-container input {
		position: absolute;
		opacity: 0;
		cursor: pointer;
		height: 0;
		width: 0;
	}

	.checkmark {
		height: 20px;
		width: 20px;
		background-color: rgba(255, 255, 255, 0.05);
		border: 1px solid var(--glass-border);
		border-radius: 6px;
		position: relative;
		transition: all 0.2s ease;
	}

	.checkbox-container:hover input ~ .checkmark {
		background-color: rgba(255, 255, 255, 0.1);
	}

	.checkbox-container input:checked ~ .checkmark {
		background-color: var(--primary);
		border-color: var(--primary);
	}

	.checkmark:after {
		content: '';
		position: absolute;
		display: none;
		left: 6px;
		top: 2px;
		width: 5px;
		height: 10px;
		border: solid #000;
		border-width: 0 2px 2px 0;
		transform: rotate(45deg);
	}

	.checkbox-container input:checked ~ .checkmark:after {
		display: block;
	}

	.label-text {
		font-size: 0.9rem;
		color: var(--text-muted);
	}

	.link-text {
		font-size: 0.9rem;
		color: var(--primary);
		transition: all 0.2s ease;
	}

	.link-text:hover {
		color: #fff;
		text-shadow: 0 0 10px var(--primary-glow);
	}

	/* CTA Button */
	.cta-button {
		width: 100%;
		padding: 16px;
		border-radius: 12px;
		background: linear-gradient(135deg, var(--primary) 0%, #00c2bb 100%);
		color: #000;
		font-weight: 700;
		font-size: 1rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		transition: all 0.3s var(--ease-elastic);
		position: relative;
		overflow: hidden;
		margin-top: var(--space-xs);
	}

	.cta-button:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 10px 30px var(--primary-glow);
	}

	.cta-button:disabled {
		opacity: 0.7;
		cursor: not-allowed;
		filter: grayscale(1);
	}

	.divider {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 10px;
		margin: var(--space-lg) 0;
		position: relative;
	}

	.divider span {
		padding: 0 10px;
		font-size: 0.8rem;
		color: var(--text-muted);
		position: relative;
		z-index: 1;
	}

	.divider::after,
	.divider::before {
		content: '';
		display: block;
		height: 1px;
		background: rgba(255, 255, 255, 0.1);
		flex: 1;
	}

	.social-actions {
		display: flex;
		gap: var(--space-md);
		justify-content: center;
	}

	.social-btn {
		width: 50px;
		height: 50px;
		border-radius: 12px;
		background: rgba(255, 255, 255, 0.05);
		border: 1px solid var(--glass-border);
		display: flex;
		align-items: center;
		justify-content: center;
		color: var(--ghost-white);
		transition: all 0.3s ease;
	}

	.social-btn:hover {
		background: rgba(255, 255, 255, 0.1);
		transform: translateY(-3px);
		border-color: var(--ghost-white);
	}

	.social-icon {
		width: 24px;
		height: 24px;
	}

	.footer-register {
		margin-top: var(--space-lg);
		text-align: center;
		display: flex;
		align-items: center;
		gap: 8px;
		justify-content: center;
		font-size: 0.95rem;
	}

	.create-account-link {
		color: var(--primary);
		font-weight: 600;
	}

	.create-account-link:hover {
		text-decoration: underline;
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
