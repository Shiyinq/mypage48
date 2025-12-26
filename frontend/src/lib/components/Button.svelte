<script lang="ts">
	export let type: 'button' | 'submit' | 'reset' = 'button';
	export let variant: 'primary' | 'secondary' | 'outline' | 'ghost' | 'google' | 'github' =
		'primary';
	export let size: 'sm' | 'md' | 'lg' = 'md';
	export let disabled = false;
	export let full = false;
	export let loading = false;
</script>

<button
	{type}
	class="btn btn-{variant} btn-{size} {full ? 'w-full' : ''} {loading ? 'loading' : ''}"
	{disabled}
	on:click
>
	{#if loading}
		<span class="spinner"></span>
	{/if}
	<slot />
</button>

<style>
	.btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		border-radius: var(--radius-md);
		font-weight: 500;
		transition: all var(--transition-fast);
		gap: 0.75rem;
		position: relative;
		overflow: hidden;
	}

	.btn-sm {
		padding: 0.5rem 1rem;
		font-size: 0.85rem;
	}

	.btn-md {
		padding: 0.75rem 1.5rem;
		font-size: 0.95rem;
	}

	.btn-lg {
		padding: 1rem 2rem;
		font-size: 1.1rem;
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
		background: linear-gradient(135deg, var(--color-primary), var(--color-primary-hover));
		color: white;
		box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
	}
	.btn-primary:active {
		transform: scale(0.98);
	}

	.btn-secondary {
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		color: var(--color-text-main);
	}
	.btn-secondary:hover {
		background: var(--color-surface-hover);
		border-color: var(--color-text-muted);
	}

	.btn-outline {
		background: transparent;
		border: 1px solid var(--color-border);
		color: var(--color-text-muted);
	}
	.btn-outline:hover {
		color: var(--color-text-main);
		border-color: var(--color-text-main);
	}

	.btn-ghost {
		background: transparent;
		color: var(--color-text-muted);
	}
	.btn-ghost:hover {
		background: rgba(255, 255, 255, 0.05);
		color: var(--color-text-main);
	}

	/* Social Buttons */
	.btn-google {
		background: white;
		color: #1a1a1a;
	}
	.btn-google:hover {
		background: #f1f1f1;
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
