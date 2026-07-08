<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { isAuthenticated } from '$lib/stores';
	import { Home, ArrowLeft, RefreshCw, TriangleAlert, Search, ServerCrash } from 'lucide-svelte';
	import SEO from '$lib/components/SEO.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	const { t } = useTranslation();

	function getErrorInfo(code: number, t: (key: string) => string) {
		switch (code) {
			case 404:
				return {
					title: t('errors.404.title'),
					subtitle: t('errors.404.subtitle'),
					description: t('errors.404.description'),
					icon: Search,
					color: 'from-amber-500 to-orange-500',
					bgColor: 'bg-amber-500/10',
					borderColor: 'border-amber-500/30'
				};
			case 500:
				return {
					title: t('errors.500.title'),
					subtitle: t('errors.500.subtitle'),
					description: t('errors.500.description'),
					icon: ServerCrash,
					color: 'from-red-500 to-rose-600',
					bgColor: 'bg-red-500/10',
					borderColor: 'border-red-500/30'
				};
			case 403:
				return {
					title: t('errors.403.title'),
					subtitle: t('errors.403.subtitle'),
					description: t('errors.403.description'),
					icon: TriangleAlert,
					color: 'from-yellow-500 to-amber-500',
					bgColor: 'bg-yellow-500/10',
					borderColor: 'border-yellow-500/30'
				};
			case 401:
				return {
					title: t('errors.401.title'),
					subtitle: t('errors.401.subtitle'),
					description: t('errors.401.description'),
					icon: TriangleAlert,
					color: 'from-blue-500 to-indigo-500',
					bgColor: 'bg-blue-500/10',
					borderColor: 'border-blue-500/30'
				};
			default:
				return {
					title: t('errors.default.title'),
					subtitle: t('errors.default.subtitle'),
					description: t('errors.default.description'),
					icon: TriangleAlert,
					color: 'from-gray-500 to-slate-600',
					bgColor: 'bg-gray-500/10',
					borderColor: 'border-gray-500/30'
				};
		}
	}

	function goHome() {
		goto(isAuthenticated.value ? '/' : '/login');
	}

	function goBack() {
		if (typeof window !== 'undefined') {
			window.history.back();
		}
	}

	function refresh() {
		if (typeof window !== 'undefined') {
			window.location.reload();
		}
	}
	let {
		overrideStatus = null,
		overrideMessage = null
	}: { overrideStatus?: number | null; overrideMessage?: string | null } = $props();
	let status = $derived(overrideStatus || $page.status);
	let message = $derived(overrideMessage || $page.error?.message);
	// Define error info based on status code
	let errorInfo = $derived(getErrorInfo(status, t));
</script>

<SEO title={`${status} - ${errorInfo.title}`} description={message || errorInfo.description} />

<div class="error-page">
	<div class="error-container animate-page-transition">
		<!-- Decorative Background Elements -->
		<div class="decorative-elements">
			<div class="floating-circle circle-1"></div>
			<div class="floating-circle circle-2"></div>
			<div class="floating-circle circle-3"></div>
		</div>

		<!-- Error Card -->
		<div class="error-card glass-panel">
			<!-- Error Icon -->
			<div class="icon-wrapper {errorInfo.bgColor} {errorInfo.borderColor}">
				<div class="icon-bg bg-gradient-to-br {errorInfo.color}">
					<errorInfo.icon class="w-8 h-8 text-white" />
				</div>
			</div>

			<!-- Error Code -->
			<div class="error-code">
				<span class="code-number bg-gradient-to-r {errorInfo.color} bg-clip-text text-transparent">
					{status}
				</span>
			</div>

			<!-- Error Title -->
			<h1 class="error-title">{errorInfo.title}</h1>

			<!-- Error Subtitle -->
			<p class="error-subtitle">{errorInfo.subtitle}</p>

			<!-- Error Description -->
			<p class="error-description">{errorInfo.description}</p>

			{#if message && message !== errorInfo.subtitle}
				<div class="error-message-box">
					<code class="error-message">{message}</code>
				</div>
			{/if}

			<!-- Action Buttons -->
			<div class="actions">
				<button class="btn btn-primary idol-gradient" onclick={goHome}>
					<Home class="w-4 h-4" />
					<span>{t('errors.goHome')}</span>
				</button>

				<button class="btn btn-secondary" onclick={goBack}>
					<ArrowLeft class="w-4 h-4" />
					<span>{t('common.back')}</span>
				</button>

				<button class="btn btn-ghost" onclick={refresh}>
					<RefreshCw class="w-4 h-4" />
					<span>{t('errors.tryAgain')}</span>
				</button>
			</div>
		</div>

		<!-- Footer Text -->
		<p class="footer-text">{t('header.tagline')} • MyPage48</p>
	</div>
</div>

<style>
	.error-page {
		min-height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 1.5rem;
		position: relative;
		overflow: hidden;
	}

	.error-container {
		position: relative;
		width: 100%;
		max-width: 480px;
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	/* Decorative Elements */
	.decorative-elements {
		position: fixed;
		inset: 0;
		pointer-events: none;
		overflow: hidden;
	}

	.floating-circle {
		position: absolute;
		border-radius: 50%;
		opacity: 0.4;
		animation: float 8s ease-in-out infinite;
	}

	.circle-1 {
		width: 300px;
		height: 300px;
		background: radial-gradient(circle, rgba(227, 0, 15, 0.15) 0%, transparent 70%);
		top: -100px;
		right: -100px;
		animation-delay: 0s;
	}

	.circle-2 {
		width: 200px;
		height: 200px;
		background: radial-gradient(circle, rgba(227, 0, 15, 0.1) 0%, transparent 70%);
		bottom: -50px;
		left: -50px;
		animation-delay: -3s;
	}

	.circle-3 {
		width: 150px;
		height: 150px;
		background: radial-gradient(circle, rgba(227, 0, 15, 0.12) 0%, transparent 70%);
		top: 40%;
		left: 10%;
		animation-delay: -5s;
	}

	@keyframes float {
		0%,
		100% {
			transform: translateY(0) scale(1);
		}
		50% {
			transform: translateY(-20px) scale(1.05);
		}
	}

	/* Error Card */
	.error-card {
		width: 100%;
		padding: 3rem 2rem;
		border-radius: 24px;
		text-align: center;
		position: relative;
		z-index: 10;
		box-shadow:
			0 4px 6px -1px rgba(0, 0, 0, 0.05),
			0 10px 15px -3px rgba(0, 0, 0, 0.05),
			0 20px 25px -5px rgba(0, 0, 0, 0.03);
	}

	/* Icon */
	.icon-wrapper {
		width: 80px;
		height: 80px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		margin: 0 auto 1.5rem;
		border: 2px solid;
		animation: pulse-subtle 3s ease-in-out infinite;
	}

	.icon-bg {
		width: 56px;
		height: 56px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		box-shadow: 0 4px 15px rgba(227, 0, 15, 0.3);
	}

	@keyframes pulse-subtle {
		0%,
		100% {
			transform: scale(1);
		}
		50% {
			transform: scale(1.02);
		}
	}

	/* Error Code */
	.error-code {
		margin-bottom: 0.75rem;
	}

	.code-number {
		font-size: 4rem;
		font-weight: 800;
		line-height: 1;
		letter-spacing: -2px;
	}

	/* Text Content */
	.error-title {
		font-size: 1.5rem;
		font-weight: 700;
		color: #1f2937;
		margin-bottom: 0.5rem;
	}

	.error-subtitle {
		font-size: 1rem;
		color: #4b5563;
		margin-bottom: 0.5rem;
		font-weight: 500;
	}

	.error-description {
		font-size: 0.875rem;
		color: #6b7280;
		margin-bottom: 1.5rem;
		line-height: 1.5;
	}

	.error-message-box {
		background: #f3f4f6;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
		padding: 0.75rem 1rem;
		margin-bottom: 1.5rem;
	}

	.error-message {
		font-size: 0.75rem;
		color: #6b7280;
		word-break: break-word;
	}

	/* Action Buttons */
	.actions {
		display: flex;
		flex-wrap: wrap;
		gap: 0.75rem;
		justify-content: center;
	}

	.btn {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.75rem 1.25rem;
		border-radius: 12px;
		font-size: 0.875rem;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s ease;
		border: none;
		outline: none;
	}

	.btn-primary {
		color: white;
		box-shadow: 0 4px 12px rgba(227, 0, 15, 0.3);
	}

	.btn-primary:hover {
		transform: translateY(-2px);
		box-shadow: 0 6px 20px rgba(227, 0, 15, 0.4);
	}

	.btn-secondary {
		background: white;
		color: #374151;
		border: 1px solid #e5e7eb;
	}

	.btn-secondary:hover {
		background: #f9fafb;
		border-color: #d1d5db;
		transform: translateY(-1px);
	}

	.btn-ghost {
		background: transparent;
		color: #6b7280;
	}

	.btn-ghost:hover {
		background: #f3f4f6;
		color: #374151;
	}

	/* Footer */
	.footer-text {
		margin-top: 2rem;
		font-size: 0.75rem;
		color: #9ca3af;
		font-weight: 500;
	}

	/* Responsive */
	@media (max-width: 480px) {
		.error-card {
			padding: 2rem 1.5rem;
		}

		.code-number {
			font-size: 3rem;
		}

		.error-title {
			font-size: 1.25rem;
		}

		.actions {
			flex-direction: column;
			width: 100%;
		}

		.btn {
			width: 100%;
			justify-content: center;
		}
	}
</style>
