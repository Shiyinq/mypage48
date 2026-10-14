<script lang="ts">
	import SpoilerText from '$lib/components/page48/SpoilerText.svelte';
	import UserHoverCard from '$lib/components/page48/UserHoverCard.svelte';
	import {
		parseContent,
		tagUrl,
		userUrl,
		type ContentPart,
		type Page48Media
	} from '$lib/utils/page48';

	interface Props {
		/** Raw text; `#hashtags`, `@mentions`, links, `||spoilers||`, inline markers and `> ` quotes are parsed out. */
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

	// Consecutive quote parts share one bar, so a quoted line with inline markup shows a
	// single left border instead of one per styled run.
	let segments = $derived.by(() => {
		const groups: { quote: boolean; parts: ContentPart[] }[] = [];
		for (const part of parts) {
			const quote = !!part.quote;
			const last = groups[groups.length - 1];
			if (last && last.quote === quote) last.parts.push(part);
			else groups.push({ quote, parts: [part] });
		}
		return groups;
	});

	// Inline markers (`**bold**`, `*italic*`, `` `code` ``, …) are reported as flags, never
	// as HTML — the text is rendered by Svelte, which escapes it, so this stays XSS-safe.
	function markerClass(part: ContentPart): string {
		const classes: string[] = [];
		if (part.bold) classes.push('font-bold');
		if (part.italic) classes.push('italic');
		if (part.underline) classes.push('underline');
		if (part.strike) classes.push('line-through');
		if (part.code)
			classes.push('rounded bg-gray-100 px-1 py-0.5 font-mono text-[0.9em] dark:bg-zinc-800');
		return classes.join(' ');
	}
</script>

{#snippet inlinePart(part: ContentPart)}
	{@const styles = markerClass(part)}
	{#if part.tag}
		<a
			href={tagUrl(part.tag, media)}
			class="pointer-events-auto cursor-pointer text-red-500 hover:underline {styles}"
			>{part.text}</a
		>
	{:else if part.mention}
		{#if mentionHover}
			<UserHoverCard
				username={part.mention}
				href={userUrl(part.mention)}
				class="pointer-events-auto cursor-pointer font-semibold text-red-500 hover:underline {styles}"
				>{part.text}</UserHoverCard
			>
		{:else}
			<a
				href={userUrl(part.mention)}
				class="pointer-events-auto cursor-pointer font-semibold text-red-500 hover:underline {styles}"
				>{part.text}</a
			>
		{/if}
	{:else if part.link}
		<a
			href={part.link}
			target="_blank"
			rel="noopener noreferrer nofollow"
			class="pointer-events-auto cursor-pointer break-all text-blue-500 hover:underline {styles}"
			>{part.text}</a
		>
	{:else if part.spoiler && spoilers}
		<SpoilerText text={part.text} />
	{:else if styles}
		<span class={styles}>{part.text}</span>
	{:else}
		{part.text}
	{/if}
{/snippet}

{#each segments as segment, i (i)}
	{#if segment.quote}
		<span class="inline-block border-l-2 border-gray-300 pl-3 dark:border-zinc-600">
			{#each segment.parts as part, j (j)}{@render inlinePart(part)}{/each}
		</span>
	{:else}
		{#each segment.parts as part, j (j)}{@render inlinePart(part)}{/each}
	{/if}
{/each}
