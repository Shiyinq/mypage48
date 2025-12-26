<script lang="ts">
	export let label = '';
	export let type = 'text';
	export let value = '';
	export let placeholder = '';
	export let error = '';
	export let id = Math.random().toString(36).substr(2, 9);
</script>

<div class="input-group">
	{#if label}
		<label for={id} class="input-label">{label}</label>
	{/if}

	<input
		{id}
		{type}
		{placeholder}
		{value}
		class="input-field {error ? 'has-error' : ''}"
		on:input={(e) => (value = e.currentTarget.value)}
		on:blur
		{...$$restProps}
	/>

	{#if error}
		<div class="error-msg">{error}</div>
	{/if}
</div>

<style>
	.input-group {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		width: 100%;
		margin-bottom: 1rem;
	}

	.input-label {
		font-size: 0.875rem;
		font-weight: 500;
		color: var(--color-text-muted);
		transition: color 0.2s;
	}

	.input-field {
		background: var(--color-bg);
		border: 1px solid var(--color-border);
		border-radius: var(--radius-md);
		padding: 0.75rem 1rem;
		color: var(--color-text-main);
		transition: all var(--transition-fast);
		outline: none;
		font-size: 1rem;
	}

	.input-field:focus {
		border-color: var(--color-primary);
		box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
	}

	.input-field::placeholder {
		color: #475569;
	}

	.has-error {
		border-color: var(--color-error);
	}
	.has-error:focus {
		box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.15);
	}

	.error-msg {
		font-size: 0.75rem;
		color: var(--color-error);
		margin-top: 0.25rem;
		animation: slideDown 0.2s ease-out;
	}

	@keyframes slideDown {
		from {
			opacity: 0;
			transform: translateY(-5px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
</style>
