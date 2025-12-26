<script lang="ts">
	import { toasts, removeToast } from '$lib/store/toast';
	import { flip } from 'svelte/animate';
	import { fly } from 'svelte/transition';
</script>

<div class="toast-container">
	{#each $toasts as toast (toast.id)}
		<div
			class="toast toast-{toast.type}"
			animate:flip
			transition:fly={{ y: 20, duration: 300 }}
			role="alert"
		>
			<span>{toast.message}</span>
			<button class="close-btn" on:click={() => removeToast(toast.id)}>×</button>
		</div>
	{/each}
</div>

<style>
	.toast-container {
		position: fixed;
		bottom: 2rem;
		right: 2rem;
		display: flex;
		flex-direction: column;
		gap: 0.75rem;
		z-index: 100;
		pointer-events: none; /* Allow clicking through container */
	}

	.toast {
		pointer-events: auto;
		min-width: 300px;
		padding: 1rem;
		border-radius: var(--radius-md);
		background: var(--color-surface);
		color: var(--color-text-main);
		box-shadow: var(--shadow-lg);
		border: 1px solid var(--color-border);
		display: flex;
		align-items: center;
		justify-content: space-between;
		font-size: 0.9rem;
	}

	.toast-success {
		border-left: 4px solid var(--color-success);
	}

	.toast-error {
		border-left: 4px solid var(--color-error);
	}

	.toast-info {
		border-left: 4px solid var(--color-primary);
	}

	.close-btn {
		background: none;
		border: none;
		color: var(--color-text-muted);
		font-size: 1.25rem;
		line-height: 1;
		cursor: pointer;
		padding: 0 0.25rem;
	}
	.close-btn:hover {
		color: var(--color-text-main);
	}
</style>
