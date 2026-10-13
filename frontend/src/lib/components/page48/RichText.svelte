<script lang="ts">
	import SpoilerText from '$lib/components/page48/SpoilerText.svelte';
	import UserHoverCard from '$lib/components/page48/UserHoverCard.svelte';
	import { parseContent, tagUrl, userUrl, type Page48Media } from '$lib/utils/page48';

	interface Props {
		/** Raw text; `#hashtags`, `@mentions`, links and `||spoilers||` are parsed out. */
		text: string;
		/** Keep the active media filter (Gambar/Video) on hashtag links. */
		media?: Page48Media | null;
		/** Show the mini profile when an `@mention` is hovered, instead of a plain link. */
		mentionHover?: boolean;
		/** Reveal inline `||spoiler||` runs; otherwise their text is shown as plain text. */
		spoilers?: boolean;
	}

	let { text, media = null, mentionHover = false, spoilers = false }: Props = $props();

	let parts = $derived(parseContent(text));
</script>

{#each parts as part, i (i)}
	{#if part.tag}
		<a
			href={tagUrl(part.tag, media)}
			class="pointer-events-auto cursor-pointer text-red-500 hover:underline">{part.text}</a
		>
	{:else if part.mention}
		{#if mentionHover}
			<UserHoverCard
				username={part.mention}
				href={userUrl(part.mention)}
				class="pointer-events-auto cursor-pointer font-semibold text-red-500 hover:underline"
				>{part.text}</UserHoverCard
			>
		{:else}
			<a
				href={userUrl(part.mention)}
				class="pointer-events-auto cursor-pointer font-semibold text-red-500 hover:underline"
				>{part.text}</a
			>
		{/if}
	{:else if part.link}
		<a
			href={part.link}
			target="_blank"
			rel="noopener noreferrer nofollow"
			class="pointer-events-auto cursor-pointer break-all text-blue-500 hover:underline"
			>{part.text}</a
		>
	{:else if part.spoiler && spoilers}
		<SpoilerText text={part.text} />
	{:else}
		{part.text}
	{/if}
{/each}
