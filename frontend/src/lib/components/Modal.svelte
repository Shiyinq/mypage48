<script lang="ts">
	import { createEventDispatcher, onDestroy, onMount } from 'svelte';
	import Button from './Button.svelte';

	export let title = 'Confirm Action';
	export let message = 'Are you sure you want to proceed?';
	export let confirmText = 'Confirm';
	export let cancelText = 'Cancel';
	export let confirmVariant: 'primary' | 'secondary' | 'outline' | 'ghost' | 'google' | 'github' =
		'primary';

	const dispatch = createEventDispatcher();

	function onConfirm() {
		dispatch('confirm');
	}

	function onCancel() {
		dispatch('cancel');
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape') {
			onCancel();
		}
	}
</script>

<svelte:window on:keydown={handleKeydown} />

<div class="modal-backdrop" on:click|self={onCancel} role="presentation">
	<div class="modal-content glass-panel">
		<h3 class="modal-title">{title}</h3>
		<p class="modal-message">{message}</p>

		<div class="modal-actions">
			<Button variant="ghost" on:click={onCancel}>{cancelText}</Button>
			<Button variant={confirmVariant} on:click={onConfirm}>{confirmText}</Button>
		</div>
	</div>
</div>

<style>
	.modal-backdrop {
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: rgba(0, 0, 0, 0.6);
		backdrop-filter: blur(4px);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 50;
		animation: fadeIn 0.2s ease-out;
	}

	.modal-content {
		width: 90%;
		max-width: 400px;
		padding: 1.5rem;
		background: #1e293b; /* Fallback */
		background: var(--color-surface);
		border: 1px solid var(--color-border);
		box-shadow: var(--shadow-lg);
		border-radius: var(--radius-lg);
		animation: slideUp 0.2s ease-out;
	}

	.modal-title {
		font-size: 1.25rem;
		font-weight: 600;
		margin-bottom: 0.75rem;
		color: var(--color-text-main);
	}

	.modal-message {
		color: var(--color-text-muted);
		margin-bottom: 1.5rem;
		line-height: 1.5;
	}

	.modal-actions {
		display: flex;
		justify-content: flex-end;
		gap: 0.75rem;
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}

	@keyframes slideUp {
		from {
			transform: translateY(20px);
			opacity: 0;
		}
		to {
			transform: translateY(0);
			opacity: 1;
		}
	}
</style>
