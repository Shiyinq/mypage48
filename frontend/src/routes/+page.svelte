<script lang="ts">
	import { onMount } from 'svelte';
	import { auth } from '$lib/apis/auth';
	import { goto } from '$app/navigation';
	import { fade, fly } from 'svelte/transition';

	let loading = true;

	onMount(async () => {
		try {
			// Check if already logged in, redirect to app
			const user = await auth.getProfile();
			if (user) {
				goto('/app');
			}
		} catch (e) {
			// Not logged in, stay here
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>FASMO | High Velocity Architecture</title>
	<meta
		name="description"
		content="Next-generation web application architecture fusing FastAPI and SvelteKit."
	/>
</svelte:head>

<div class="landing-container">
	{#if loading}
		<div class="loader-container" in:fade>
			<div class="spinner"></div>
		</div>
	{:else}
		<nav class="top-nav" in:fade={{ duration: 800 }}>
			<a href="/login" class="nav-link">Login</a>
			<a href="/register" class="nav-btn">Register</a>
		</nav>

		<div class="content" in:fly={{ y: 20, duration: 1000 }}>
			<header class="hero-section">
				<pre class="ascii-logo">
            ('-.      .-')   _   .-')                
           ( OO ).-. ( OO ).( '.( OO )_              
   ,------./ . --. /(_)---\_),--.   ,--.).-'),-----. 
('-| _.---'| \-.  \ /    _ | |   `.'   |( OO'  .-.  '
(OO|(_\  .-'-'  |  |\  :` `. |         |/   |  | |  |
/  |  '--.\| |_.'  | '..`''.)|  |'.'|  |\_) |  |\|  |
\_)|  .--' |  .-.  |.-._)   \|  |   |  |  \ |  | |  |
  \|  |_)  |  | |  |\       /|  |   |  |   `'  '-'  '
   `--'    `--' `--' `-----' `--'   `--'     `-----' 
				</pre>
				<div class="pill">
					<span>FastAPI</span>
					<span class="accent">•</span>
					<span>SvelteKit</span>
					<span class="accent">•</span>
					<span>MongoDB</span>
				</div>
				<p class="tagline">
					Your gateway to <span>next-generation</span> architecture. <br />
					Seamlessly fused for <span>maximum velocity</span>.
				</p>

				<div class="header-spacer"></div>
			</header>

			<div class="features-grid">
				<div class="feature-card">
					<div class="icon-wrapper">
						<img src="/assets/icons/lightning.png" alt="Fast" class="feature-icon" />
					</div>
					<h3>Lightning Fast</h3>
					<p>Powered by Vite and FastAPI for incredible speed.</p>
				</div>
				<div class="feature-card">
					<div class="icon-wrapper">
						<img src="/assets/icons/padlock.png" alt="Secure" class="feature-icon" />
					</div>
					<h3>Secure Auth</h3>
					<p>JWT-based authentication with OAuth support built-in.</p>
				</div>
				<div class="feature-card">
					<div class="icon-wrapper">
						<img src="/assets/icons/diamond.png" alt="Modern" class="feature-icon" />
					</div>
					<h3>Modern UI</h3>
					<p>Sleek glassmorphism design system ready to go.</p>
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.landing-container {
		height: 100vh;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: var(--space-md);
		color: var(--ghost-white);
		color: var(--ghost-white);
		text-align: center;
		overflow: hidden;
	}

	.loader-container {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
	}

	.spinner {
		width: 40px;
		height: 40px;
		border: 3px solid rgba(255, 255, 255, 0.1);
		border-radius: 50%;
		border-top-color: var(--primary);
		animation: spin 1s ease-in-out infinite;
	}

	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}

	.content {
		max-width: 1200px;
		width: 100%;
		height: 100%;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center; /* Center vertically */
		gap: 3vh; /* Slightly reduced gap to accommodate larger logo */
	}

	.hero-section {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 2vh;
		width: 100%;
	}

	.ascii-logo {
		font-family: 'Courier New', Courier, monospace;
		font-weight: bold;
		font-size: clamp(16px, 2.8vh, 28px); /* Doubled specific values */
		line-height: 1.1;
		white-space: pre;
		margin: 0;
		background: linear-gradient(135deg, #fff 0%, rgba(255, 255, 255, 0.8) 100%);
		background-clip: text;
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		user-select: none;
		text-align: center;
		padding: 1vh 0;
		filter: drop-shadow(0 0 10px rgba(255, 255, 255, 0.15)); /* Add glow */
	}

	.pill {
		font-size: 0.75rem;
		text-transform: uppercase;
		letter-spacing: 0.25em;
		padding: 8px 20px;
		border-radius: 100px;
		background: rgba(0, 0, 0, 0.4);
		border: 1px solid rgba(255, 255, 255, 0.1);
		color: var(--ghost-white);
		margin-bottom: 2vh;
		backdrop-filter: blur(10px);
		box-shadow:
			0 0 20px rgba(0, 0, 0, 0.5),
			inset 0 0 10px rgba(255, 255, 255, 0.05);
		display: flex;
		gap: 12px;
		align-items: center;
		font-weight: 600;
	}

	.pill span {
		background: linear-gradient(90deg, #fff, #aaa);
		background-clip: text;
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
	}

	.pill .accent {
		color: var(--primary);
		-webkit-text-fill-color: initial;
		text-shadow: 0 0 10px var(--primary);
	}

	.tagline {
		font-size: clamp(1.2rem, 3.5vw, 1.8rem); /* Larger font */
		color: var(--ghost-white);
		max-width: 800px;
		line-height: 1.4;
		font-weight: 300;
		letter-spacing: -0.02em;
	}

	.tagline span {
		color: var(--text-muted);
	}

	.top-nav {
		position: absolute;
		top: 0;
		right: 0;
		width: 100%;
		padding: var(--space-lg);
		display: flex;
		justify-content: flex-end;
		align-items: center;
		gap: 20px;
		z-index: 10;
	}

	.nav-link {
		color: var(--ghost-white);
		text-decoration: none;
		font-weight: 600;
		font-size: 0.9rem;
		opacity: 0.8;
		transition: opacity 0.2s;
	}

	.nav-link:hover {
		opacity: 1;
		color: var(--primary);
	}

	.nav-btn {
		background: rgba(255, 255, 255, 0.1);
		border: 1px solid var(--glass-border);
		padding: 8px 24px;
		border-radius: 100px;
		color: var(--ghost-white);
		text-decoration: none;
		font-weight: 600;
		font-size: 0.9rem;
		transition: all 0.3s ease;
		text-transform: uppercase;
		font-size: 0.75rem;
		letter-spacing: 0.05em;
	}

	.nav-btn:hover {
		background: var(--primary);
		color: #000;
		border-color: var(--primary);
		box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
	}

	.header-spacer {
		height: 4vh;
	}

	.features-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr); /* Force 3 cols */
		gap: 1.5rem;
		width: 100%;
		max-width: 1000px;
	}

	.feature-card {
		background: rgba(255, 255, 255, 0.02);
		border: 1px solid var(--glass-border);
		padding: 1.5rem;
		border-radius: 16px;
		text-align: left;
		transition: all 0.3s ease;
	}

	.feature-card:hover {
		transform: translateY(-5px);
		background: rgba(255, 255, 255, 0.04);
		border-color: var(--primary);
		box-shadow:
			0 10px 30px rgba(0, 0, 0, 0.2),
			0 0 20px rgba(0, 242, 234, 0.1);
	}

	.icon-wrapper {
		width: 60px;
		height: 60px;
		margin-bottom: 1rem;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.feature-icon {
		width: 100%;
		height: 100%;
		object-fit: contain;
		filter: drop-shadow(0 0 10px rgba(255, 255, 255, 0.2));
	}

	.feature-card h3 {
		font-size: 1.1rem;
		margin-bottom: 0.4rem;
		color: var(--ghost-white);
	}

	.feature-card p {
		color: var(--text-muted);
		line-height: 1.4;
		font-size: 0.9rem;
	}
</style>
