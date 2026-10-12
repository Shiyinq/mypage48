<script lang="ts">
	import { ExternalLink } from 'lucide-svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		/** Normalised story URL, built by `extractInstagramStory`. */
		url: string;
		class?: string;
	}

	let { url, class: klass = '' }: Props = $props();

	const { t } = useTranslation();
</script>

<!-- Stories are ephemeral and have no official embed endpoint, so this is a plain
     link card that opens the story on Instagram in a new tab. -->
<a
	href={url}
	target="_blank"
	rel="noopener noreferrer nofollow"
	class={`group/story flex items-center gap-3 rounded-2xl border border-gray-200 bg-white px-4 py-3 transition-colors hover:bg-gray-50 dark:border-zinc-700 dark:bg-zinc-900 dark:hover:bg-zinc-800/60 ${klass}`}
>
	<span
		class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-yellow-400 via-pink-500 to-purple-600 text-white"
	>
		<svg
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			stroke-width="2"
			stroke-linecap="round"
			stroke-linejoin="round"
			class="h-[20px] w-[20px]"
			aria-hidden="true"
		>
			<rect x="2" y="2" width="20" height="20" rx="5" ry="5" />
			<path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
			<line x1="17.5" y1="6.5" x2="17.51" y2="6.5" />
		</svg>
	</span>
	<span class="min-w-0 flex-1 text-left">
		<span class="block text-[14px] font-semibold text-gray-900 dark:text-gray-100">
			{t('page48.embed.viewStoryOnInstagram')}
		</span>
		<span class="block text-[12px] text-gray-500 dark:text-gray-400">
			{t('page48.embed.storyNotice')}
		</span>
	</span>
	<ExternalLink
		size={16}
		class="shrink-0 text-gray-400 transition-colors group-hover/story:text-gray-600 dark:group-hover/story:text-gray-200"
	/>
</a>
