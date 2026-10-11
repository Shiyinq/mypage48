<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		/** The hidden text of an inline `||spoiler||` run. */
		text: string;
	}

	let { text }: Props = $props();

	const { t } = useTranslation();

	// Inline spoilers reveal on tap and stay open for the life of the component.
	let revealed = $state(false);

	function reveal(event: MouseEvent) {
		// The card behind the text is a link; the click must only reveal.
		event.stopPropagation();
		revealed = true;
	}
</script>

{#if revealed}
	<span>{text}</span>
{:else}
	<button
		type="button"
		class="spoiler-hidden pointer-events-auto cursor-pointer appearance-none border-0 bg-transparent p-0 text-inherit [font:inherit]"
		onclick={reveal}
		aria-label={t('page48.spoiler.show')}
	>
		{text}
	</button>
{/if}

<style>
	/* A real blur of the glyphs (Threads-style), not a box or a shadow: the text
	   is unreadable until tapped. Blur lightens on hover as a hint. */
	.spoiler-hidden {
		filter: blur(6px);
		opacity: 0.8;
		user-select: none;
		transition:
			filter 150ms ease,
			opacity 150ms ease;
	}
	.spoiler-hidden:hover,
	.spoiler-hidden:focus-visible {
		filter: blur(4px);
		opacity: 0.95;
	}
</style>
