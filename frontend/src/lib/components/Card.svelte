<div class="card glass-panel">
	<slot />
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
