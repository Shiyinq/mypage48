<script lang="ts">
	import { EyeOff } from 'lucide-svelte';
	import { spoilerStore } from '$lib/stores/spoiler.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		postId: string;
		class?: string;
	}

	let { postId, class: klass = '' }: Props = $props();

	const { t } = useTranslation();

	function reveal(event: MouseEvent) {
		// The card behind the cover is a link; the click must only reveal.
		event.stopPropagation();
		spoilerStore.reveal(postId);
	}
</script>

<button
	type="button"
	class={`pointer-events-auto relative z-[1] mt-2 flex w-full cursor-pointer flex-col items-center gap-1.5 rounded-2xl border border-amber-300/70 bg-amber-50 px-4 py-6 text-center transition-colors hover:bg-amber-100 dark:border-amber-900/40 dark:bg-amber-950/20 dark:hover:bg-amber-950/40 ${klass}`}
	onclick={reveal}
	aria-label={t('page48.spoiler.show')}
>
	<EyeOff size={20} class="text-amber-600 dark:text-amber-400" />
	<span class="text-[14px] font-semibold text-amber-700 dark:text-amber-400">
		{t('page48.spoiler.show')}
	</span>
	<span class="text-[12px] text-amber-700/80 dark:text-amber-400/80">
		{t('page48.spoiler.tapToShow')}
	</span>
</button>
