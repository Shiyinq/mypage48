<script lang="ts">
	import { ExternalLink, Music } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		/** The share link, validated by `extractSpotifyLink`. */
		url: string;
		class?: string;
	}

	let { url, class: klass = '' }: Props = $props();

	const { t } = useTranslation();
</script>

<!-- Spotify share links (spotify.link/...) carry no id and cannot be resolved
     from the browser, so this is a plain link card that opens them on Spotify. -->
<a
	href={url}
	target="_blank"
	rel="noopener noreferrer nofollow"
	class={`group/sp-link flex items-center gap-3 rounded-2xl border border-gray-200 bg-white px-4 py-3 transition-colors hover:bg-gray-50 dark:border-zinc-700 dark:bg-zinc-900 dark:hover:bg-zinc-800/60 ${klass}`}
>
	<span
		class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#1DB954] text-black"
	>
		<Music size={20} />
	</span>
	<span class="min-w-0 flex-1 text-left">
		<span class="block text-[14px] font-semibold text-gray-900 dark:text-gray-100">
			{t('page48.embed.listenOnSpotify')}
		</span>
		<span class="block text-[12px] text-gray-500 dark:text-gray-400">
			{t('page48.embed.spotifyShortNotice')}
		</span>
	</span>
	<ExternalLink
		size={16}
		class="shrink-0 text-gray-400 transition-colors group-hover/sp-link:text-gray-600 dark:group-hover/sp-link:text-gray-200"
	/>
</a>
