<script lang="ts">
	interface Props {
		children?: import('svelte').Snippet;
	}

	let { children }: Props = $props();
</script>

<div class="card glass-panel">
	{@render children?.()}
</div>

<style>
	.card {
		padding: 2rem;
		width: 100%;
		margin: 0 auto;
	}

	@media (min-width: 640px) {
		.card {
			padding: 3rem;
		}
	}
</style>
