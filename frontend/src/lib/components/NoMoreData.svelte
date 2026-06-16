<script lang="ts">
	import { useTranslation } from '$lib/i18n/useTranslation';
	import { fade } from 'svelte/transition';

	interface Props {
		message?: string;
		theme?: 'red' | 'blue' | 'pink' | 'gray';
		padding?: string;
	}

	let { message, theme = 'gray', padding = 'py-16' }: Props = $props();
	const { t } = useTranslation();

	const themeColors = {
		red: 'from-red-200 dark:from-red-900',
		blue: 'from-blue-200 dark:from-blue-900',
		pink: 'from-pink-200 dark:from-pink-900',
		gray: 'from-slate-200 dark:from-zinc-800'
	};
</script>

<div
	class="w-full {padding} flex flex-col items-center justify-center text-center px-4"
	in:fade={{ duration: 1000 }}
>
	<p
		class="text-[10px] uppercase font-black tracking-[0.2em] text-slate-400 opacity-80 dark:text-slate-500"
	>
		{message || t('common.noMoreData')}
	</p>
	<div class="h-10 w-px bg-gradient-to-b {themeColors[theme]} to-transparent mt-4"></div>
</div>
