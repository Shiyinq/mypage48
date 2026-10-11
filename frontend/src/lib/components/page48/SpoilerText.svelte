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
		class="pointer-events-auto rounded bg-gray-800 px-1 text-transparent transition-colors hover:bg-gray-700 dark:bg-zinc-600 dark:hover:bg-zinc-500"
		onclick={reveal}
		aria-label={t('page48.spoiler.show')}
	>
		{text}
	</button>
{/if}
