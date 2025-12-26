<script lang="ts">
	import { auth } from '$lib/apis/auth';
	import { goto } from '$app/navigation';
	import { fade, fly, slide } from 'svelte/transition';

	let step = 1;
	let totalSteps = 2;

	// Form Data
	let name = '';
	let username = '';
	let email = '';
	let password = '';
	let confirmPassword = '';

	// Checklist Requirement States
	let reqLength = false;
	let reqNumber = false;
	let reqSpecial = false;
	let reqMatch = false;

	$: {
		reqLength = password.length > 7;
		reqNumber = /[0-9]/.test(password);
		reqSpecial = /[^A-Za-z0-9]/.test(password);
		reqMatch = password.length > 0 && password === confirmPassword;
	}

	let loading = false;
	let error = '';

	// Password Strength
	$: passwordStrength = calculateStrength(password);

	function calculateStrength(pw: string) {
		if (!pw) return 0;
		let score = 0;
		if (pw.length > 7) score++;
		if (/[A-Z]/.test(pw)) score++;
		if (/[0-9]/.test(pw)) score++;
		if (/[^A-Za-z0-9]/.test(pw)) score++;
		return score; // Max 4
	}

	function getStrengthLabel(score: number) {
		if (score === 0) return '';
		if (score < 2) return 'Weak';
		if (score < 4) return 'Good';
		return 'Strong';
	}

	function getStrengthColor(score: number) {
		if (score < 2) return 'var(--error)';
		if (score < 4) return 'var(--warning)';
		return 'var(--success)';
	}

	async function handleRegister() {
		if (step === 1) {
			nextStep();
			return;
		}

		loading = true;
		error = '';

		if (password !== confirmPassword) {
			error = 'Passwords do not match';
			loading = false;
			return;
		}

		try {
			await auth.register({ name, username, email, password, confirmPassword });
			// Auto login after register
			await auth.login({ username: email, password });
			goto('/app');
		} catch (e: any) {
			console.error(e);
			error = typeof e.detail === 'string' ? e.detail : 'Registration failed.';
		} finally {
			loading = false;
		}
	}

	function nextStep() {
		if (step === 1) {
			if (!name || !username) {
				error = 'Please fill in all fields';
				return;
			}
			error = '';
			step = 2;
		}
	}

	function prevStep() {
		step = 1;
		error = '';
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
	<title>FASMO | Join the Network</title>
	<meta name="description" content="Create your digital identity and access the FASMO network." />
</svelte:head>

<div class="page-container">
	<div class="content">
		<!-- Visual Section -->
		<div class="visual-pane" in:fly={{ y: 20, duration: 1000, delay: 200 }}>
			<div class="header-section">
				<h1>JOIN</h1>
				<p class="subtitle">Create your digital identity.<br />Access the network.</p>
			</div>

			<div class="asset-wrapper">
				<!-- Enhancing the asset container with internal glow -->
				<div class="cube-glow"></div>
				<img src="/assets/background/register.png" alt="Register Cube" class="accent-asset" />
			</div>
		</div>

		<!-- Interaction Section -->
		<div class="interaction-pane glass-pane" in:fly={{ y: 50, duration: 1000 }}>
			<!-- Progress Stepper -->
			<div class="stepper">
				<div class="step-indicator {step >= 1 ? 'active' : ''}"></div>
				<div class="step-line {step >= 2 ? 'filled' : ''}"></div>
				<div class="step-indicator {step >= 2 ? 'active' : ''}"></div>
			</div>

			<form class="register-form" on:submit|preventDefault={handleRegister}>
				{#if error}
					<div class="error-banner" transition:fade>
						<span class="error-icon">!</span>
						{error}
					</div>
				{/if}

				<div class="steps-container">
					{#if step === 1}
						<div
							class="step-content"
							in:fly={{ x: -20, duration: 400 }}
							out:fly={{ x: 20, duration: 400 }}
						>
							<div class="input-group">
								<label for="name" class="input-label">Full Name</label>
								<div class="input-wrapper">
									<input
										id="name"
										type="text"
										placeholder="e.g. Alex Chen"
										bind:value={name}
										class="glass-input"
										required
									/>
									{#if name.length > 2}
										<div class="valid-icon" in:fade>✓</div>
									{/if}
								</div>
							</div>

							<div class="input-group">
								<label for="username" class="input-label">Username</label>
								<div class="input-wrapper">
									<input
										id="username"
										type="text"
										placeholder="e.g. achen"
										bind:value={username}
										class="glass-input"
										required
									/>
									{#if username.length > 2}
										<div class="valid-icon" in:fade>✓</div>
									{/if}
								</div>
							</div>

							<button type="submit" class="cta-button">
								Continue
								<span class="arrow">→</span>
							</button>
						</div>
					{:else}
						<div
							class="step-content"
							in:fly={{ x: 20, duration: 400 }}
							out:fly={{ x: -20, duration: 400 }}
						>
							<div class="input-group">
								<label for="email" class="input-label">Email</label>
								<div class="input-wrapper">
									<input
										id="email"
										type="email"
										placeholder="name@example.com"
										bind:value={email}
										class="glass-input"
										required
									/>
								</div>
							</div>

							<div class="input-group">
								<label for="password" class="input-label">Password</label>
								<div class="input-wrapper">
									<input
										id="password"
										type="password"
										placeholder="••••••••"
										bind:value={password}
										class="glass-input"
										required
									/>
								</div>

								<!-- Password Strength -->
								{#if password}
									<div class="strength-meter" transition:slide>
										<div class="strength-bars">
											<div
												class="bar"
												style="background: {passwordStrength >= 1
													? getStrengthColor(passwordStrength)
													: 'rgba(255,255,255,0.1)'}"
											></div>
											<div
												class="bar"
												style="background: {passwordStrength >= 2
													? getStrengthColor(passwordStrength)
													: 'rgba(255,255,255,0.1)'}"
											></div>
											<div
												class="bar"
												style="background: {passwordStrength >= 3
													? getStrengthColor(passwordStrength)
													: 'rgba(255,255,255,0.1)'}"
											></div>
											<div
												class="bar"
												style="background: {passwordStrength >= 4
													? getStrengthColor(passwordStrength)
													: 'rgba(255,255,255,0.1)'}"
											></div>
										</div>
										<span
											class="strength-label"
											style="color: {getStrengthColor(passwordStrength)}"
										>
											{getStrengthLabel(passwordStrength)}
										</span>
									</div>
									<!-- Checklist moved below confirm password -->
									<!-- <div class="checklist">...</div> -->
								{/if}
							</div>

							<div class="input-group">
								<label for="confirm" class="input-label">Confirm Password</label>
								<div class="input-wrapper">
									<input
										id="confirm"
										type="password"
										placeholder="••••••••"
										bind:value={confirmPassword}
										class="glass-input"
										required
									/>
									{#if confirmPassword && confirmPassword === password}
										<div class="valid-icon" in:fade>✓</div>
									{/if}
								</div>

								<!-- Requirements Checklist -->
								{#if password}
									<div class="checklist" transition:slide>
										<div class="check-item {reqLength ? 'met' : ''}">
											<span class="icon">{reqLength ? '✓' : '○'}</span>
											At least 8 characters
										</div>
										<div class="check-item {reqNumber ? 'met' : ''}">
											<span class="icon">{reqNumber ? '✓' : '○'}</span>
											Contains a number
										</div>
										<div class="check-item {reqSpecial ? 'met' : ''}">
											<span class="icon">{reqSpecial ? '✓' : '○'}</span>
											Contains special char
										</div>
										<div class="check-item {reqMatch ? 'met' : ''}">
											<span class="icon">{reqMatch ? '✓' : '○'}</span>
											Passwords match
										</div>
									</div>
								{/if}
							</div>

							<div class="button-row">
								<button type="button" class="back-btn" on:click={prevStep}>Back</button>
								<button type="submit" class="cta-button" disabled={loading}>
									{#if loading}
										Creating...
									{:else}
										REGISTER
									{/if}
								</button>
							</div>
						</div>
					{/if}
				</div>

				<div class="divider">
					<span>Or join with</span>
				</div>

				<div class="social-actions">
					<button
						type="button"
						class="social-btn"
						on:click={() => handleSocialLogin('google')}
						aria-label="Sign up with Google"
					>
						<svg class="social-icon" viewBox="0 0 24 24" fill="currentColor">
							<path
								d="M12.545,10.239v3.821h5.445c-0.712,2.315-2.647,3.972-5.445,3.972c-3.332,0-6.033-2.701-6.033-6.032s2.701-6.032,6.033-6.032c1.498,0,2.866,0.549,3.921,1.453l2.814-2.814C17.503,2.988,15.139,2,12.545,2C7.021,2,2.543,6.477,2.543,12s4.478,10,10.002,10c8.396,0,10.249-7.85,9.426-11.748L12.545,10.239z"
							/>
						</svg>
					</button>
					<button
						type="button"
						class="social-btn"
						on:click={() => handleSocialLogin('github')}
						aria-label="Sign up with Github"
					>
						<svg class="social-icon" viewBox="0 0 24 24" fill="currentColor">
							<path
								d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"
							/>
						</svg>
					</button>
				</div>

				<div class="footer-login">
					<p>Already have an account?</p>
					<a href="/login" class="login-link">Login</a>
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
		border-left: 2px solid var(--secondary);
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
		animation: float 10s ease-in-out infinite reverse; /* Reverse float */
		filter: drop-shadow(0 0 40px var(--secondary-glow));
	}

	.cube-glow {
		position: absolute;
		width: 675px;
		height: 675px;
		background: radial-gradient(circle, var(--secondary-glow) 0%, transparent 70%);
		opacity: 0.4;
		animation: pulse-glow 4s infinite;
	}

	/* Interaction Pane */
	.interaction-pane {
		padding: 48px;
		display: flex;
		flex-direction: column;
		position: relative;
		overflow: hidden;
		min-height: 500px;
	}

	/* Add top accent line */
	.interaction-pane::before {
		content: '';
		position: absolute;
		top: 0;
		left: 0;
		width: 100%;
		height: 2px;
		background: linear-gradient(90deg, transparent, var(--secondary), transparent);
	}

	/* Stepper */
	.stepper {
		display: flex;
		align-items: center;
		justify-content: center;
		margin-bottom: var(--space-xl);
		gap: 10px;
	}

	.step-indicator {
		width: 12px;
		height: 12px;
		border-radius: 50%;
		background: rgba(255, 255, 255, 0.1);
		transition: all 0.3s ease;
		border: 1px solid transparent;
	}

	.step-indicator.active {
		background: var(--secondary);
		box-shadow: 0 0 10px var(--secondary-glow);
	}

	.step-line {
		width: 60px;
		height: 2px;
		background: rgba(255, 255, 255, 0.1);
		position: relative;
	}

	.step-line::after {
		content: '';
		position: absolute;
		top: 0;
		left: 0;
		height: 100%;
		width: 0%;
		background: var(--secondary);
		transition: width 0.3s ease;
	}

	.step-line.filled::after {
		width: 100%;
	}

	.register-form {
		display: flex;
		flex-direction: column;
		flex: 1;
	}

	.steps-container {
		display: grid;
		grid-template-areas: 'stack';
		align-items: start;
		flex: 1;
	}

	.step-content {
		grid-area: stack;
		display: flex;
		flex-direction: column;
		gap: var(--space-md);
		width: 100%;
	}

	.input-group {
		position: relative;
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	.input-label {
		font-size: 0.85rem;
		color: var(--text-muted);
		font-weight: 500;
		margin-left: 4px;
	}

	.input-wrapper {
		position: relative;
	}

	.glass-input {
		width: 100%;
		background: rgba(255, 255, 255, 0.03);
		border: 1px solid var(--glass-border);
		border-radius: 12px;
		padding: 14px 20px;
		color: var(--ghost-white);
		font-family: var(--font-body);
		font-size: 1rem;
		transition: all 0.3s var(--ease-smooth);
	}

	.glass-input:focus {
		outline: none;
		border-color: var(--secondary);
		box-shadow: 0 0 15px rgba(255, 0, 85, 0.15);
		background: rgba(255, 255, 255, 0.05);
	}

	.valid-icon {
		position: absolute;
		right: 15px;
		top: 50%;
		transform: translateY(-50%);
		color: var(--success);
		font-weight: bold;
	}

	/* Strength Meter */
	.strength-meter {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin-top: 4px;
		gap: 10px;
	}

	.strength-bars {
		display: flex;
		gap: 4px;
		flex: 1;
	}

	.bar {
		height: 4px;
		border-radius: 2px;
		flex: 1;
		transition: background 0.3s ease;
	}

	.strength-label {
		font-size: 0.75rem;
		font-weight: 600;
		min-width: 40px;
		text-align: right;
	}

	/* Checklist */
	.checklist {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 8px;
		margin-top: 8px;
		padding-top: 8px;
		border-top: 1px solid rgba(255, 255, 255, 0.1);
	}

	.check-item {
		font-size: 0.75rem;
		color: var(--text-muted);
		display: flex;
		align-items: center;
		gap: 6px;
		transition: color 0.3s ease;
	}

	.check-item.met {
		color: var(--success);
	}

	.icon {
		font-weight: bold;
	}

	/* Buttons */
	.button-row {
		display: flex;
		gap: var(--space-md);
		margin-top: var(--space-md);
	}

	.cta-button {
		flex: 1;
		padding: 16px;
		border-radius: 12px;
		background: linear-gradient(135deg, var(--secondary) 0%, #d40049 100%);
		color: #fff;
		font-weight: 700;
		font-size: 1rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		transition: all 0.3s var(--ease-elastic);
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
	}

	.cta-button:hover:not(:disabled) {
		transform: translateY(-2px);
		box-shadow: 0 10px 30px var(--secondary-glow);
	}

	.back-btn {
		padding: 16px;
		border-radius: 12px;
		border: 1px solid var(--glass-border);
		color: var(--ghost-white);
		font-weight: 600;
		font-size: 1rem;
		transition: all 0.2s ease;
	}

	.back-btn:hover {
		background: rgba(255, 255, 255, 0.05);
	}

	.footer-login {
		margin-top: auto;
		padding-top: var(--space-lg);
		text-align: center;
		display: flex;
		align-items: center;
		gap: 8px;
		justify-content: center;
		font-size: 0.95rem;
	}

	.login-link {
		color: var(--secondary);
		font-weight: 600;
	}

	.login-link:hover {
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
		margin-bottom: var(--space-md);
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

	.arrow {
		font-size: 1.2rem;
		line-height: 1;
	}

	.divider {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 10px;
		margin: var(--space-md) 0;
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
		margin-bottom: var(--space-md);
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
</style>
