<script lang="ts">
	import { EyeOff } from 'lucide-svelte';
	import { spoilerStore } from '$lib/stores/spoiler.svelte';
	import { useTranslation } from '$lib/i18n/useTranslation';

	interface Props {
		postId: string;
	}

	let { postId }: Props = $props();

	const { t } = useTranslation();

	function reveal(event: MouseEvent) {
		// The card behind the cover is a link; the click must only reveal.
		event.stopPropagation();
		spoilerStore.reveal(postId);
	}
</script>

<!-- No veil: just the reveal pill over the blurred content, matching the inline
     spoiler (a real blur, not a box). -->
<button
	type="button"
	class="pointer-events-auto absolute inset-0 z-[3] flex cursor-pointer items-center justify-center rounded-2xl transition-colors hover:bg-black/[0.03] dark:hover:bg-white/[0.03]"
	onclick={reveal}
	aria-label={t('page48.spoiler.show')}
>
	<span
		class="pointer-events-none inline-flex items-center gap-1.5 rounded-full border border-white/15 bg-zinc-900/85 px-3.5 py-1.5 text-[12.5px] font-semibold text-white shadow-lg backdrop-blur-md"
	>
		<EyeOff size={14} />
		{t('page48.spoiler.show')}
	</span>
</button>
