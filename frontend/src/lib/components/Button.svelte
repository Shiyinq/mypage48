<script lang="ts">
	interface Props {
		type?: 'button' | 'submit' | 'reset';
		variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'google' | 'github';
		size?: 'sm' | 'md' | 'lg';
		disabled?: boolean;
		full?: boolean;
		loading?: boolean;
		class?: string;
		onclick?: (e: MouseEvent) => void;
		children?: import('svelte').Snippet;
	}

	let {
		type = 'button',
		variant = 'primary',
		size = 'md',
		disabled = false,
		full = false,
		loading = false,
		class: className = '',
		onclick,
		children
	}: Props = $props();
</script>

<button
	{type}
	class="btn btn-{variant} btn-{size} {full ? 'w-full' : ''} {loading ? 'loading' : ''} {className}"
	{disabled}
	{onclick}
>
	{#if loading}
		<span class="spinner"></span>
	{/if}
	{@render children?.()}
</button>

<style>
	.btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		border-radius: var(--radius-md, 0.75rem);
		font-weight: 600;
		transition: all var(--transition-fast, 0.2s);
		gap: 0.5rem;
		position: relative;
		overflow: hidden;
		cursor: pointer;
		border: none;
		outline: none;
		font-family: inherit;
	}

	.btn-sm {
		padding: 0.5rem 1rem;
		font-size: 0.75rem;
	}

	.btn-md {
		padding: 0.75rem 1.5rem;
		font-size: 0.875rem;
	}

	.btn-lg {
		padding: 1rem 2rem;
		font-size: 1rem;
	}

	.btn:disabled {
		opacity: 0.7;
		cursor: not-allowed;
		filter: grayscale(0.5);
	}

	.w-full {
		width: 100%;
		display: flex;
	}

	/* Variants */
	.btn-primary {
		background: linear-gradient(
			135deg,
			var(--color-primary, #ef4444),
			var(--color-primary-hover, #dc2626)
		);
		color: white;
		box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
	}
	.btn-primary:hover {
		transform: translateY(-1px);
		box-shadow: 0 6px 16px rgba(239, 68, 68, 0.4);
	}
	.btn-primary:active {
		transform: scale(0.98);
	}

	.btn-secondary {
		background: var(--color-surface, #ffffff);
		border: 1px solid var(--color-border, #e2e8f0);
		color: var(--color-text-main, #1e293b);
	}
	.btn-secondary:hover {
		background: var(--color-surface-hover, #f8fafc);
		border-color: var(--color-text-muted, #94a3b8);
	}

	.btn-outline {
		background: transparent;
		border: 1px solid var(--color-border, #e2e8f0);
		color: var(--color-text-muted, #64748b);
	}
	.btn-outline:hover {
		color: var(--color-primary, #ef4444);
		border-color: var(--color-primary, #ef4444);
		background: var(--color-surface-hover, #fff1f2);
	}

	.btn-ghost {
		background: transparent;
		color: var(--color-text-muted, #64748b);
	}
	.btn-ghost:hover {
		background: rgba(0, 0, 0, 0.05);
		color: var(--color-text-main, #1e293b);
	}

	/* Social Buttons */
	.btn-google {
		background: white;
		color: #1a1a1a;
		border: 1px solid #e2e8f0;
	}
	.btn-google:hover {
		background: #f8fafc;
	}

	.btn-github {
		background: #24292e;
		color: white;
	}
	.btn-github:hover {
		background: #2f363d;
	}

	/* Loading Spinner */
	.spinner {
		width: 1rem;
		height: 1rem;
		border: 2px solid currentColor;
		border-right-color: transparent;
		border-radius: 50%;
		animation: spin 0.75s linear infinite;
	}
	@keyframes spin {
		100% {
			transform: rotate(360deg);
		}
	}
</style>
